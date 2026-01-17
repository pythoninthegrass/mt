use std::path::Path;
use tauri::command;

#[command]
pub async fn show_in_folder(path: String) -> Result<(), String> {
    let file_path = Path::new(&path);

    // Verify the file exists
    if !file_path.exists() {
        return Err(format!("File not found: {}", path));
    }

    #[cfg(target_os = "macos")]
    {
        use std::process::Command;
        Command::new("open")
            .arg("-R")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open Finder: {}", e))?;
    }

    #[cfg(target_os = "windows")]
    {
        use std::process::Command;
        Command::new("explorer")
            .arg("/select,")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open Explorer: {}", e))?;
    }

    #[cfg(target_os = "linux")]
    {
        use std::process::Command;

        // Get the parent directory
        let parent = file_path.parent()
            .ok_or_else(|| "Failed to get parent directory".to_string())?;

        // Try common Linux file managers in order of preference
        let file_managers = vec![
            ("xdg-open", vec![parent.to_str().unwrap()]),
            ("nautilus", vec![parent.to_str().unwrap()]),
            ("dolphin", vec!["--select", file_path.to_str().unwrap()]),
            ("thunar", vec![parent.to_str().unwrap()]),
        ];

        let mut success = false;
        for (manager, args) in file_managers {
            if let Ok(mut child) = Command::new(manager).args(&args).spawn() {
                // Don't wait for the file manager to exit
                let _ = child.wait();
                success = true;
                break;
            }
        }

        if !success {
            return Err("No supported file manager found".to_string());
        }
    }

    Ok(())
}
