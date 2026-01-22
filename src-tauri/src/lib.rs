pub mod audio;
pub mod commands;
pub mod db;
pub mod dialog;
pub mod events;
pub mod lastfm;
pub mod library;
pub mod media_keys;
pub mod metadata;
pub mod scanner;
pub mod sidecar;
pub mod watcher;

use commands::{
    audio_get_status, audio_get_volume, audio_load, audio_pause, audio_play, audio_seek,
    audio_set_volume, audio_stop, favorites_add, favorites_check, favorites_get,
    favorites_get_recently_added, favorites_get_recently_played, favorites_get_top25,
    favorites_remove, lastfm_auth_callback, lastfm_disconnect, lastfm_get_auth_url,
    lastfm_get_settings, lastfm_update_settings, playlist_add_tracks,
    playlist_create, playlist_delete, playlist_generate_name, playlist_get, playlist_list,
    playlist_remove_track, playlist_reorder_tracks, playlist_update, playlists_reorder,
    queue_add, queue_add_files, queue_clear, queue_get, queue_remove, queue_reorder,
    queue_shuffle, settings_get, settings_get_all, settings_reset, settings_set,
    settings_update, AudioState,
};
use dialog::{open_add_music_dialog, open_file_dialog, open_folder_dialog};
use media_keys::{MediaKeyManager, NowPlayingInfo};
use metadata::{get_track_metadata, save_track_metadata};
use sidecar::{check_backend_health, get_backend_port, get_backend_url, SidecarManager};
use scanner::commands::{
    extract_file_metadata, get_track_artwork, get_track_artwork_url, scan_paths_metadata,
    scan_paths_to_library,
};
use library::commands::{
    library_check_status, library_delete_track, library_get_all, library_get_artwork,
    library_get_artwork_url, library_get_missing, library_get_stats, library_get_track,
    library_locate_track, library_mark_missing, library_mark_present, library_reconcile_scan,
    library_rescan_track, library_update_play_count,
};
use watcher::{
    watched_folders_add, watched_folders_get, watched_folders_list, watched_folders_remove,
    watched_folders_rescan, watched_folders_status, watched_folders_update, WatcherManager,
};
use serde::Serialize;
use std::fs::File;
use std::io::Write;
use std::time::Duration;
use tauri::{Emitter, Manager, State};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut};

#[tauri::command]
fn media_set_metadata(
    title: Option<String>,
    artist: Option<String>,
    album: Option<String>,
    duration_ms: Option<u64>,
    cover_url: Option<String>,
    state: State<MediaKeyManager>,
) -> Result<(), String> {
    state.set_metadata(NowPlayingInfo {
        title,
        artist,
        album,
        duration: duration_ms.map(Duration::from_millis),
        cover_url,
    })
}

#[tauri::command]
fn media_set_playing(progress_ms: Option<u64>, state: State<MediaKeyManager>) -> Result<(), String> {
    state.set_playing(progress_ms.map(Duration::from_millis))
}

#[tauri::command]
fn media_set_paused(progress_ms: Option<u64>, state: State<MediaKeyManager>) -> Result<(), String> {
    state.set_paused(progress_ms.map(Duration::from_millis))
}

#[tauri::command]
fn media_set_stopped(state: State<MediaKeyManager>) -> Result<(), String> {
    state.set_stopped()
}

#[derive(Serialize)]
struct AppInfo {
    version: String,
    build: String,
    platform: String,
}

#[tauri::command]
fn app_get_info() -> AppInfo {
    let version = env!("CARGO_PKG_VERSION").to_string();
    let build = option_env!("MT_BUILD_ID")
        .unwrap_or("dev")
        .to_string();
    let platform = format!(
        "{} {}",
        std::env::consts::OS,
        std::env::consts::ARCH
    );
    
    AppInfo {
        version,
        build,
        platform,
    }
}

#[tauri::command]
fn export_diagnostics(path: String) -> Result<(), String> {
    let mut content = String::new();
    
    content.push_str("=== mt Diagnostics ===\n\n");
    
    let info = app_get_info();
    content.push_str(&format!("Version: {}\n", info.version));
    content.push_str(&format!("Build: {}\n", info.build));
    content.push_str(&format!("Platform: {}\n", info.platform));
    content.push_str(&format!("Timestamp: {}\n", chrono::Utc::now().to_rfc3339()));
    
    content.push_str("\n=== Environment ===\n\n");
    content.push_str(&format!("Rust version: {}\n", env!("CARGO_PKG_RUST_VERSION")));
    
    if let Ok(cwd) = std::env::current_dir() {
        content.push_str(&format!("Working directory: {}\n", cwd.display()));
    }
    
    let mut file = File::create(&path).map_err(|e| format!("Failed to create file: {}", e))?;
    file.write_all(content.as_bytes())
        .map_err(|e| format!("Failed to write file: {}", e))?;
    
    Ok(())
}

