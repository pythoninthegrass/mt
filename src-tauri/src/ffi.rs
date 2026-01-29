//! FFI bindings for Zig mtcore library
//!
//! This module provides Rust bindings to call Zig functions exported from libmtcore.a.
//! All types use #[repr(C)] to match Zig's extern struct layout.

use std::os::raw::c_char;

// ============================================================================
// Type Definitions (matching zig-core/src/types.zig)
// ============================================================================

/// File fingerprint for change detection
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct FileFingerprint {
    /// Modification time in nanoseconds since Unix epoch (0 if unavailable)
    pub mtime_ns: i64,
    /// File size in bytes
    pub size: i64,
    /// Inode number (0 if unavailable, Unix only)
    pub inode: u64,
    /// Whether mtime_ns is valid
    pub has_mtime: bool,
    /// Whether inode is valid
    pub has_inode: bool,
}

impl FileFingerprint {
    /// Check if two fingerprints match (ignores inode)
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

/// Extracted metadata from an audio file
/// Uses fixed-size buffers for FFI safety - no allocations cross the boundary
#[repr(C)]
#[derive(Debug, Clone)]
pub struct ExtractedMetadata {
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

impl ExtractedMetadata {
    /// Get title as a string slice
    pub fn get_title(&self) -> &str {
        std::str::from_utf8(&self.title[..self.title_len as usize]).unwrap_or("")
    }

    /// Get artist as a string slice
    pub fn get_artist(&self) -> &str {
        std::str::from_utf8(&self.artist[..self.artist_len as usize]).unwrap_or("")
    }

    /// Get album as a string slice
    pub fn get_album(&self) -> &str {
        std::str::from_utf8(&self.album[..self.album_len as usize]).unwrap_or("")
    }

    /// Get filepath as a string slice
    pub fn get_filepath(&self) -> &str {
        std::str::from_utf8(&self.filepath[..self.filepath_len as usize]).unwrap_or("")
    }
}

/// Scan statistics
#[repr(C)]
#[derive(Debug, Clone, Copy, Default)]
pub struct ScanStats {
    pub visited: u64,
    pub added: u64,
    pub modified: u64,
    pub unchanged: u64,
    pub deleted: u64,
    pub errors: u64,
}

// ============================================================================
// FFI Function Declarations (from zig-core/src/ffi.zig)
// ============================================================================

unsafe extern "C" {
    /// Extract metadata from a single file.
    /// Returns a pointer to ExtractedMetadata that must be freed with mt_free_metadata.
    pub fn mt_extract_metadata(path: *const c_char) -> *mut ExtractedMetadata;

    /// Free metadata returned by mt_extract_metadata
    pub fn mt_free_metadata(ptr: *mut ExtractedMetadata);

    /// Extract metadata into a caller-provided buffer (no allocation).
    /// Returns true on success.
    pub fn mt_extract_metadata_into(path: *const c_char, out: *mut ExtractedMetadata) -> bool;

    /// Batch extract metadata from multiple files.
    /// Caller provides arrays for paths and results.
    /// Returns number of successfully extracted files.
    pub fn mt_extract_metadata_batch(
        paths: *const *const c_char,
        count: usize,
        results: *mut ExtractedMetadata,
    ) -> usize;

    /// Check if a file has a supported audio extension
    pub fn mt_is_audio_file(path: *const c_char) -> bool;

    /// Get file fingerprint from path.
    /// Returns true on success, populates out_fp.
    pub fn mt_get_fingerprint(path: *const c_char, out_fp: *mut FileFingerprint) -> bool;

    /// Compare two fingerprints for equality (ignores inode)
    pub fn mt_fingerprint_matches(fp1: *const FileFingerprint, fp2: *const FileFingerprint)
        -> bool;

    /// Get library version string
    pub fn mt_version() -> *const c_char;
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::{CStr, CString};

    #[test]
    fn test_version() {
        unsafe {
            let version_ptr = mt_version();
            let version = CStr::from_ptr(version_ptr).to_str().unwrap();
            assert_eq!(version, "0.1.0");
        }
    }

    #[test]
    fn test_is_audio_file() {
        unsafe {
            // Test supported extensions
            let mp3 = CString::new("song.mp3").unwrap();
            assert!(mt_is_audio_file(mp3.as_ptr()));

            let flac = CString::new("track.flac").unwrap();
            assert!(mt_is_audio_file(flac.as_ptr()));

            let m4a = CString::new("audio.m4a").unwrap();
            assert!(mt_is_audio_file(m4a.as_ptr()));

            // Test case insensitivity
            let mp3_upper = CString::new("SONG.MP3").unwrap();
            assert!(mt_is_audio_file(mp3_upper.as_ptr()));

            // Test unsupported extensions
            let jpg = CString::new("image.jpg").unwrap();
            assert!(!mt_is_audio_file(jpg.as_ptr()));

            let txt = CString::new("readme.txt").unwrap();
            assert!(!mt_is_audio_file(txt.as_ptr()));
        }
    }

    #[test]
    fn test_fingerprint_matches() {
        let fp1 = FileFingerprint {
            mtime_ns: 1234567890,
            size: 1000,
            inode: 12345,
            has_mtime: true,
            has_inode: true,
        };

        let fp2 = FileFingerprint {
            mtime_ns: 1234567890,
            size: 1000,
            inode: 99999, // Different inode - should still match
            has_mtime: true,
            has_inode: true,
        };

        let fp3 = FileFingerprint {
            mtime_ns: 1234567890,
            size: 2000, // Different size
            inode: 12345,
            has_mtime: true,
            has_inode: true,
        };

        assert!(fp1.matches(&fp2));
        assert!(!fp1.matches(&fp3));

        // Test FFI function
        unsafe {
            assert!(mt_fingerprint_matches(&fp1, &fp2));
            assert!(!mt_fingerprint_matches(&fp1, &fp3));
        }
    }

    #[test]
    fn test_extract_metadata_into_nonexistent() {
        unsafe {
            let path = CString::new("/nonexistent/path.mp3").unwrap();
            let mut metadata = std::mem::zeroed::<ExtractedMetadata>();

            let success = mt_extract_metadata_into(path.as_ptr(), &mut metadata);

            // Should fail for nonexistent file
            assert!(!success);
            assert!(!metadata.is_valid);
        }
    }
}
