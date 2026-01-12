---
id: task-099
title: 'P3: Implement Tauri sidecar management'
status: To Do
assignee: []
created_date: '2026-01-12 04:07'
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
2. Spawn PEX sidecar with port argument
3. Wait for readiness signal
4. Expose backend URL to frontend
5. Monitor sidecar health
6. Clean shutdown on app exit

**Implementation:**
```rust
// src-tauri/src/sidecar.rs
use tauri::api::process::{Command, CommandEvent};

pub struct SidecarManager {
    port: u16,
    child: Option<CommandChild>,
}

impl SidecarManager {
    pub fn start(app: &AppHandle) -> Result<Self, Error> {
        // 1. Find available port
        let port = find_available_port()?;
        
        // 2. Spawn sidecar
        let (mut rx, child) = app.shell()
            .sidecar("mt-backend")?
            .args(&["--port", &port.to_string()])
            .spawn()?;
        
        // 3. Wait for readiness
        wait_for_ready(&mut rx)?;
        
        Ok(Self { port, child: Some(child) })
    }
    
    pub fn get_url(&self) -> String {
        format!("http://127.0.0.1:{}", self.port)
    }
}
```

**Tauri command:**
```rust
#[tauri::command]
fn get_backend_url(state: State<SidecarManager>) -> String {
    state.get_url()
}
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sidecar spawns on app startup
- [ ] #2 Port allocation avoids conflicts
- [ ] #3 Readiness detection works reliably
- [ ] #4 Backend URL accessible from frontend
- [ ] #5 Sidecar terminates on app close
- [ ] #6 Handles sidecar crash gracefully
<!-- AC:END -->
