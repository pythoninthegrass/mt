// Integration test to verify FFI calls to Zig library work
use std::ffi::CString;

#[test]
fn test_zig_version() {
    unsafe {
        let version = mt_lib::ffi::mt_version();
        let version_str = std::ffi::CStr::from_ptr(version)
            .to_str()
            .expect("Invalid UTF-8 in version string");

        println!("Zig library version: {}", version_str);
        assert!(
            !version_str.is_empty(),
            "Version string should not be empty"
        );
        assert!(
            version_str.contains('.'),
            "Version should contain dots (e.g., 0.1.0)"
        );
    }
}

#[test]
fn test_zig_is_audio_file() {
    unsafe {
        // Test valid audio extensions
        let mp3 = CString::new("song.mp3").unwrap();
        assert!(
            mt_lib::ffi::mt_is_audio_file(mp3.as_ptr()),
            "mp3 should be recognized"
        );

        let flac = CString::new("song.flac").unwrap();
        assert!(
            mt_lib::ffi::mt_is_audio_file(flac.as_ptr()),
            "flac should be recognized"
        );

        let m4a = CString::new("song.m4a").unwrap();
        assert!(
            mt_lib::ffi::mt_is_audio_file(m4a.as_ptr()),
            "m4a should be recognized"
        );

        // Test invalid extensions
        let txt = CString::new("file.txt").unwrap();
        assert!(
            !mt_lib::ffi::mt_is_audio_file(txt.as_ptr()),
            "txt should not be recognized"
        );

        let jpg = CString::new("image.jpg").unwrap();
        assert!(
            !mt_lib::ffi::mt_is_audio_file(jpg.as_ptr()),
            "jpg should not be recognized"
        );
    }
}

#[test]
fn test_zig_fingerprint_matches() {
    use mt_lib::ffi::FileFingerprint;

    unsafe {
        // Create two identical fingerprints
        let fp1 = FileFingerprint {
            mtime_ns: 1234567890000000000,
            size: 1024,
            inode: 0,
            has_mtime: true,
            has_inode: false,
        };

        let fp2 = FileFingerprint {
            mtime_ns: 1234567890000000000,
            size: 1024,
            inode: 0,
            has_mtime: true,
            has_inode: false,
        };

        assert!(
            mt_lib::ffi::mt_fingerprint_matches(&fp1, &fp2),
            "Identical fingerprints should match"
        );

        // Create different fingerprint
        let fp3 = FileFingerprint {
            mtime_ns: 1234567890000000000,
            size: 2048,
            inode: 0,
            has_mtime: true,
            has_inode: false,
        };

        assert!(
            !mt_lib::ffi::mt_fingerprint_matches(&fp1, &fp3),
            "Different fingerprints should not match"
        );
    }
}