fn setup_global_shortcuts(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let app_handle = app.handle().clone();
    
    let play_pause = Shortcut::new(Some(Modifiers::empty()), Code::MediaPlayPause);
    let next_track = Shortcut::new(Some(Modifiers::empty()), Code::MediaTrackNext);
    let prev_track = Shortcut::new(Some(Modifiers::empty()), Code::MediaTrackPrevious);
    let stop = Shortcut::new(Some(Modifiers::empty()), Code::MediaStop);

    app.handle().plugin(
        tauri_plugin_global_shortcut::Builder::new()
            .with_handler(move |_app, shortcut, event| {
                if event.state() != tauri_plugin_global_shortcut::ShortcutState::Pressed {
                    return;
                }
                
                let event_name = if shortcut == &play_pause {
                    println!("Media key: Play/Pause");
                    Some("mediakey://toggle")
                } else if shortcut == &next_track {
                    println!("Media key: Next");
                    Some("mediakey://next")
                } else if shortcut == &prev_track {
                    println!("Media key: Previous");
                    Some("mediakey://previous")
                } else if shortcut == &stop {
                    println!("Media key: Stop");
                    Some("mediakey://stop")
                } else {
                    None
                };

                if let Some(name) = event_name {
                    let _ = app_handle.emit(name, ());
                }
            })
            .build(),
    )?;

    let global_shortcut = app.global_shortcut();
    
    if let Err(e) = global_shortcut.register(play_pause) {
        eprintln!("Failed to register MediaPlayPause: {}", e);
    }
    if let Err(e) = global_shortcut.register(next_track) {
        eprintln!("Failed to register MediaTrackNext: {}", e);
    }
    if let Err(e) = global_shortcut.register(prev_track) {
        eprintln!("Failed to register MediaTrackPrevious: {}", e);
    }
    if let Err(e) = global_shortcut.register(stop) {
        eprintln!("Failed to register MediaStop: {}", e);
    }

    println!("Global media shortcuts registered");
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(feature = "devtools")]
    {
        builder = builder.plugin(tauri_plugin_devtools::init());
    }

    builder
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            audio_load,
            audio_play,
            audio_pause,
            audio_stop,
            audio_seek,
            audio_set_volume,
            audio_get_volume,
            audio_get_status,
            get_backend_url,
            get_backend_port,
            check_backend_health,
            open_file_dialog,
            open_folder_dialog,
            open_add_music_dialog,
            media_set_metadata,
            media_set_playing,
            media_set_paused,
            media_set_stopped,
            app_get_info,
            export_diagnostics,
            get_track_metadata,
            save_track_metadata,
            watched_folders_list,
            watched_folders_get,
            watched_folders_add,
            watched_folders_update,
            watched_folders_remove,
            watched_folders_rescan,
            watched_folders_status,
            scan_paths_to_library,
            scan_paths_metadata,
            extract_file_metadata,
            get_track_artwork,
            get_track_artwork_url,
            library_get_all,
            library_get_stats,
            library_get_track,
            library_get_artwork,
            library_get_artwork_url,
            library_delete_track,
            library_rescan_track,
            library_update_play_count,
            library_get_missing,
            library_locate_track,
            library_check_status,
            library_mark_missing,
            library_mark_present,
            library_reconcile_scan,
            queue_get,
            queue_add,
            queue_add_files,
            queue_remove,
            queue_clear,
            queue_reorder,
            queue_shuffle,
            playlist_list,
            playlist_create,
            playlist_get,
            playlist_update,
            playlist_delete,
            playlist_add_tracks,
            playlist_remove_track,
            playlist_reorder_tracks,
            playlists_reorder,
            playlist_generate_name,
            favorites_get,
            favorites_check,
            favorites_add,
            favorites_remove,
            favorites_get_top25,
            favorites_get_recently_played,
            favorites_get_recently_added,
            lastfm_get_settings,
            lastfm_update_settings,
            lastfm_get_auth_url,
            lastfm_auth_callback,
            lastfm_disconnect,
            settings_get_all,
            settings_get,
            settings_set,
            settings_update,
            settings_reset,
        ])
        .setup(|app| {
            // Initialize database
            let db_path = app.path().app_data_dir()
                .expect("Failed to get app data directory")
                .join("mt.db");

            // Ensure parent directory exists
            if let Some(parent) = db_path.parent() {
                std::fs::create_dir_all(parent).ok();
            }

            let database = db::Database::new(&db_path)
                .expect("Failed to initialize database");
            let database_for_watcher = database.clone();
            app.manage(database);
            println!("Database initialized at: {}", db_path.display());

            let sidecar = SidecarManager::start(app.handle())
                .expect("Failed to start backend sidecar");
            let backend_url = sidecar.get_url().to_string();
            println!("Backend URL: {}", backend_url);
            app.manage(sidecar);

            // Pass database clone to watcher manager (migrated from Python backend)
            let watcher = WatcherManager::new(app.handle().clone(), database_for_watcher);
            app.manage(watcher);
            println!("Watcher manager initialized (using native Rust)");

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                tokio::time::sleep(Duration::from_secs(2)).await;
                if let Some(watcher) = app_handle.try_state::<WatcherManager>() {
                    if let Err(e) = watcher.start().await {
                        eprintln!("Failed to start watched folder watchers: {}", e);
                    } else {
                        println!("Watched folder watchers started ({} active)", watcher.active_watcher_count());
                    }
                }
            });

            app.manage(AudioState::new(app.handle().clone()));
            println!("Audio engine initialized");

            match MediaKeyManager::new(app.handle().clone()) {
                Ok(media_keys) => {
                    app.manage(media_keys);
                    println!("Media keys (Now Playing) initialized");
                }
                Err(e) => {
                    eprintln!("Failed to initialize media keys: {}", e);
                }
            }

            if let Err(e) = setup_global_shortcuts(app) {
                eprintln!("Failed to setup global shortcuts: {}", e);
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app = window.app_handle();
                // Graceful sidecar shutdown handled by SidecarManager Drop impl
                if let Some(sidecar) = app.try_state::<SidecarManager>() {
                    sidecar.shutdown();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
