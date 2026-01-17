pub mod audio;
pub mod commands;
pub mod dialog;
pub mod media_keys;
pub mod metadata;
pub mod sidecar;

use commands::{
    audio_get_status, audio_get_volume, audio_load, audio_pause, audio_play, audio_seek,
    audio_set_volume, audio_stop, AudioState,
};
use dialog::{open_add_music_dialog, open_file_dialog, open_folder_dialog};
use media_keys::{MediaKeyManager, NowPlayingInfo};
use metadata::{get_track_metadata, save_track_metadata};
use sidecar::{check_backend_health, get_backend_port, get_backend_url, SidecarManager};
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
        ])
        .setup(|app| {
            let sidecar = SidecarManager::start(app.handle())
                .expect("Failed to start backend sidecar");
            println!("Backend URL: {}", sidecar.get_url());
            app.manage(sidecar);

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
