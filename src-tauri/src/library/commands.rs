//! Tauri commands for library management.
//!
//! These commands expose library operations to the frontend,
//! replacing the Python FastAPI library routes.

use std::path::Path;
use tauri::{AppHandle, State};

use crate::db::{
    library, Database, LibrarySortColumn, LibraryStats, SortOrder, Track, TrackMetadata,
};
use crate::events::{EventEmitter, LibraryUpdatedEvent};
use crate::scanner::artwork::Artwork;
use crate::scanner::artwork_cache::ArtworkCache;
use crate::scanner::fingerprint::{compute_content_hash, FileFingerprint};
use crate::scanner::metadata::extract_metadata;

/// Response for paginated library queries
#[derive(Clone, serde::Serialize)]
pub struct LibraryResponse {
    pub tracks: Vec<Track>,
    pub total: i64,
    pub limit: i64,
    pub offset: i64,
}

/// Response for missing tracks queries
#[derive(Clone, serde::Serialize)]
pub struct MissingTracksResponse {
    pub tracks: Vec<Track>,
    pub total: i64,
}

/// Get all tracks with filtering, sorting, and pagination
#[tauri::command]
pub fn library_get_all(
    db: State<'_, Database>,
    search: Option<String>,
    artist: Option<String>,
    album: Option<String>,
    sort_by: Option<String>,
    sort_order: Option<String>,
    limit: Option<i64>,
    offset: Option<i64>,
) -> Result<LibraryResponse, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    // Update file sizes for tracks that have 0 (background operation)
    let _ = library::update_file_sizes(&conn);

    let query = library::LibraryQuery {
        search,
        artist,
        album,
        sort_by: sort_by
            .as_ref()
            .map(|s| LibrarySortColumn::from_str(s))
            .unwrap_or_default(),
        sort_order: sort_order
            .as_ref()
            .map(|s| {
                if s.to_lowercase() == "asc" {
                    SortOrder::Asc
                } else {
                    SortOrder::Desc
                }
            })
            .unwrap_or(SortOrder::Desc),
        limit: limit.unwrap_or(100),
        offset: offset.unwrap_or(0),
    };

    let result = library::get_all_tracks(&conn, &query).map_err(|e| e.to_string())?;

    Ok(LibraryResponse {
        tracks: result.items,
        total: result.total,
        limit: query.limit,
        offset: query.offset,
    })
}

/// Get library statistics
#[tauri::command]
pub fn library_get_stats(db: State<'_, Database>) -> Result<LibraryStats, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    library::get_library_stats(&conn).map_err(|e| e.to_string())
}

/// Get a single track by ID
#[tauri::command]
pub fn library_get_track(db: State<'_, Database>, track_id: i64) -> Result<Option<Track>, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    library::get_track_by_id(&conn, track_id).map_err(|e| e.to_string())
}

/// Get artwork for a track by ID (uses LRU cache)
#[tauri::command]
pub fn library_get_artwork(
    db: State<'_, Database>,
    cache: State<'_, ArtworkCache>,
    track_id: i64,
) -> Result<Option<Artwork>, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let track = library::get_track_by_id(&conn, track_id).map_err(|e| e.to_string())?;

    match track {
        Some(t) => Ok(cache.get_or_load(track_id, &t.filepath)),
        None => Err(format!("Track with id {} not found", track_id)),
    }
}

/// Get artwork data URL for a track by ID (for use in img src, uses LRU cache)
#[tauri::command]
pub fn library_get_artwork_url(
    db: State<'_, Database>,
    cache: State<'_, ArtworkCache>,
    track_id: i64,
) -> Result<Option<String>, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let track = library::get_track_by_id(&conn, track_id).map_err(|e| e.to_string())?;

    match track {
        Some(t) => {
            let artwork = cache.get_or_load(track_id, &t.filepath);
            Ok(artwork.map(|a| format!("data:{};base64,{}", a.mime_type, a.data)))
        }
        None => Err(format!("Track with id {} not found", track_id)),
    }
}

