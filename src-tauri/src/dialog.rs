use tauri_plugin_dialog::DialogExt;

/// Open a file dialog to select audio files and/or folders
#[tauri::command]
pub async fn open_file_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let dialog = app.dialog().file();
    
    // Configure dialog for audio files
    let result = dialog
        .add_filter("Audio Files", &["mp3", "m4a", "flac", "ogg", "wav", "aac", "wma", "opus"])
        .add_filter("All Files", &["*"])
        .set_title("Select audio files and/or folders to add to your library")
        .set_can_create_directories(false)
        .blocking_pick_files();
    
    match result {
        Some(paths) => {
            let path_strings: Vec<String> = paths
                .iter()
                .filter_map(|p| p.as_path().map(|path| path.to_string_lossy().to_string()))
                .collect();
            Ok(path_strings)
        }
        None => Ok(vec![]), // User cancelled
    }
}

/// Open a folder dialog to select directories
#[tauri::command]
pub async fn open_folder_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let dialog = app.dialog().file();
    
    let result = dialog
        .set_title("Select folders to add to your library")
        .set_can_create_directories(false)
        .blocking_pick_folders();
    
    match result {
        Some(paths) => {
            let path_strings: Vec<String> = paths
                .iter()
                .filter_map(|p| p.as_path().map(|path| path.to_string_lossy().to_string()))
                .collect();
            Ok(path_strings)
        }
        None => Ok(vec![]), // User cancelled
    }
}

/// Open a combined dialog that allows selecting both files and folders
/// This mimics the macOS Finder behavior shown in the reference image
#[tauri::command]
pub async fn open_add_music_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let dialog = app.dialog().file();
    
    // Use folder picker which on macOS allows selecting both files and folders
    // when configured appropriately
    let result = dialog
        .add_filter("Audio Files", &["mp3", "m4a", "flac", "ogg", "wav", "aac", "wma", "opus"])
        .set_title("Select audio files and/or folders to add to your library")
        .set_can_create_directories(false)
        .blocking_pick_folders();
    
    match result {
        Some(paths) => {
            let path_strings: Vec<String> = paths
                .iter()
                .filter_map(|p| p.as_path().map(|path| path.to_string_lossy().to_string()))
                .collect();
            Ok(path_strings)
        }
        None => Ok(vec![]), // User cancelled
    }
}
