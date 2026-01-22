//! Tauri event types for real-time UI updates.
//!
//! This module defines all event types that can be emitted from the Rust backend
//! to the frontend. These replace the WebSocket events from the Python backend.
//!
//! Event naming convention: `domain:action` (e.g., `library:updated`)

use serde::Serialize;

// ============================================
// Library Events
// ============================================

/// Emitted when library tracks are added, modified, or deleted
#[derive(Clone, Debug, Serialize)]
pub struct LibraryUpdatedEvent {
    /// The type of change: "added", "modified", "deleted"
    pub action: String,
    /// The IDs of affected tracks
    pub track_ids: Vec<i64>,
}

impl LibraryUpdatedEvent {
    pub const EVENT_NAME: &'static str = "library:updated";

    pub fn added(track_ids: Vec<i64>) -> Self {
        Self {
            action: "added".to_string(),
            track_ids,
        }
    }

    pub fn modified(track_ids: Vec<i64>) -> Self {
        Self {
            action: "modified".to_string(),
            track_ids,
        }
    }

    pub fn deleted(track_ids: Vec<i64>) -> Self {
        Self {
            action: "deleted".to_string(),
            track_ids,
        }
    }
}

/// Emitted during library scan to report progress
#[derive(Clone, Debug, Serialize)]
pub struct ScanProgressEvent {
    /// Unique identifier for this scan job
    pub job_id: String,
    /// Current status: "scanning", "processing", "complete", "error"
    pub status: String,
    /// Number of files scanned so far
    pub scanned: u32,
    /// Number of new tracks found
    pub found: u32,
    /// Number of errors encountered
    pub errors: u32,
    /// Current file/directory being processed
    pub current_path: Option<String>,
}

impl ScanProgressEvent {
    pub const EVENT_NAME: &'static str = "library:scan-progress";
}

/// Emitted when a library scan completes
#[derive(Clone, Debug, Serialize)]
pub struct ScanCompleteEvent {
    /// Unique identifier for the completed scan job
    pub job_id: String,
    /// Number of tracks added to library
    pub added: u32,
    /// Number of files skipped (already in library or not audio)
    pub skipped: u32,
    /// Number of errors during scan
    pub errors: u32,
    /// Total scan duration in milliseconds
    pub duration_ms: u64,
}

impl ScanCompleteEvent {
    pub const EVENT_NAME: &'static str = "library:scan-complete";
}

// ============================================
// Queue Events
// ============================================

/// Emitted when the playback queue changes
#[derive(Clone, Debug, Serialize)]
pub struct QueueUpdatedEvent {
    /// The type of change: "added", "removed", "cleared", "reordered", "shuffled"
    pub action: String,
    /// Affected positions in the queue (if applicable)
    pub positions: Option<Vec<i64>>,
    /// Current queue length after the change
    pub queue_length: i64,
}

impl QueueUpdatedEvent {
    pub const EVENT_NAME: &'static str = "queue:updated";

    pub fn added(positions: Vec<i64>, queue_length: i64) -> Self {
        Self {
            action: "added".to_string(),
            positions: Some(positions),
            queue_length,
        }
    }

    pub fn removed(position: i64, queue_length: i64) -> Self {
        Self {
            action: "removed".to_string(),
            positions: Some(vec![position]),
            queue_length,
        }
    }

    pub fn cleared() -> Self {
        Self {
            action: "cleared".to_string(),
            positions: None,
            queue_length: 0,
        }
    }

    pub fn reordered(from: i64, to: i64, queue_length: i64) -> Self {
        Self {
            action: "reordered".to_string(),
            positions: Some(vec![from, to]),
            queue_length,
        }
    }

    pub fn shuffled(queue_length: i64) -> Self {
        Self {
            action: "shuffled".to_string(),
            positions: None,
            queue_length,
        }
    }
}

// ============================================
// Favorites Events
// ============================================

/// Emitted when a track is added to or removed from favorites
#[derive(Clone, Debug, Serialize)]
pub struct FavoritesUpdatedEvent {
    /// The type of change: "added", "removed"
    pub action: String,
    /// The track ID that was affected
    pub track_id: i64,
}

impl FavoritesUpdatedEvent {
    pub const EVENT_NAME: &'static str = "favorites:updated";

    pub fn added(track_id: i64) -> Self {
        Self {
            action: "added".to_string(),
            track_id,
        }
    }

    pub fn removed(track_id: i64) -> Self {
        Self {
            action: "removed".to_string(),
            track_id,
        }
    }
}

// ============================================
// Playlist Events
// ============================================

/// Emitted when a playlist is created, modified, or deleted
#[derive(Clone, Debug, Serialize)]
pub struct PlaylistsUpdatedEvent {
    /// The type of change: "created", "renamed", "deleted", "tracks_added", "tracks_removed", "reordered"
    pub action: String,
    /// The playlist ID that was affected
    pub playlist_id: i64,
    /// Track IDs involved in the change (for track operations)
    pub track_ids: Option<Vec<i64>>,
}