/// Delete a track from the library
#[tauri::command]
pub fn library_delete_track(
    app: AppHandle,
    db: State<'_, Database>,
    track_id: i64,
) -> Result<bool, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let deleted = library::delete_track(&conn, track_id).map_err(|e| e.to_string())?;

    if deleted {
        // Emit standardized library updated event
        let _ = app.emit_library_updated(LibraryUpdatedEvent::deleted(vec![track_id]));
    }

    Ok(deleted)
}

/// Rescan a track's metadata from its file
#[tauri::command]
pub fn library_rescan_track(
    app: AppHandle,
    db: State<'_, Database>,
    cache: State<'_, ArtworkCache>,
    track_id: i64,
) -> Result<Track, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    // Get the existing track
    let track = library::get_track_by_id(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| format!("Track with id {} not found", track_id))?;

    // Extract fresh metadata
    let extracted = extract_metadata(&track.filepath)
        .map_err(|e| format!("Failed to extract metadata: {}", e))?;

    // Convert to TrackMetadata for update
    let metadata = TrackMetadata {
        title: extracted.title,
        artist: extracted.artist,
        album: extracted.album,
        album_artist: extracted.album_artist,
        track_number: extracted.track_number,
        track_total: extracted.track_total,
        date: extracted.date,
        duration: extracted.duration,
        file_size: Some(extracted.file_size),
        file_mtime_ns: extracted.file_mtime_ns,
        file_inode: None,
        content_hash: None,
    };

    // Update in database
    library::update_track_metadata(&conn, track_id, &metadata).map_err(|e| e.to_string())?;

    // Invalidate artwork cache since metadata (and potentially artwork) changed
    cache.invalidate(track_id);

    // Get updated track
    let updated_track = library::get_track_by_id(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Track not found after update".to_string())?;

    // Emit standardized library updated event
    let _ = app.emit_library_updated(LibraryUpdatedEvent::modified(vec![track_id]));

    Ok(updated_track)
}

/// Increment play count for a track
#[tauri::command]
pub fn library_update_play_count(
    app: AppHandle,
    db: State<'_, Database>,
    track_id: i64,
) -> Result<Track, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let track = library::update_play_count(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| format!("Track with id {} not found", track_id))?;

    // Emit standardized library updated event
    let _ = app.emit_library_updated(LibraryUpdatedEvent::modified(vec![track_id]));

    Ok(track)
}

/// Get all tracks marked as missing
#[tauri::command]
pub fn library_get_missing(db: State<'_, Database>) -> Result<MissingTracksResponse, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let tracks = library::get_missing_tracks(&conn).map_err(|e| e.to_string())?;
    let total = tracks.len() as i64;

    Ok(MissingTracksResponse { tracks, total })
}

/// Update a missing track's filepath after user locates the file
#[tauri::command]
pub fn library_locate_track(
    app: AppHandle,
    db: State<'_, Database>,
    track_id: i64,
    new_path: String,
) -> Result<Track, String> {
    // Verify the new path exists
    if !Path::new(&new_path).exists() {
        return Err(format!("File not found: {}", new_path));
    }

    let conn = db.conn().map_err(|e| e.to_string())?;

    // Verify the track exists
    library::get_track_by_id(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| format!("Track with id {} not found", track_id))?;

    // Update the filepath
    library::update_track_filepath(&conn, track_id, &new_path).map_err(|e| e.to_string())?;

    // Get updated track
    let updated_track = library::get_track_by_id(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Track not found after update".to_string())?;

    // Emit standardized library updated event
    let _ = app.emit_library_updated(LibraryUpdatedEvent::modified(vec![track_id]));

    Ok(updated_track)
}

/// Check if a track's file exists and update its missing status
#[tauri::command]
pub fn library_check_status(
    app: AppHandle,
    db: State<'_, Database>,
    track_id: i64,
) -> Result<Track, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let track = library::check_and_update_track_status(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| format!("Track with id {} not found", track_id))?;

    // Emit standardized library updated event
    let _ = app.emit_library_updated(LibraryUpdatedEvent::modified(vec![track_id]));

    Ok(track)
}

