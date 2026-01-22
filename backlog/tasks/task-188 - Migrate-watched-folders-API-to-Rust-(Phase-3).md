---
id: task-188
title: Migrate watched folders API to Rust (Phase 3)
status: Done
assignee: []
created_date: '2026-01-21 17:39'
updated_date: '2026-01-22 18:37'
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
ordinal: 3656.25
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
- [x] #1 All 5 endpoints migrated to Tauri commands
- [x] #2 CRUD operations functional
- [x] #3 Real-time filesystem monitoring working (notify)
- [x] #4 Periodic scanning working (background mode)
- [x] #5 Startup scan working
- [x] #6 Manual scan working
- [x] #7 Path validation functional
- [x] #8 Frontend updated and E2E tests passing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Migration Complete (2026-01-22)

Migrated watched folders API from Python FastAPI to native Rust:

### Changes Made

1. **watcher.rs** - Refactored `WatcherManager` to use `Database` directly instead of HTTP calls to Python backend:
   - Removed `backend_url` field, replaced with `db: Database`
   - All CRUD commands now use `db::watched` module functions directly
   - Rescan uses native Rust scanner (`scan_2phase`) instead of HTTP calls
   - Preserved filesystem watcher functionality (notify crate)
   - Preserved all event emissions for frontend

2. **lib.rs** - Updated initialization:
   - Pass `Database` clone to `WatcherManager` instead of `backend_url`

### Commands Migrated
- `watched_folders_list` - List all watched folders
- `watched_folders_get` - Get single watched folder by ID
- `watched_folders_add` - Add new watched folder with path validation
- `watched_folders_update` - Update folder settings (mode, cadence, enabled)
- `watched_folders_remove` - Remove watched folder
- `watched_folders_rescan` - Trigger manual rescan using Rust scanner
- `watched_folders_status` - Get active watcher count

### Features Working
- CRUD operations via direct database access
- Real-time filesystem monitoring (notify crate)
- Periodic scanning (continuous mode)
- Startup scan (startup mode)
- Manual scan via rescan command
- Path validation (directory exists check)
- Progress events emission during scans
- Library update events on changes

### Tests
- All 20 watcher tests pass
- All 6 db::watched tests pass
- All 113 Rust tests pass

### E2E Tests
- All 15 watched folders E2E tests pass (9.5s)
- Tests cover: UI display, folder list, mode selector, cadence input, rescan button, remove button, add button, path truncation, remove action, mode update, loading state, rescan trigger, scanning indicator
<!-- SECTION:NOTES:END -->
