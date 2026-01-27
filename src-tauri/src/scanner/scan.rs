//! 2-phase scan orchestration.
//!
//! Coordinates the inventory and metadata extraction phases
//! for optimal scanning performance.

use std::collections::HashMap;

use crate::scanner::fingerprint::FileFingerprint;
use crate::scanner::inventory::{run_inventory, InventoryResult};
use crate::scanner::metadata::extract_metadata_batch;
use crate::scanner::{ExtractedMetadata, ScanProgress, ScanResult, ScanStats};

/// Result of a complete 2-phase scan
#[derive(Debug)]
pub struct ScanResult2Phase {
    /// Metadata for newly added files
    pub added: Vec<ExtractedMetadata>,
    /// Metadata for modified files
    pub modified: Vec<ExtractedMetadata>,
    /// Paths of unchanged files
    pub unchanged: Vec<String>,
    /// Paths of deleted files (were in DB, not on filesystem)
    pub deleted: Vec<String>,
    /// Scan statistics
    pub stats: ScanStats,
}

/// Progress callback type for scan operations
pub type ProgressCallback = Box<dyn Fn(ScanProgress) + Send + Sync>;

/// Run a complete 2-phase scan
///
/// # Arguments
/// * `paths` - Paths to scan (files or directories)
/// * `db_fingerprints` - Current fingerprints from database (filepath -> fingerprint)
/// * `recursive` - Whether to scan directories recursively
/// * `progress_callback` - Optional callback for progress updates
///
/// # Returns
/// Scan result with categorized files and extracted metadata
pub fn scan_2phase(
    paths: &[String],
    db_fingerprints: &HashMap<String, FileFingerprint>,
    recursive: bool,
    progress_callback: Option<&ProgressCallback>,
) -> ScanResult<ScanResult2Phase> {
    // Phase 1: Inventory
    if let Some(cb) = progress_callback {
        cb(ScanProgress {
            phase: "inventory".to_string(),
            current: 0,
            total: 0,
            message: Some("Starting inventory phase...".to_string()),
        });
    }

    let inventory_progress = progress_callback.map(|cb| {
        move |visited: usize| {
            cb(ScanProgress {
                phase: "inventory".to_string(),
                current: visited,
                total: 0, // Unknown total during inventory
                message: None,
            });
        }
    });

    let inventory = run_inventory(paths, db_fingerprints, recursive, inventory_progress)?;

    // Phase 2: Parse changed files
    let total_to_parse = inventory.added.len() + inventory.modified.len();

    if let Some(cb) = progress_callback {
        cb(ScanProgress {
            phase: "parse".to_string(),
            current: 0,
            total: total_to_parse,
            message: Some(format!(
                "Parsing {} new/modified files...",
                total_to_parse
            )),
        });
    }

    // Combine added and modified for parsing
    let all_to_parse: Vec<(String, FileFingerprint)> = inventory
        .added
        .iter()
        .chain(inventory.modified.iter())
        .cloned()
        .collect();

    let parse_progress = progress_callback.map(|cb| {
        move |current: usize, total: usize| {
            cb(ScanProgress {
                phase: "parse".to_string(),
                current,
                total,
                message: None,
            });
        }
    });

    let parsed_metadata = extract_metadata_batch(&all_to_parse, parse_progress);

    // Split results back into added and modified
    let added_count = inventory.added.len();
    let (added_metadata, modified_metadata) = parsed_metadata.split_at(added_count);

    // Final stats
    let mut stats = inventory.stats;
    stats.errors += parsed_metadata
        .iter()
        .filter(|m| m.title.is_none() || m.duration.is_none())
        .count();

    if let Some(cb) = progress_callback {
        cb(ScanProgress {
            phase: "complete".to_string(),
            current: total_to_parse,
            total: total_to_parse,
            message: Some(format!(
                "Scan complete: {} added, {} modified, {} unchanged, {} deleted",
                stats.added, stats.modified, stats.unchanged, stats.deleted
            )),
        });
    }

    Ok(ScanResult2Phase {
        added: added_metadata.to_vec(),
        modified: modified_metadata.to_vec(),
        unchanged: inventory.unchanged,
        deleted: inventory.deleted,
        stats,
    })
}

/// Quick scan that only runs inventory (no metadata extraction)
///
/// Useful for fast change detection when you only need to know
/// what changed, not the full metadata.
pub fn scan_inventory_only(
    paths: &[String],
    db_fingerprints: &HashMap<String, FileFingerprint>,
    recursive: bool,
) -> ScanResult<InventoryResult> {
    run_inventory(paths, db_fingerprints, recursive, None::<fn(usize)>)
}

/// Build a fingerprint map from database tracks
pub fn build_fingerprint_map(
    tracks: &[(String, Option<i64>, i64)],
) -> HashMap<String, FileFingerprint> {
    tracks
        .iter()
        .map(|(filepath, mtime_ns, size)| {
            (
                filepath.clone(),
                FileFingerprint::from_db(*mtime_ns, *size),
            )
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use std::io::Write;
    use tempfile::tempdir;

    #[test]
    fn test_scan_2phase_empty() {
        let db_fingerprints: HashMap<String, FileFingerprint> = HashMap::new();
        let dir = tempdir().unwrap();

        let result = scan_2phase(
            &[dir.path().to_string_lossy().to_string()],
            &db_fingerprints,
            true,
            None,
        )
        .unwrap();

        assert!(result.added.is_empty());
        assert!(result.modified.is_empty());
        assert!(result.unchanged.is_empty());
        assert!(result.deleted.is_empty());
    }

    #[test]
    fn test_scan_inventory_only() {
        let dir = tempdir().unwrap();

        // Create test file
        let file_path = dir.path().join("song.mp3");
        let mut file = File::create(&file_path).unwrap();
        file.write_all(b"fake mp3").unwrap();

        let db_fingerprints: HashMap<String, FileFingerprint> = HashMap::new();

        let result = scan_inventory_only(
            &[dir.path().to_string_lossy().to_string()],
            &db_fingerprints,
            true,
        )
        .unwrap();

        assert_eq!(result.stats.added, 1);
        assert_eq!(result.added.len(), 1);
    }

    #[test]
    fn test_build_fingerprint_map() {
        let tracks = vec![
            ("/music/song1.mp3".to_string(), Some(1234567890_i64), 1000_i64),
            ("/music/song2.mp3".to_string(), None, 2000_i64),
        ];

        let map = build_fingerprint_map(&tracks);

        assert_eq!(map.len(), 2);
        assert_eq!(map["/music/song1.mp3"].mtime_ns, Some(1234567890));
        assert_eq!(map["/music/song1.mp3"].size, 1000);
        assert_eq!(map["/music/song2.mp3"].mtime_ns, None);
        assert_eq!(map["/music/song2.mp3"].size, 2000);
    }
}
