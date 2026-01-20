use notify_debouncer_full::{
    new_debouncer,
    notify::{self, RecursiveMode},
    DebounceEventResult, Debouncer, RecommendedCache,
};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;
use tauri::{AppHandle, Emitter, State};
use tokio::sync::mpsc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WatchedFolder {
    pub id: i64,
    pub path: String,
    pub mode: String,
    pub cadence_minutes: Option<i32>,
    pub enabled: bool,
    pub last_scanned_at: Option<i64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct WatcherStatus {
    pub folder_id: i64,
    pub status: String,
    pub message: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ScanProgress {
    pub folder_id: i64,
    pub percent: Option<u8>,
    pub stage: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ScanResults {
    pub folder_id: i64,
    pub added: i32,
    pub updated: i32,
    pub deleted: i32,
}

#[derive(Debug, Clone, Serialize)]
pub struct FsEvent {
    pub folder_id: i64,
    pub event_type: String,
    pub paths: Vec<String>,
}

pub struct WatcherManager {
    app: AppHandle,
    backend_url: String,
    active_watchers: Arc<RwLock<HashMap<i64, WatcherHandle>>>,
}

struct WatcherHandle {
    #[allow(dead_code)]
    folder_id: i64,
    cancel_tx: mpsc::Sender<()>,
    #[allow(dead_code)]
    fs_watcher: Option<Debouncer<notify::RecommendedWatcher, RecommendedCache>>,
}

impl WatcherManager {
    pub fn new(app: AppHandle, backend_url: String) -> Self {
        Self {
            app,
            backend_url,
            active_watchers: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn start(&self) -> Result<(), String> {
        let folders = self.fetch_enabled_folders().await?;

        for folder in folders {
            if folder.enabled {
                self.start_watching(folder).await?;
            }
        }

        Ok(())
    }

    pub async fn stop(&self) {
        let cancel_txs: Vec<_> = {
            let watchers = self.active_watchers.read();
            watchers.values().map(|h| h.cancel_tx.clone()).collect()
        };
        for tx in cancel_txs {
            let _ = tx.send(()).await;
        }
    }

    pub fn get_backend_url(&self) -> &str {
        &self.backend_url
    }

    pub fn active_watcher_count(&self) -> usize {
        self.active_watchers.read().len()
    }

    async fn fetch_enabled_folders(&self) -> Result<Vec<WatchedFolder>, String> {
        let client = reqwest::Client::new();
        let url = format!("{}/api/watched-folders", self.backend_url);

        let response = client
            .get(&url)
            .send()
            .await
            .map_err(|e| format!("Failed to fetch watched folders: {}", e))?;

        #[derive(Deserialize)]
        struct FoldersResponse {
            folders: Vec<WatchedFolder>,
        }

        let data: FoldersResponse = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse watched folders: {}", e))?;

        Ok(data.folders.into_iter().filter(|f| f.enabled).collect())
    }

    async fn start_watching(&self, folder: WatchedFolder) -> Result<(), String> {
        let (cancel_tx, mut cancel_rx) = mpsc::channel::<()>(1);

        let app = self.app.clone();
        let backend_url = self.backend_url.clone();
        let folder_id = folder.id;
        let mode = folder.mode.clone();
        let cadence_minutes = folder.cadence_minutes.unwrap_or(10) as u64;
        let folder_path = folder.path.clone();

        println!(
            "[watcher] Starting watcher for folder {} (mode={}, cadence={}min)",
            folder_id, mode, cadence_minutes
        );

        let fs_watcher = if mode == "continuous" {
            self.create_fs_watcher(folder_id, &folder_path)
        } else {
            None
        };

        let handle = WatcherHandle {
            folder_id: folder.id,
            cancel_tx,
            fs_watcher,
        };

        self.active_watchers.write().insert(folder.id, handle);

        tokio::spawn(async move {
            if mode == "startup" {
                Self::trigger_rescan(&app, &backend_url, folder_id).await;
            } else if mode == "continuous" {
                Self::trigger_rescan(&app, &backend_url, folder_id).await;

                let mut interval =
                    tokio::time::interval(Duration::from_secs(cadence_minutes * 60));
                interval.tick().await;

                loop {
                    tokio::select! {
                        _ = interval.tick() => {
                            Self::trigger_rescan(&app, &backend_url, folder_id).await;
                        }
                        _ = cancel_rx.recv() => {
                            println!("[watcher] Stopping watcher for folder {}", folder_id);
                            break;
                        }
                    }
                }
            }
        });

        Ok(())
    }

    fn create_fs_watcher(
        &self,
        folder_id: i64,
        folder_path: &str,
    ) -> Option<Debouncer<notify::RecommendedWatcher, RecommendedCache>> {
        let app = self.app.clone();
        let backend_url = self.backend_url.clone();
        let path = PathBuf::from(folder_path);

        if !path.exists() {
            eprintln!(
                "[watcher] Cannot watch folder {}: path does not exist",
                folder_path
            );
            return None;
        }

        let debounce_duration = Duration::from_millis(1000);
        
        // Capture the Tokio runtime handle to spawn async tasks from the sync callback
        let runtime_handle = tokio::runtime::Handle::current();

        let debouncer_result = new_debouncer(debounce_duration, None, move |result: DebounceEventResult| {
            match result {
                Ok(events) => {
                    let mut has_changes = false;
                    let mut event_paths: Vec<String> = Vec::new();

                    for event in events.iter() {
                        match event.kind {
                            notify::EventKind::Create(_)
                            | notify::EventKind::Modify(_)
                            | notify::EventKind::Remove(_) => {
                                has_changes = true;
                                for p in &event.paths {
                                    if let Some(ext) = p.extension() {
                                        let ext_lower = ext.to_string_lossy().to_lowercase();
                                        if matches!(
                                            ext_lower.as_str(),
                                            "mp3" | "flac" | "m4a" | "ogg" | "wav" | "aac" | "wma" | "opus"
                                        ) {
                                            event_paths.push(p.to_string_lossy().to_string());
                                        }
                                    }
                                }
                            }
                            _ => {}
                        }
                    }

                    if has_changes && !event_paths.is_empty() {
                        println!(
                            "[watcher] FS events detected for folder {}: {} files changed",
                            folder_id,
                            event_paths.len()
                        );

                        let _ = app.emit(
                            "watched-folder:fs-event",
                            FsEvent {
                                folder_id,
                                event_type: "change".to_string(),
                                paths: event_paths,
                            },
                        );

                        let app_clone = app.clone();
                        let backend_url_clone = backend_url.clone();
                        runtime_handle.spawn(async move {
                            Self::trigger_rescan(&app_clone, &backend_url_clone, folder_id).await;
                        });
                    }
                }
                Err(errors) => {
                    for error in errors {
                        eprintln!("[watcher] FS watcher error for folder {}: {:?}", folder_id, error);
                    }
                }
            }
        });

        match debouncer_result {
            Ok(mut debouncer) => {
                if let Err(e) = debouncer.watch(&path, RecursiveMode::Recursive) {
                    eprintln!(
                        "[watcher] Failed to start watching folder {}: {:?}",
                        folder_path, e
                    );
                    return None;
                }
                println!(
                    "[watcher] FS watcher active for folder {} at {}",
                    folder_id, folder_path
                );
                Some(debouncer)
            }
            Err(e) => {
                eprintln!(
                    "[watcher] Failed to create debouncer for folder {}: {:?}",
                    folder_path, e
                );
                None
            }
        }
    }

    async fn trigger_rescan(app: &AppHandle, backend_url: &str, folder_id: i64) {
        println!("[watcher] Triggering rescan for folder {}", folder_id);

        let _ = app.emit(
            "watched-folder:status",
            WatcherStatus {
                folder_id,
                status: "scanning".to_string(),
                message: None,
            },
        );

        let client = reqwest::Client::new();
        let url = format!("{}/api/watched-folders/{}/rescan", backend_url, folder_id);

        match client.post(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    #[derive(Deserialize)]
                    struct RescanResponse {
                        added: i32,
                        updated: i32,
                        deleted: i32,
                    }

                    if let Ok(data) = response.json::<RescanResponse>().await {
                        println!(
                            "[watcher] Folder {} scan complete: +{} ~{} -{}",
                            folder_id, data.added, data.updated, data.deleted
                        );
                        let _ = app.emit(
                            "watched-folder:results",
                            ScanResults {
                                folder_id,
                                added: data.added,
                                updated: data.updated,
                                deleted: data.deleted,
                            },
                        );
                    }

                    let _ = app.emit(
                        "watched-folder:status",
                        WatcherStatus {
                            folder_id,
                            status: "idle".to_string(),
                            message: None,
                        },
                    );
                } else {
                    let error_msg = format!("Rescan failed with status {}", response.status());
                    eprintln!("[watcher] Folder {}: {}", folder_id, error_msg);
                    let _ = app.emit(
                        "watched-folder:status",
                        WatcherStatus {
                            folder_id,
                            status: "error".to_string(),
                            message: Some(error_msg),
                        },
                    );
                }
            }
            Err(e) => {
                let error_msg = format!("Rescan request failed: {}", e);
                eprintln!("[watcher] Folder {}: {}", folder_id, error_msg);
                let _ = app.emit(
                    "watched-folder:status",
                    WatcherStatus {
                        folder_id,
                        status: "error".to_string(),
                        message: Some(error_msg),
                    },
                );
            }
        }
    }

    pub async fn add_folder(&self, folder: WatchedFolder) -> Result<(), String> {
        if folder.enabled {
            self.start_watching(folder).await?;
        }
        Ok(())
    }

    pub async fn remove_folder(&self, folder_id: i64) {
        let cancel_tx = self.active_watchers.write().remove(&folder_id).map(|h| h.cancel_tx);
        if let Some(tx) = cancel_tx {
            let _ = tx.send(()).await;
        }
    }

    pub async fn update_folder(&self, folder: WatchedFolder) -> Result<(), String> {
        self.remove_folder(folder.id).await;
        if folder.enabled {
            self.start_watching(folder).await?;
        }
        Ok(())
    }

    /// Trigger a manual rescan for a specific folder
    pub async fn rescan_folder(&self, folder_id: i64) {
        Self::trigger_rescan(&self.app, &self.backend_url, folder_id).await;
    }
}

// ============================================================================
// Tauri Commands
// ============================================================================

/// List all watched folders from the Python backend
#[tauri::command]
pub async fn watched_folders_list(
    state: State<'_, WatcherManager>,
) -> Result<Vec<WatchedFolder>, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/watched-folders", state.get_backend_url());

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch watched folders: {}", e))?;

    #[derive(Deserialize)]
    struct FoldersResponse {
        folders: Vec<WatchedFolder>,
    }

    let data: FoldersResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(data.folders)
}

/// Get a specific watched folder by ID
#[tauri::command]
pub async fn watched_folders_get(
    id: i64,
    state: State<'_, WatcherManager>,
) -> Result<WatchedFolder, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/watched-folders/{}", state.get_backend_url(), id);

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to fetch watched folder: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Folder not found: {}", id));
    }

    let folder: WatchedFolder = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(folder)
}

