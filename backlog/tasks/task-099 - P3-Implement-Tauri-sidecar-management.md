---
id: task-099
title: 'P3: Implement Tauri sidecar management'
status: Done
assignee: []
created_date: '2026-01-12 04:07'
updated_date: '2026-01-13 08:03'
labels:
  - rust
  - tauri
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-098
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Rust code to manage the Python sidecar lifecycle.

**Responsibilities:**
1. Find available port
2. Spawn PEX sidecar with `MT_API_PORT` environment variable
3. Poll health endpoint for readiness
4. Expose backend URL to frontend
5. Monitor sidecar health
6. Clean shutdown on app exit

**Implementation:**
```rust
// src-tauri/src/sidecar.rs
use std::time::Duration;
use tauri::Manager;

pub struct SidecarManager {
    port: u16,
    child: Option<tauri::process::CommandChild>,
}

impl SidecarManager {
    pub async fn start(app: &tauri::AppHandle) -> Result<Self, Error> {
        // 1. Find available port
        let port = find_available_port()?;
        
        // 2. Spawn sidecar with MT_API_PORT env var
        let child = app.shell()
            .sidecar("main")?
            .env("MT_API_PORT", port.to_string())
            .spawn()?;
        
        // 3. Poll health endpoint for readiness
        let health_url = format!("http://127.0.0.1:{}/api/health", port);
        for _ in 0..30 {
            if reqwest::get(&health_url).await.is_ok() {
                return Ok(Self { port, child: Some(child) });
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
        
        Err(Error::SidecarTimeout)
    }
    
    pub fn get_url(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }
}
```

**Tauri command:**
```rust
#[tauri::command]
fn get_backend_url(state: tauri::State<SidecarManager>) -> String {
    state.get_url()
}
```

**Key Changes from Original Design:**
- Use `MT_API_PORT` env var instead of `--port` CLI argument
- Poll `GET /api/health` endpoint instead of parsing stdout for "SERVER_READY"
- Health endpoint returns `{"status": "ok"}` when server is ready
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Sidecar spawns on app startup with `MT_API_PORT` env var
- [x] #2 Port allocation avoids conflicts (find available port)
- [x] #3 Health endpoint polling detects readiness (`GET /api/health`)
- [x] #4 Backend URL accessible from frontend via Tauri command
- [x] #5 Sidecar terminates on app close (graceful shutdown)
- [x] #6 Handles sidecar crash gracefully (error state, retry logic)
<!-- AC:END -->