impl PlaylistsUpdatedEvent {
    pub const EVENT_NAME: &'static str = "playlists:updated";

    pub fn created(playlist_id: i64) -> Self {
        Self {
            action: "created".to_string(),
            playlist_id,
            track_ids: None,
        }
    }

    pub fn renamed(playlist_id: i64) -> Self {
        Self {
            action: "renamed".to_string(),
            playlist_id,
            track_ids: None,
        }
    }

    pub fn deleted(playlist_id: i64) -> Self {
        Self {
            action: "deleted".to_string(),
            playlist_id,
            track_ids: None,
        }
    }

    pub fn tracks_added(playlist_id: i64, track_ids: Vec<i64>) -> Self {
        Self {
            action: "tracks_added".to_string(),
            playlist_id,
            track_ids: Some(track_ids),
        }
    }

    pub fn tracks_removed(playlist_id: i64, track_ids: Vec<i64>) -> Self {
        Self {
            action: "tracks_removed".to_string(),
            playlist_id,
            track_ids: Some(track_ids),
        }
    }

    pub fn reordered(playlist_id: i64) -> Self {
        Self {
            action: "reordered".to_string(),
            playlist_id,
            track_ids: None,
        }
    }
}

// ============================================
// Settings Events
// ============================================

/// Emitted when a setting value changes
#[derive(Clone, Debug, Serialize)]
pub struct SettingsUpdatedEvent {
    /// The setting key that changed
    pub key: String,
    /// The new value (as JSON value)
    pub value: serde_json::Value,
    /// The previous value (as JSON value, if available)
    pub previous_value: Option<serde_json::Value>,
}

impl SettingsUpdatedEvent {
    pub const EVENT_NAME: &'static str = "settings:updated";

    pub fn new(key: String, value: serde_json::Value, previous_value: Option<serde_json::Value>) -> Self {
        Self {
            key,
            value,
            previous_value,
        }
    }
}

// ============================================
// Helper trait for emitting events
// ============================================

/// Extension trait for emitting typed events
pub trait EventEmitter {
    fn emit_library_updated(&self, event: LibraryUpdatedEvent) -> Result<(), String>;
    fn emit_scan_progress(&self, event: ScanProgressEvent) -> Result<(), String>;
    fn emit_scan_complete(&self, event: ScanCompleteEvent) -> Result<(), String>;
    fn emit_queue_updated(&self, event: QueueUpdatedEvent) -> Result<(), String>;
    fn emit_favorites_updated(&self, event: FavoritesUpdatedEvent) -> Result<(), String>;
    fn emit_playlists_updated(&self, event: PlaylistsUpdatedEvent) -> Result<(), String>;
    fn emit_settings_updated(&self, event: SettingsUpdatedEvent) -> Result<(), String>;
}

impl EventEmitter for tauri::AppHandle {
    fn emit_library_updated(&self, event: LibraryUpdatedEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(LibraryUpdatedEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }

    fn emit_scan_progress(&self, event: ScanProgressEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(ScanProgressEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }

    fn emit_scan_complete(&self, event: ScanCompleteEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(ScanCompleteEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }

    fn emit_queue_updated(&self, event: QueueUpdatedEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(QueueUpdatedEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }

    fn emit_favorites_updated(&self, event: FavoritesUpdatedEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(FavoritesUpdatedEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }

    fn emit_playlists_updated(&self, event: PlaylistsUpdatedEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(PlaylistsUpdatedEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }

    fn emit_settings_updated(&self, event: SettingsUpdatedEvent) -> Result<(), String> {
        use tauri::Emitter;
        self.emit(SettingsUpdatedEvent::EVENT_NAME, event)
            .map_err(|e| e.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_library_updated_event_serialization() {
        let event = LibraryUpdatedEvent::added(vec![1, 2, 3]);
        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("\"action\":\"added\""));
        assert!(json.contains("\"track_ids\":[1,2,3]"));
    }

    #[test]
    fn test_queue_updated_event_serialization() {
        let event = QueueUpdatedEvent::added(vec![0, 1], 5);
        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("\"action\":\"added\""));
        assert!(json.contains("\"queue_length\":5"));
    }

    #[test]
    fn test_favorites_updated_event_serialization() {
        let event = FavoritesUpdatedEvent::added(42);
        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("\"action\":\"added\""));
        assert!(json.contains("\"track_id\":42"));
    }

    #[test]
    fn test_settings_updated_event_serialization() {
        let event = SettingsUpdatedEvent::new(
            "volume".to_string(),
            serde_json::json!(0.8),
            Some(serde_json::json!(0.5)),
        );
        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("\"key\":\"volume\""));
        assert!(json.contains("\"value\":0.8"));
    }
}