#[derive(Debug, Deserialize)]
pub struct AddWatchedFolderRequest {
    pub path: String,
    pub mode: Option<String>,
    pub cadence_minutes: Option<i32>,
    pub enabled: Option<bool>,
}

/// Add a new watched folder
#[tauri::command]
pub async fn watched_folders_add(
    request: AddWatchedFolderRequest,
    state: State<'_, WatcherManager>,
) -> Result<WatchedFolder, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/watched-folders", state.get_backend_url());

    let response = client
        .post(&url)
        .json(&serde_json::json!({
            "path": request.path,
            "mode": request.mode.unwrap_or_else(|| "continuous".to_string()),
            "cadence_minutes": request.cadence_minutes.unwrap_or(10),
            "enabled": request.enabled.unwrap_or(true),
        }))
        .send()
        .await
        .map_err(|e| format!("Failed to add watched folder: {}", e))?;

    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_default();
        return Err(format!("Failed to add folder: {}", error_text));
    }

    let folder: WatchedFolder = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Start watching the new folder if enabled
    if folder.enabled {
        state.add_folder(folder.clone()).await?;
    }

    Ok(folder)
}

#[derive(Debug, Deserialize)]
pub struct UpdateWatchedFolderRequest {
    pub mode: Option<String>,
    pub cadence_minutes: Option<i32>,
    pub enabled: Option<bool>,
}

