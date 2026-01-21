//! Tauri commands for scanner operations.
//!
//! These commands expose the scanner functionality to the frontend
//! with progress events emitted during scanning.

use std::collections::HashMap;
use tauri::{AppHandle, Emitter, State};

use crate::db::{library, Database};
use crate::scanner::artwork::{get_artwork, Artwork};
use crate::scanner::fingerprint::FileFingerprint;
use crate::scanner::metadata::extract_metadata;
use crate::scanner::scan::{scan_2phase, ProgressCallback, ScanResult2Phase};
use crate::scanner::{ExtractedMetadata, ScanProgress, ScanStats};

/// Scan event payload for progress updates
#[derive(Clone, serde::Serialize)]
struct ScanProgressEvent {
    phase: String,
    current: usize,
    total: usize,
    message: Option<String>,
}

/// Scan result sent to frontend
#[derive(Clone, serde::Serialize)]
pub struct ScanResultResponse {
    pub added_count: usize,
    pub modified_count: usize,
    pub unchanged_count: usize,
    pub deleted_count: usize,
    pub error_count: usize,
    pub stats: ScanStats,
}

impl From<&ScanResult2Phase> for ScanResultResponse {
    fn from(result: &ScanResult2Phase) -> Self {
        ScanResultResponse {
            added_count: result.added.len(),
            modified_count: result.modified.len(),
            unchanged_count: result.unchanged.len(),
            deleted_count: result.deleted.len(),
            error_count: result.stats.errors,
            stats: result.stats.clone(),
        }
    }
}

/// Get fingerprints from the database for comparison
fn get_db_fingerprints(db: &Database) -> Result<HashMap<String, FileFingerprint>, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    // Get all tracks with their fingerprints
    let mut stmt = conn
        .prepare("SELECT filepath, file_mtime_ns, file_size FROM library")
        .map_err(|e| e.to_string())?;

    let fingerprints: HashMap<String, FileFingerprint> = stmt
        .query_map([], |row| {
            let filepath: String = row.get(0)?;
            let mtime_ns: Option<i64> = row.get(1)?;
            let size: i64 = row.get(2)?;
            Ok((filepath, FileFingerprint::from_db(mtime_ns, size)))
        })
        .map_err(|e| e.to_string())?
        .filter_map(|r| r.ok())
        .collect();

    Ok(fingerprints)
}

/// Scan paths and add/update tracks in the database
#[tauri::command]
pub async fn scan_paths_to_library(
    app: AppHandle,
    db: State<'_, Database>,
    paths: Vec<String>,
    recursive: bool,
) -> Result<ScanResultResponse, String> {
    // Get current fingerprints from DB
    let db_fingerprints = get_db_fingerprints(&db)?;

    // Create progress callback that emits Tauri events
    let app_handle = app.clone();
    let progress_callback: ProgressCallback = Box::new(move |progress: ScanProgress| {
        let _ = app_handle.emit(
            "scan-progress",
            ScanProgressEvent {
                phase: progress.phase,
                current: progress.current,
                total: progress.total,
                message: progress.message,
            },
        );
    });

    // Run 2-phase scan
    let scan_result = scan_2phase(&paths, &db_fingerprints, recursive, Some(&progress_callback))
        .map_err(|e| e.to_string())?;

    // Get database connection for updates
    let conn = db.conn().map_err(|e| e.to_string())?;

    // Add new tracks to database
    if !scan_result.added.is_empty() {
        let tracks: Vec<(String, crate::db::TrackMetadata)> = scan_result
            .added
            .iter()
            .map(|m| (m.filepath.clone(), to_db_metadata(m)))
            .collect();

        library::add_tracks_bulk(&conn, &tracks).map_err(|e| e.to_string())?;
    }

    // Update modified tracks
    if !scan_result.modified.is_empty() {
        let updates: Vec<(String, crate::db::TrackMetadata)> = scan_result
            .modified
            .iter()
            .map(|m| (m.filepath.clone(), to_db_metadata(m)))
            .collect();

        library::update_tracks_bulk(&conn, &updates).map_err(|e| e.to_string())?;
    }

    // Mark deleted tracks as missing
    for filepath in &scan_result.deleted {
        let _ = library::mark_track_missing_by_filepath(&conn, filepath);
    }

    // Emit completion event
    let _ = app.emit(
        "scan-complete",
        ScanResultResponse::from(&scan_result),
    );

    Ok(ScanResultResponse::from(&scan_result))
}

/// Scan a single path (file or directory) without database integration
#[tauri::command]
pub async fn scan_paths_metadata(
    app: AppHandle,
    paths: Vec<String>,
    recursive: bool,
) -> Result<Vec<ExtractedMetadata>, String> {
    let db_fingerprints: HashMap<String, FileFingerprint> = HashMap::new();

    // Create progress callback
    let app_handle = app.clone();
    let progress_callback: ProgressCallback = Box::new(move |progress: ScanProgress| {
        let _ = app_handle.emit(
            "scan-progress",
            ScanProgressEvent {
                phase: progress.phase,
                current: progress.current,
                total: progress.total,
                message: progress.message,
            },
        );
    });

    let scan_result = scan_2phase(&paths, &db_fingerprints, recursive, Some(&progress_callback))
        .map_err(|e| e.to_string())?;

    // Return all metadata (added is everything since we have no DB fingerprints)
    Ok(scan_result.added)
}

/// Extract metadata from a single file
#[tauri::command]
pub fn extract_file_metadata(filepath: String) -> Result<ExtractedMetadata, String> {
    extract_metadata(&filepath).map_err(|e| e.to_string())
}

/// Get artwork for a track
#[tauri::command]
pub fn get_track_artwork(filepath: String) -> Option<Artwork> {
    get_artwork(&filepath)
}

/// Get artwork as a data URL for use in img src
#[tauri::command]
pub fn get_track_artwork_url(filepath: String) -> Option<String> {
    crate::scanner::artwork::get_artwork_data_url(&filepath)
}

/// Convert ExtractedMetadata to database TrackMetadata
fn to_db_metadata(m: &ExtractedMetadata) -> crate::db::TrackMetadata {
    crate::db::TrackMetadata {
        title: m.title.clone(),
        artist: m.artist.clone(),
        album: m.album.clone(),
        album_artist: m.album_artist.clone(),
        track_number: m.track_number.clone(),
        track_total: m.track_total.clone(),
        date: m.date.clone(),
        duration: m.duration,
        file_size: Some(m.file_size),
        file_mtime_ns: m.file_mtime_ns,
    }
}
