//! File fingerprinting for change detection.
//!
//! Uses file modification time (mtime_ns) and file size as a fingerprint
//! to detect changes without reading file contents.

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::time::UNIX_EPOCH;

use crate::scanner::ScanResult;

/// File fingerprint using mtime and size for change detection
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct FileFingerprint {
    /// File modification time in nanoseconds since Unix epoch
    pub mtime_ns: Option<i64>,
    /// File size in bytes
    pub size: i64,
}

impl FileFingerprint {
    /// Create a new fingerprint from file metadata
    pub fn from_path(path: &Path) -> ScanResult<Self> {
        let metadata = fs::metadata(path)?;

        let mtime_ns = metadata
            .modified()
            .ok()
            .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
            .map(|d| d.as_nanos() as i64);

        let size = metadata.len() as i64;

        Ok(FileFingerprint { mtime_ns, size })
    }

    /// Create a fingerprint from database values
    pub fn from_db(mtime_ns: Option<i64>, size: i64) -> Self {
        FileFingerprint { mtime_ns, size }
    }

    /// Check if this fingerprint matches another
    pub fn matches(&self, other: &FileFingerprint) -> bool {
        self.mtime_ns == other.mtime_ns && self.size == other.size
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use std::io::Write;
    use tempfile::tempdir;

    #[test]
    fn test_fingerprint_from_path() {
        let dir = tempdir().unwrap();
        let file_path = dir.path().join("test.txt");

        // Create a test file
        let mut file = File::create(&file_path).unwrap();
        file.write_all(b"test content").unwrap();
        drop(file);

        let fingerprint = FileFingerprint::from_path(&file_path).unwrap();

        assert!(fingerprint.mtime_ns.is_some());
        assert_eq!(fingerprint.size, 12); // "test content" is 12 bytes
    }

    #[test]
    fn test_fingerprint_matches() {
        let fp1 = FileFingerprint {
            mtime_ns: Some(1234567890),
            size: 1000,
        };

        let fp2 = FileFingerprint {
            mtime_ns: Some(1234567890),
            size: 1000,
        };

        let fp3 = FileFingerprint {
            mtime_ns: Some(1234567890),
            size: 2000, // Different size
        };

        let fp4 = FileFingerprint {
            mtime_ns: Some(9999999999),
            size: 1000, // Different mtime
        };

        assert!(fp1.matches(&fp2));
        assert!(!fp1.matches(&fp3));
        assert!(!fp1.matches(&fp4));
    }

    #[test]
    fn test_fingerprint_from_db() {
        let fp = FileFingerprint::from_db(Some(1234567890), 5000);

        assert_eq!(fp.mtime_ns, Some(1234567890));
        assert_eq!(fp.size, 5000);
    }
}
