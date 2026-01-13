use tauri_plugin_dialog::DialogExt;

#[tauri::command]
pub async fn open_file_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let dialog = app.dialog().file();
    
    let result = dialog
        .add_filter("Audio Files", &["mp3", "m4a", "flac", "ogg", "wav", "aac", "wma", "opus"])
        .add_filter("All Files", &["*"])
        .set_title("Select audio files to add to your library")
        .blocking_pick_files();
    
    match result {
        Some(paths) => {
            let path_strings: Vec<String> = paths
                .iter()
                .filter_map(|p| p.as_path().map(|path| path.to_string_lossy().to_string()))
                .collect();
            println!("File dialog selected {} files: {:?}", path_strings.len(), path_strings);
            Ok(path_strings)
        }
        None => {
            println!("File dialog cancelled");
            Ok(vec![])
        }
    }
}

#[tauri::command]
pub async fn open_folder_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let dialog = app.dialog().file();
    
    let result = dialog
        .set_title("Select folders to add to your library")
        .blocking_pick_folders();
    
    match result {
        Some(paths) => {
            let path_strings: Vec<String> = paths
                .iter()
                .filter_map(|p| p.as_path().map(|path| path.to_string_lossy().to_string()))
                .collect();
            println!("Folder dialog selected {} folders: {:?}", path_strings.len(), path_strings);
            Ok(path_strings)
        }
        None => {
            println!("Folder dialog cancelled");
            Ok(vec![])
        }
    }
}

#[tauri::command]
pub async fn open_add_music_dialog(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let dialog = app.dialog().file();
    
    let result = dialog
        .set_title("Select audio files and/or folders to add to your library")
        .blocking_pick_folders();
    
    match result {
        Some(paths) => {
            let path_strings: Vec<String> = paths
                .iter()
                .filter_map(|p| p.as_path().map(|path| path.to_string_lossy().to_string()))
                .collect();
            println!("Add music dialog selected {} paths: {:?}", path_strings.len(), path_strings);
            Ok(path_strings)
        }
        None => {
            println!("Add music dialog cancelled");
            Ok(vec![])
        }
    }
}
