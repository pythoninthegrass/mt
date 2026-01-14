use std::net::TcpListener;
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;
use thiserror::Error;

/// Default port range for sidecar
const PORT_RANGE_START: u16 = 8765;
const PORT_RANGE_END: u16 = 8865;

/// Health check configuration
const HEALTH_CHECK_ATTEMPTS: u32 = 30;
const HEALTH_CHECK_INTERVAL_MS: u64 = 100;

#[derive(Error, Debug)]
pub enum SidecarError {
    #[error("No available port in range {0}-{1}")]
    NoAvailablePort(u16, u16),
    #[error("Failed to spawn sidecar: {0}")]
    SpawnFailed(String),
    #[error("Sidecar health check timed out after {0} attempts")]
    HealthCheckTimeout(u32),
    #[error("HTTP request failed: {0}")]
    HttpError(#[from] reqwest::Error),
}

/// Manages the Python backend sidecar lifecycle
pub struct SidecarManager {
    port: u16,
    child: Mutex<Option<CommandChild>>,
    base_url: String,
}

impl SidecarManager {
    /// Start the sidecar with dynamic port allocation
    pub fn start(app: &tauri::AppHandle) -> Result<Self, SidecarError> {
        // 1. Find available port
        let port = find_available_port(PORT_RANGE_START, PORT_RANGE_END)?;
        println!("Sidecar: Found available port {}", port);

        // 2. Spawn sidecar with environment variables
        let shell = app.shell();
        let sidecar = shell
            .sidecar("main")
            .map_err(|e| SidecarError::SpawnFailed(e.to_string()))?;

        // Get database path - use app data dir for consistency
        let db_path = app
            .path()
            .app_data_dir()
            .map(|p| p.join("mt.db"))
            .unwrap_or_else(|_| std::path::PathBuf::from("mt.db"));
        
        // Ensure parent directory exists
        if let Some(parent) = db_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }

        let sidecar_with_env = sidecar
            .env("MT_API_PORT", port.to_string())
            .env("MT_DB_PATH", db_path.to_string_lossy().to_string());

        let (_rx, child) = sidecar_with_env
            .spawn()
            .map_err(|e| SidecarError::SpawnFailed(e.to_string()))?;

        println!("Sidecar: Process spawned, waiting for health check...");

        let base_url = format!("http://127.0.0.1:{}", port);

        // 3. Poll health endpoint for readiness
        let health_url = format!("{}/api/health", base_url);
        let client = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(2))
            .build()?;

        for attempt in 1..=HEALTH_CHECK_ATTEMPTS {
            match client.get(&health_url).send() {
                Ok(response) if response.status().is_success() => {
                    println!(
                        "Sidecar: Health check passed on attempt {} (port {})",
                        attempt, port
                    );
                    return Ok(Self {
                        port,
                        child: Mutex::new(Some(child)),
                        base_url,
                    });
                }
                Ok(response) => {
                    println!(
                        "Sidecar: Health check attempt {} returned status {}",
                        attempt,
                        response.status()
                    );
                }
                Err(_) => {
                    // Server not ready yet, continue polling
                }
            }
            std::thread::sleep(Duration::from_millis(HEALTH_CHECK_INTERVAL_MS));
        }

        // Health check failed, kill the child process
        let _ = child.kill();
        Err(SidecarError::HealthCheckTimeout(HEALTH_CHECK_ATTEMPTS))
    }

    /// Get the backend base URL
    pub fn get_url(&self) -> String {
        self.base_url.clone()
    }

    /// Get the port the sidecar is running on
    pub fn get_port(&self) -> u16 {
        self.port
    }

    /// Check if the sidecar is healthy
    pub fn is_healthy(&self) -> bool {
        let health_url = format!("{}/api/health", self.base_url);
        let client = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(2))
            .build();

        match client {
            Ok(client) => client
                .get(&health_url)
                .send()
                .map(|r| r.status().is_success())
                .unwrap_or(false),
            Err(_) => false,
        }
    }

    /// Gracefully shutdown the sidecar
    pub fn shutdown(&self) {
        let mut guard = self.child.lock().unwrap();
        if let Some(child) = guard.take() {
            println!("Sidecar: Shutting down...");
            let _ = child.kill();
            println!("Sidecar: Stopped");
        }
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        self.shutdown();
    }
}

/// Find an available port in the given range
fn find_available_port(start: u16, end: u16) -> Result<u16, SidecarError> {
    for port in start..=end {
        if is_port_available(port) {
            return Ok(port);
        }
    }
    Err(SidecarError::NoAvailablePort(start, end))
}

/// Check if a port is available by attempting to bind to it
fn is_port_available(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

// Tauri commands for frontend access

#[tauri::command]
pub fn get_backend_url(state: tauri::State<SidecarManager>) -> String {
    state.get_url()
}

#[tauri::command]
pub fn get_backend_port(state: tauri::State<SidecarManager>) -> u16 {
    state.get_port()
}

#[tauri::command]
pub fn check_backend_health(state: tauri::State<SidecarManager>) -> bool {
    state.is_healthy()
}
