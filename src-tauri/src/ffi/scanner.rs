//! Scanner FFI bindings
//!
//! Safe Rust wrappers for zig-core scanner functions.

use std::ffi::{CStr, CString};
use std::os::raw::c_char;

/// File fingerprint - mirrors Zig's FileFingerprint
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct FileFingerprint {
    pub mtime_ns: i64,
    pub size: i64,
    pub inode: u64,
    pub has_mtime: bool,
    pub has_inode: bool,
}

impl FileFingerprint {
    pub fn matches(&self, other: &FileFingerprint) -> bool {
        if self.has_mtime != other.has_mtime {
            return false;
        }
        if self.has_mtime && self.mtime_ns != other.mtime_ns {
            return false;
        }
        self.size == other.size
    }
}

/// Extracted metadata - mirrors Zig's ExtractedMetadata
#[repr(C)]
pub struct ExtractedMetadataRaw {
    // File info
    pub filepath: [u8; 4096],
    pub filepath_len: u32,
    pub file_size: i64,
    pub file_mtime_ns: i64,
    pub file_inode: u64,
    pub has_mtime: bool,
    pub has_inode: bool,

    // Basic tags
    pub title: [u8; 512],
    pub title_len: u32,
    pub artist: [u8; 512],
    pub artist_len: u32,
    pub album: [u8; 512],
    pub album_len: u32,
    pub album_artist: [u8; 512],
    pub album_artist_len: u32,

    // Track info
    pub track_number: [u8; 32],
    pub track_number_len: u32,
    pub track_total: [u8; 32],
    pub track_total_len: u32,
    pub disc_number: u32,
    pub disc_total: u32,
    pub has_disc_number: bool,
    pub has_disc_total: bool,

    // Date/genre
    pub date: [u8; 64],
    pub date_len: u32,
    pub genre: [u8; 256],
    pub genre_len: u32,

    // Audio properties
    pub duration_secs: f64,
    pub bitrate: u32,
    pub sample_rate: u32,
    pub channels: u8,
    pub has_duration: bool,
    pub has_bitrate: bool,
    pub has_sample_rate: bool,
    pub has_channels: bool,

    // Status
    pub is_valid: bool,
    pub error_code: u32,
}

impl ExtractedMetadataRaw {
    fn get_string(buf: &[u8], len: u32) -> Option<String> {
        if len == 0 {
            return None;
        }
        let slice = &buf[..len as usize];
        String::from_utf8(slice.to_vec()).ok()
    }

    pub fn filepath(&self) -> String {
        Self::get_string(&self.filepath, self.filepath_len).unwrap_or_default()
    }

    pub fn title(&self) -> Option<String> {
        Self::get_string(&self.title, self.title_len)
    }

    pub fn artist(&self) -> Option<String> {
        Self::get_string(&self.artist, self.artist_len)
    }

    pub fn album(&self) -> Option<String> {
        Self::get_string(&self.album, self.album_len)
    }

    pub fn album_artist(&self) -> Option<String> {
        Self::get_string(&self.album_artist, self.album_artist_len)
    }

    pub fn track_number(&self) -> Option<String> {
        Self::get_string(&self.track_number, self.track_number_len)
    }

    pub fn track_total(&self) -> Option<String> {
        Self::get_string(&self.track_total, self.track_total_len)
    }

    pub fn date(&self) -> Option<String> {
        Self::get_string(&self.date, self.date_len)
    }

    pub fn genre(&self) -> Option<String> {
        Self::get_string(&self.genre, self.genre_len)
    }

    pub fn duration(&self) -> Option<f64> {
        if self.has_duration {
            Some(self.duration_secs)
        } else {
            None
        }
    }

    pub fn disc_number(&self) -> Option<u32> {
        if self.has_disc_number {
            Some(self.disc_number)
        } else {
            None
        }
    }

    pub fn disc_total(&self) -> Option<u32> {
        if self.has_disc_total {
            Some(self.disc_total)
        } else {
            None
        }
    }
}

// FFI declarations
#[link(name = "mtcore")]
extern "C" {
    fn mt_extract_metadata(path: *const c_char) -> *mut ExtractedMetadataRaw;
    fn mt_free_metadata(ptr: *mut ExtractedMetadataRaw);
    fn mt_extract_metadata_into(path: *const c_char, out: *mut ExtractedMetadataRaw) -> bool;
    fn mt_is_audio_file(path: *const c_char) -> bool;
    fn mt_get_fingerprint(path: *const c_char, out: *mut FileFingerprint) -> bool;
    fn mt_fingerprint_matches(fp1: *const FileFingerprint, fp2: *const FileFingerprint) -> bool;
    fn mt_version() -> *const c_char;
}

/// Safe wrapper for extracting metadata
pub fn extract_metadata(filepath: &str) -> Result<ExtractedMetadataRaw, String> {
    let c_path = CString::new(filepath).map_err(|e| e.to_string())?;

    unsafe {
        let mut result = std::mem::zeroed::<ExtractedMetadataRaw>();
        let success = mt_extract_metadata_into(c_path.as_ptr(), &mut result);

        if success {
            Ok(result)
        } else {
            Err(format!(
                "Failed to extract metadata from {}: error code {}",
                filepath, result.error_code
            ))
        }
    }
}

/// Safe wrapper for extracting metadata (returns default on error)
pub fn extract_metadata_or_default(filepath: &str) -> ExtractedMetadataRaw {
    extract_metadata(filepath).unwrap_or_else(|_| unsafe { std::mem::zeroed() })
}

/// Check if file is a supported audio format
pub fn is_audio_file(filepath: &str) -> bool {
    let Ok(c_path) = CString::new(filepath) else {
        return false;
    };
    unsafe { mt_is_audio_file(c_path.as_ptr()) }
}

/// Get file fingerprint
pub fn get_fingerprint(filepath: &str) -> Option<FileFingerprint> {
    let c_path = CString::new(filepath).ok()?;

    unsafe {
        let mut fp = std::mem::zeroed::<FileFingerprint>();
        if mt_get_fingerprint(c_path.as_ptr(), &mut fp) {
            Some(fp)
        } else {
            None
        }
    }
}

/// Get zig-core library version
pub fn version() -> String {
    unsafe {
        let ptr = mt_version();
        CStr::from_ptr(ptr).to_string_lossy().into_owned()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_audio_file() {
        assert!(is_audio_file("song.mp3"));
        assert!(is_audio_file("track.FLAC"));
        assert!(!is_audio_file("image.jpg"));
    }

    #[test]
    fn test_version() {
        let v = version();
        assert!(!v.is_empty());
    }
}
