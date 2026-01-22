---
id: task-188
title: Migrate watched folders API to Rust (Phase 3)
status: In Progress
assignee: []
created_date: '2026-01-21 17:39'
updated_date: '2026-01-21 18:32'
labels:
  - rust
  - migration
  - watched-folders
  - phase-3
  - api
  - filesystem
dependencies:
  - task-173
  - task-180
  - task-181
  - task-182
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate watched folders management from FastAPI to Rust with real-time filesystem monitoring using the notify crate.

**Endpoints to Migrate** (5 total):
- GET `/api/watched-folders` - List all watched folders
- POST `/api/watched-folders` - Add watched folder
- PUT `/api/watched-folders/{id}` - Update watched folder settings
- DELETE `/api/watched-folders/{id}` - Remove watched folder
- GET `/api/watched-folders/{id}` - Get single watched folder

**Features**:
- Watched folders CRUD operations
- Scan modes: "startup" (scan on launch), "background" (periodic), "manual"
- Cadence: minutes between scans (for background mode)
- Enable/disable state
- Last scanned timestamp tracking

**Database Operations**:
- watched_folders table (id, path, mode, cadence_minutes, enabled, last_scanned_at, created_at, updated_at)
- Path uniqueness validation

**Real-time Monitoring** (NEW):
- Use `notify` crate for filesystem watching
- Listen for file creation/modification/deletion events
- Automatic library updates when files change
- More efficient than periodic polling

**Implementation**:
- Convert to Tauri commands
- Use database layer from task-180
- Integrate `notify` crate for real-time file system events
- Use `tokio::time` for periodic background scanning
- Spawn async tasks for each watched folder
- Emit progress events for scans

**Rust Crates**:
- `notify` - Cross-platform filesystem watcher
- `tokio::time` - Periodic scanning timers
- `tokio::spawn` - Background task management

**Estimated Effort**: 1-2 weeks
**File**: backend/routes/watched_folders.py (118 lines)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 5 endpoints migrated to Tauri commands
- [ ] #2 CRUD operations functional
- [ ] #3 Real-time filesystem monitoring working (notify)
- [ ] #4 Periodic scanning working (background mode)
- [ ] #5 Startup scan working
- [ ] #6 Manual scan working
- [ ] #7 Path validation functional
- [ ] #8 Frontend updated and E2E tests passing
<!-- AC:END -->
