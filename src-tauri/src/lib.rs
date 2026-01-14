pub mod audio;
pub mod commands;
pub mod dialog;
pub mod media_keys;
pub mod sidecar;

use commands::{
    audio_get_status, audio_get_volume, audio_load, audio_pause, audio_play, audio_seek,
    audio_set_volume, audio_stop, AudioState,
};
use dialog::{open_add_music_dialog, open_file_dialog, open_folder_dialog};
use media_keys::{MediaKeyManager, NowPlayingInfo};
use sidecar::{check_backend_health, get_backend_port, get_backend_url, SidecarManager};
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