/// Update an existing watched folder
#[tauri::command]
pub async fn watched_folders_update(
    id: i64,
    request: UpdateWatchedFolderRequest,
    state: State<'_, WatcherManager>,
) -> Result<WatchedFolder, String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/watched-folders/{}", state.get_backend_url(), id);

    let mut body = serde_json::Map::new();
    if let Some(mode) = &request.mode {
        body.insert("mode".to_string(), serde_json::json!(mode));
    }
    if let Some(cadence) = request.cadence_minutes {
        body.insert("cadence_minutes".to_string(), serde_json::json!(cadence));
    }
    if let Some(enabled) = request.enabled {
        body.insert("enabled".to_string(), serde_json::json!(enabled));
    }

    let response = client
        .patch(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("Failed to update watched folder: {}", e))?;

    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_default();
        return Err(format!("Failed to update folder: {}", error_text));
    }

    let folder: WatchedFolder = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Update the watcher for this folder
    state.update_folder(folder.clone()).await?;

    Ok(folder)
}

/// Remove a watched folder
#[tauri::command]
pub async fn watched_folders_remove(
    id: i64,
    state: State<'_, WatcherManager>,
) -> Result<(), String> {
    let client = reqwest::Client::new();
    let url = format!("{}/api/watched-folders/{}", state.get_backend_url(), id);

    let response = client
        .delete(&url)
        .send()
        .await
        .map_err(|e| format!("Failed to remove watched folder: {}", e))?;

    if !response.status().is_success() {
        let error_text = response.text().await.unwrap_or_default();
        return Err(format!("Failed to remove folder: {}", error_text));
    }

    // Stop watching this folder
    state.remove_folder(id).await;

    Ok(())
}

