pub mod audio;
pub mod commands;
pub mod dialog;
pub mod sidecar;

use commands::{
    audio_get_status, audio_get_volume, audio_load, audio_pause, audio_play, audio_seek,
    audio_set_volume, audio_stop, AudioState,
};
use dialog::{open_add_music_dialog, open_file_dialog, open_folder_dialog};
use sidecar::{check_backend_health, get_backend_port, get_backend_url, SidecarManager};
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    #[cfg(feature = "devtools")]
    {
        builder = builder.plugin(tauri_plugin_devtools::init());
    }

    builder
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            // Audio commands
            audio_load,
            audio_play,
            audio_pause,
            audio_stop,
            audio_seek,
            audio_set_volume,
            audio_get_volume,
            audio_get_status,
            // Sidecar commands
            get_backend_url,
            get_backend_port,
            check_backend_health,
            // Dialog commands
            open_file_dialog,
            open_folder_dialog,
            open_add_music_dialog,
        ])
        .setup(|app| {
            // Start the Python backend sidecar
            let sidecar = SidecarManager::start(app.handle())
                .expect("Failed to start backend sidecar");
            println!("Backend URL: {}", sidecar.get_url());
            app.manage(sidecar);

            // Initialize audio engine
            app.manage(AudioState::new(app.handle().clone()));
            println!("Audio engine initialized");

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
