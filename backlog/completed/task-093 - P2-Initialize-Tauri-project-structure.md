---
id: task-093
title: 'P2: Initialize Tauri project structure'
status: Done
assignee: []
created_date: '2026-01-12 04:06'
updated_date: '2026-01-24 22:28'
labels:
  - infrastructure
  - rust
  - phase-2
milestone: Tauri Migration
dependencies: []
priority: high
ordinal: 95382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Set up the Tauri project skeleton in the migration worktree.

**Steps:**
1. Install Tauri CLI: `cargo install tauri-cli`
2. Initialize Tauri: `cargo tauri init`
3. Configure project structure:
   ```
   mt/
   ├── src/                    # Frontend (AlpineJS + Basecoat)
   ├── src-tauri/              # Rust backend
   │   ├── src/
   │   │   ├── main.rs         # Tauri app entry
   │   │   ├── audio/          # Playback engine (symphonia + rodio)
   │   │   └── commands/       # Tauri invoke handlers
   │   ├── binaries/           # PEX sidecar (later)
   │   └── Cargo.toml
   ├── backend/                # Python sidecar source (later)
   └── package.json
   ```
4. Configure tauri.conf.json for development
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tauri CLI installed
- [x] #2 Project structure created
- [x] #3 tauri.conf.json configured
- [x] #4 `cargo tauri dev` launches empty window
<!-- AC:END -->