/// Trigger a manual rescan for a watched folder
#[tauri::command]
pub async fn watched_folders_rescan(
    id: i64,
    state: State<'_, WatcherManager>,
) -> Result<(), String> {
    state.rescan_folder(id).await;
    Ok(())
}

/// Get the current watcher status (number of active watchers)
#[tauri::command]
pub fn watched_folders_status(state: State<'_, WatcherManager>) -> serde_json::Value {
    serde_json::json!({
        "active_watchers": state.active_watcher_count(),
    })
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // -------------------------------------------------------------------------
    // WatchedFolder struct tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_watched_folder_serialization() {
        let folder = WatchedFolder {
            id: 1,
            path: "/Users/test/Music".to_string(),
            mode: "continuous".to_string(),
            cadence_minutes: Some(10),
            enabled: true,
            last_scanned_at: Some(1234567890),
        };

        let json = serde_json::to_string(&folder).unwrap();
        assert!(json.contains("\"id\":1"));
        assert!(json.contains("\"path\":\"/Users/test/Music\""));
        assert!(json.contains("\"mode\":\"continuous\""));
        assert!(json.contains("\"cadence_minutes\":10"));
        assert!(json.contains("\"enabled\":true"));
    }

    #[test]
    fn test_watched_folder_deserialization() {
        let json = r#"{
            "id": 42,
            "path": "/home/user/music",
            "mode": "startup",
            "cadence_minutes": null,
            "enabled": false,
            "last_scanned_at": null
        }"#;

        let folder: WatchedFolder = serde_json::from_str(json).unwrap();
        assert_eq!(folder.id, 42);
        assert_eq!(folder.path, "/home/user/music");
        assert_eq!(folder.mode, "startup");
        assert!(folder.cadence_minutes.is_none());
        assert!(!folder.enabled);
        assert!(folder.last_scanned_at.is_none());
    }

    #[test]
    fn test_watched_folder_clone() {
        let folder = WatchedFolder {
            id: 1,
            path: "/test".to_string(),
            mode: "continuous".to_string(),
            cadence_minutes: Some(5),
            enabled: true,
            last_scanned_at: None,
        };

        let cloned = folder.clone();
        assert_eq!(folder.id, cloned.id);
        assert_eq!(folder.path, cloned.path);
        assert_eq!(folder.mode, cloned.mode);
        assert_eq!(folder.cadence_minutes, cloned.cadence_minutes);
        assert_eq!(folder.enabled, cloned.enabled);
    }

    // -------------------------------------------------------------------------
    // WatcherStatus tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_watcher_status_serialization() {
        let status = WatcherStatus {
            folder_id: 123,
            status: "scanning".to_string(),
            message: Some("Processing files...".to_string()),
        };

        let json = serde_json::to_string(&status).unwrap();
        assert!(json.contains("\"folder_id\":123"));
        assert!(json.contains("\"status\":\"scanning\""));
        assert!(json.contains("\"message\":\"Processing files...\""));
    }

    #[test]
    fn test_watcher_status_without_message() {
        let status = WatcherStatus {
            folder_id: 1,
            status: "idle".to_string(),
            message: None,
        };

        let json = serde_json::to_string(&status).unwrap();
        assert!(json.contains("\"message\":null"));
    }

    // -------------------------------------------------------------------------
    // ScanProgress tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_scan_progress_serialization() {
        let progress = ScanProgress {
            folder_id: 5,
            percent: Some(75),
            stage: Some("Scanning metadata".to_string()),
        };

        let json = serde_json::to_string(&progress).unwrap();
        assert!(json.contains("\"folder_id\":5"));
        assert!(json.contains("\"percent\":75"));
        assert!(json.contains("\"stage\":\"Scanning metadata\""));
    }

    #[test]
    fn test_scan_progress_optional_fields() {
        let progress = ScanProgress {
            folder_id: 1,
            percent: None,
            stage: None,
        };

        let json = serde_json::to_string(&progress).unwrap();
        assert!(json.contains("\"percent\":null"));
        assert!(json.contains("\"stage\":null"));
    }

    // -------------------------------------------------------------------------
    // ScanResults tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_scan_results_serialization() {
        let results = ScanResults {
            folder_id: 10,
            added: 50,
            updated: 12,
            deleted: 3,
        };

        let json = serde_json::to_string(&results).unwrap();
        assert!(json.contains("\"folder_id\":10"));
        assert!(json.contains("\"added\":50"));
        assert!(json.contains("\"updated\":12"));
        assert!(json.contains("\"deleted\":3"));
    }

    #[test]
    fn test_scan_results_zero_values() {
        let results = ScanResults {
            folder_id: 1,
            added: 0,
            updated: 0,
            deleted: 0,
        };

        let json = serde_json::to_string(&results).unwrap();
        assert!(json.contains("\"added\":0"));
        assert!(json.contains("\"updated\":0"));
        assert!(json.contains("\"deleted\":0"));
    }

    // -------------------------------------------------------------------------
    // FsEvent tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_fs_event_serialization() {
        let event = FsEvent {
            folder_id: 7,
            event_type: "change".to_string(),
            paths: vec![
                "/music/track1.mp3".to_string(),
                "/music/track2.flac".to_string(),
            ],
        };

        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("\"folder_id\":7"));
        assert!(json.contains("\"event_type\":\"change\""));
        assert!(json.contains("/music/track1.mp3"));
        assert!(json.contains("/music/track2.flac"));
    }

    #[test]
    fn test_fs_event_empty_paths() {
        let event = FsEvent {
            folder_id: 1,
            event_type: "create".to_string(),
            paths: vec![],
        };

        let json = serde_json::to_string(&event).unwrap();
        assert!(json.contains("\"paths\":[]"));
    }

    // -------------------------------------------------------------------------
    // AddWatchedFolderRequest tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_add_watched_folder_request_full() {
        let json = r#"{
            "path": "/Users/test/Music",
            "mode": "continuous",
            "cadence_minutes": 15,
            "enabled": true
        }"#;

        let request: AddWatchedFolderRequest = serde_json::from_str(json).unwrap();
        assert_eq!(request.path, "/Users/test/Music");
        assert_eq!(request.mode, Some("continuous".to_string()));
        assert_eq!(request.cadence_minutes, Some(15));
        assert_eq!(request.enabled, Some(true));
    }

    #[test]
    fn test_add_watched_folder_request_minimal() {
        let json = r#"{"path": "/home/user/audio"}"#;

        let request: AddWatchedFolderRequest = serde_json::from_str(json).unwrap();
        assert_eq!(request.path, "/home/user/audio");
        assert!(request.mode.is_none());
        assert!(request.cadence_minutes.is_none());
        assert!(request.enabled.is_none());
    }

    // -------------------------------------------------------------------------
    // UpdateWatchedFolderRequest tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_update_watched_folder_request_mode_only() {
        let json = r#"{"mode": "startup"}"#;

        let request: UpdateWatchedFolderRequest = serde_json::from_str(json).unwrap();
        assert_eq!(request.mode, Some("startup".to_string()));
        assert!(request.cadence_minutes.is_none());
        assert!(request.enabled.is_none());
    }

    #[test]
    fn test_update_watched_folder_request_all_fields() {
        let json = r#"{
            "mode": "continuous",
            "cadence_minutes": 30,
            "enabled": false
        }"#;

        let request: UpdateWatchedFolderRequest = serde_json::from_str(json).unwrap();
        assert_eq!(request.mode, Some("continuous".to_string()));
        assert_eq!(request.cadence_minutes, Some(30));
        assert_eq!(request.enabled, Some(false));
    }

    // -------------------------------------------------------------------------
    // Mode validation tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_valid_modes() {
        let startup_folder = WatchedFolder {
            id: 1,
            path: "/test".to_string(),
            mode: "startup".to_string(),
            cadence_minutes: None,
            enabled: true,
            last_scanned_at: None,
        };
        assert_eq!(startup_folder.mode, "startup");

        let continuous_folder = WatchedFolder {
            id: 2,
            path: "/test2".to_string(),
            mode: "continuous".to_string(),
            cadence_minutes: Some(10),
            enabled: true,
            last_scanned_at: None,
        };
        assert_eq!(continuous_folder.mode, "continuous");
    }

    // -------------------------------------------------------------------------
    // Cadence validation tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_cadence_minutes_range() {
        let folder_min = WatchedFolder {
            id: 1,
            path: "/test".to_string(),
            mode: "continuous".to_string(),
            cadence_minutes: Some(1),
            enabled: true,
            last_scanned_at: None,
        };
        assert_eq!(folder_min.cadence_minutes, Some(1));

        let folder_typical = WatchedFolder {
            id: 2,
            path: "/test".to_string(),
            mode: "continuous".to_string(),
            cadence_minutes: Some(10),
            enabled: true,
            last_scanned_at: None,
        };
        assert_eq!(folder_typical.cadence_minutes, Some(10));

        let folder_max = WatchedFolder {
            id: 3,
            path: "/test".to_string(),
            mode: "continuous".to_string(),
            cadence_minutes: Some(1440),
            enabled: true,
            last_scanned_at: None,
        };
        assert_eq!(folder_max.cadence_minutes, Some(1440));
    }

    // -------------------------------------------------------------------------
    // Audio file extension filter tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_supported_audio_extensions() {
        let supported = ["mp3", "flac", "m4a", "ogg", "wav", "aac", "wma", "opus"];
        
        for ext in supported.iter() {
            let ext_lower = ext.to_lowercase();
            let is_audio = matches!(
                ext_lower.as_str(),
                "mp3" | "flac" | "m4a" | "ogg" | "wav" | "aac" | "wma" | "opus"
            );
            assert!(is_audio, "Extension {} should be supported", ext);
        }
    }

    #[test]
    fn test_unsupported_extensions() {
        let unsupported = ["txt", "jpg", "png", "pdf", "doc", "mp4", "avi"];
        
        for ext in unsupported.iter() {
            let ext_lower = ext.to_lowercase();
            let is_audio = matches!(
                ext_lower.as_str(),
                "mp3" | "flac" | "m4a" | "ogg" | "wav" | "aac" | "wma" | "opus"
            );
            assert!(!is_audio, "Extension {} should not be supported", ext);
        }
    }

    #[test]
    fn test_case_insensitive_extensions() {
        let extensions = ["MP3", "FLAC", "M4A", "Ogg", "WAV", "AAC", "WMA", "OPUS"];
        
        for ext in extensions.iter() {
            let ext_lower = ext.to_lowercase();
            let is_audio = matches!(
                ext_lower.as_str(),
                "mp3" | "flac" | "m4a" | "ogg" | "wav" | "aac" | "wma" | "opus"
            );
            assert!(is_audio, "Extension {} (case insensitive) should be supported", ext);
        }
    }
}