/// Manually mark a track as missing
#[tauri::command]
pub fn library_mark_missing(
    app: AppHandle,
    db: State<'_, Database>,
    track_id: i64,
) -> Result<Track, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let marked = library::mark_track_missing(&conn, track_id).map_err(|e| e.to_string())?;

    if !marked {
        return Err(format!("Track with id {} not found", track_id));
    }

    let track = library::get_track_by_id(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Track not found after marking".to_string())?;

    // Emit standardized library updated event
    let _ = app.emit_library_updated(LibraryUpdatedEvent::modified(vec![track_id]));

    Ok(track)
}

/// Manually mark a track as present (not missing)
#[tauri::command]
pub fn library_mark_present(
    app: AppHandle,
    db: State<'_, Database>,
    track_id: i64,
) -> Result<Track, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let marked = library::mark_track_present(&conn, track_id).map_err(|e| e.to_string())?;

    if !marked {
        return Err(format!("Track with id {} not found", track_id));
    }

    let track = library::get_track_by_id(&conn, track_id)
        .map_err(|e| e.to_string())?
        .ok_or_else(|| "Track not found after marking".to_string())?;

    // Emit standardized library updated event
    let _ = app.emit_library_updated(LibraryUpdatedEvent::modified(vec![track_id]));

    Ok(track)
}

#[derive(Clone, serde::Serialize)]
pub struct ReconcileScanResult {
    pub backfilled: u32,
    pub duplicates_merged: u32,
    pub errors: u32,
}

#[tauri::command]
pub fn library_reconcile_scan(
    app: AppHandle,
    db: State<'_, Database>,
) -> Result<ReconcileScanResult, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;

    let mut backfilled = 0u32;
    let mut errors = 0u32;

    let tracks = library::get_tracks_needing_fingerprints(&conn).map_err(|e| e.to_string())?;

    for track in tracks {
        let path = std::path::Path::new(&track.filepath);
        if !path.exists() {
            continue;
        }

        let fingerprint = match FileFingerprint::from_path(path) {
            Ok(fp) => fp,
            Err(_) => {
                errors += 1;
                continue;
            }
        };

        let content_hash = match compute_content_hash(path) {
            Ok(h) => Some(h),
            Err(_) => {
                errors += 1;
                None
            }
        };

        match library::update_track_fingerprints(
            &conn,
            track.id,
            fingerprint.inode,
            content_hash.as_deref(),
        ) {
            Ok(true) => backfilled += 1,
            Ok(false) => {}
            Err(_) => errors += 1,
        }
    }

    let mut duplicates_merged = 0u32;
    let mut deleted_ids = Vec::new();

    let inode_dups = library::find_duplicates_by_inode(&conn).map_err(|e| e.to_string())?;
    for group in inode_dups {
        if group.len() < 2 {
            continue;
        }
        let keep = &group[0];
        for dup in &group[1..] {
            match library::merge_duplicate_tracks(&conn, keep.id, dup.id) {
                Ok(true) => {
                    duplicates_merged += 1;
                    deleted_ids.push(dup.id);
                }
                Ok(false) => {}
                Err(_) => errors += 1,
            }
        }
    }

    let hash_dups = library::find_duplicates_by_content_hash(&conn).map_err(|e| e.to_string())?;
    for group in hash_dups {
        if group.len() < 2 {
            continue;
        }
        let keep = &group[0];
        for dup in &group[1..] {
            if deleted_ids.contains(&dup.id) {
                continue;
            }
            match library::merge_duplicate_tracks(&conn, keep.id, dup.id) {
                Ok(true) => {
                    duplicates_merged += 1;
                    deleted_ids.push(dup.id);
                }
                Ok(false) => {}
                Err(_) => errors += 1,
            }
        }
    }

    if !deleted_ids.is_empty() {
        let _ = app.emit_library_updated(LibraryUpdatedEvent::deleted(deleted_ids));
    }

    Ok(ReconcileScanResult {
        backfilled,
        duplicates_merged,
        errors,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_library_response_serialization() {
        let response = LibraryResponse {
            tracks: vec![],
            total: 0,
            limit: 100,
            offset: 0,
        };

        let json = serde_json::to_string(&response).unwrap();
        assert!(json.contains("\"total\":0"));
        assert!(json.contains("\"limit\":100"));
    }
}
