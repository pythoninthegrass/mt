//! Tauri commands for queue management.
//!
//! These commands expose queue operations to the frontend,
//! replacing the Python FastAPI queue routes.

use rand::rng;
use rand::seq::SliceRandom;
use tauri::{AppHandle, Emitter, State};

use crate::db::{queue, Database, QueueItem, Track};

/// Response for queue get operations
#[derive(Clone, serde::Serialize)]
pub struct QueueResponse {
    pub items: Vec<QueueItem>,
    pub count: i64,
}

/// Response for queue add operations
#[derive(Clone, serde::Serialize)]
pub struct QueueAddResponse {
    pub added: i64,
    pub queue_length: i64,
}

/// Response for queue add-files operations
#[derive(Clone, serde::Serialize)]
pub struct QueueAddFilesResponse {
    pub added: i64,
    pub queue_length: i64,
    pub tracks: Vec<Track>,
}

/// Response for queue operations that return success status
#[derive(Clone, serde::Serialize)]
pub struct QueueOperationResponse {
    pub success: bool,
    pub queue_length: i64,
}

/// Get the current playback queue with track metadata
#[tauri::command]
pub fn queue_get(db: State<'_, Database>) -> Result<QueueResponse, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    let items = queue::get_queue(&conn).map_err(|e| e.to_string())?;
    let count = items.len() as i64;

    Ok(QueueResponse { items, count })
}

/// Add tracks to the queue by track IDs
#[tauri::command]
pub fn queue_add(
    app: AppHandle,
    db: State<'_, Database>,
    track_ids: Vec<i64>,
    position: Option<i64>,
) -> Result<QueueAddResponse, String> {
    if track_ids.is_empty() {
        return Err("track_ids must not be empty".to_string());
    }

    let conn = db.conn().map_err(|e| e.to_string())?;
    let added = queue::add_to_queue(&conn, &track_ids, position).map_err(|e| e.to_string())?;
    let queue_length = queue::get_queue_length(&conn).map_err(|e| e.to_string())?;

    // Emit queue updated event
    let _ = app.emit("queue:updated", ());

    Ok(QueueAddResponse {
        added,
        queue_length,
    })
}

/// Add files directly to the queue (for drag-and-drop support)
#[tauri::command]
pub fn queue_add_files(
    app: AppHandle,
    db: State<'_, Database>,
    filepaths: Vec<String>,
    position: Option<i64>,
) -> Result<QueueAddFilesResponse, String> {
    if filepaths.is_empty() {
        return Err("filepaths must not be empty".to_string());
    }

    let conn = db.conn().map_err(|e| e.to_string())?;
    let (added, tracks) =
        queue::add_files_to_queue(&conn, &filepaths, position).map_err(|e| e.to_string())?;
    let queue_length = queue::get_queue_length(&conn).map_err(|e| e.to_string())?;

    // Emit queue updated event
    let _ = app.emit("queue:updated", ());

    Ok(QueueAddFilesResponse {
        added,
        queue_length,
        tracks,
    })
}

/// Remove a track from the queue by position
#[tauri::command]
pub fn queue_remove(
    app: AppHandle,
    db: State<'_, Database>,
    position: i64,
) -> Result<(), String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    let removed = queue::remove_from_queue(&conn, position).map_err(|e| e.to_string())?;

    if !removed {
        return Err(format!("No track at position {}", position));
    }

    // Emit queue updated event
    let _ = app.emit("queue:updated", ());

    Ok(())
}

/// Clear the entire queue
#[tauri::command]
pub fn queue_clear(app: AppHandle, db: State<'_, Database>) -> Result<(), String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    queue::clear_queue(&conn).map_err(|e| e.to_string())?;

    // Emit queue updated event
    let _ = app.emit("queue:updated", ());

    Ok(())
}

/// Reorder tracks in the queue (move from one position to another)
#[tauri::command]
pub fn queue_reorder(
    app: AppHandle,
    db: State<'_, Database>,
    from_position: i64,
    to_position: i64,
) -> Result<QueueOperationResponse, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    let success =
        queue::reorder_queue(&conn, from_position, to_position).map_err(|e| e.to_string())?;

    if !success {
        return Err("Invalid positions".to_string());
    }

    let queue_length = queue::get_queue_length(&conn).map_err(|e| e.to_string())?;

    // Emit queue updated event
    let _ = app.emit("queue:updated", ());

    Ok(QueueOperationResponse {
        success,
        queue_length,
    })
}

/// Shuffle the queue using Fisher-Yates algorithm
#[tauri::command]
pub fn queue_shuffle(
    app: AppHandle,
    db: State<'_, Database>,
    keep_current: Option<bool>,
) -> Result<QueueOperationResponse, String> {
    let conn = db.conn().map_err(|e| e.to_string())?;
    let items = queue::get_queue(&conn).map_err(|e| e.to_string())?;

    if items.is_empty() {
        return Ok(QueueOperationResponse {
            success: true,
            queue_length: 0,
        });
    }

    // Get filepaths from queue items
    let mut filepaths: Vec<String> = items.iter().map(|item| item.track.filepath.clone()).collect();

    let keep_current = keep_current.unwrap_or(true);

    if keep_current && !filepaths.is_empty() {
        // Keep first item, shuffle rest using Fisher-Yates
        let first = filepaths.remove(0);
        filepaths.shuffle(&mut rng());
        filepaths.insert(0, first);
    } else {
        // Shuffle all items
        filepaths.shuffle(&mut rng());
    }

    // Rebuild queue with shuffled order
    queue::clear_queue(&conn).map_err(|e| e.to_string())?;

    for filepath in &filepaths {
        conn.execute(
            "INSERT INTO queue (filepath) VALUES (?)",
            rusqlite::params![filepath],
        )
        .map_err(|e| e.to_string())?;
    }

    let queue_length = queue::get_queue_length(&conn).map_err(|e| e.to_string())?;

    // Emit queue updated event
    let _ = app.emit("queue:updated", ());

    Ok(QueueOperationResponse {
        success: true,
        queue_length,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_queue_response_serialization() {
        let response = QueueResponse {
            items: vec![],
            count: 0,
        };

        let json = serde_json::to_string(&response).unwrap();
        assert!(json.contains("\"count\":0"));
        assert!(json.contains("\"items\":[]"));
    }

    #[test]
    fn test_queue_add_response_serialization() {
        let response = QueueAddResponse {
            added: 3,
            queue_length: 10,
        };

        let json = serde_json::to_string(&response).unwrap();
        assert!(json.contains("\"added\":3"));
        assert!(json.contains("\"queue_length\":10"));
    }
}
