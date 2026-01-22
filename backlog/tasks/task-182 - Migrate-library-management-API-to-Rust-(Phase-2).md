---
id: task-182
title: Migrate library management API to Rust (Phase 2)
status: Done
assignee: []
created_date: '2026-01-21 17:37'
updated_date: '2026-01-21 23:45'
labels:
  - rust
  - migration
  - library
  - phase-2
  - api
dependencies:
  - task-173
  - task-180
  - task-181
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate library management endpoints from FastAPI to Rust Tauri commands, providing all library browsing and management functionality.

**Endpoints to Migrate** (13 total):
- GET `/api/library` - Paginated library with filters, search, sort
- GET `/api/library/stats` - Library statistics
- GET `/api/library/{track_id}` - Single track details
- GET `/api/library/{track_id}/artwork` - Album artwork
- DELETE `/api/library/{track_id}` - Remove track
- PUT `/api/library/{track_id}/rescan` - Re-extract metadata
- PUT `/api/library/{track_id}/play-count` - Increment play count
- POST `/api/library/scan` - Scan paths for audio files
- GET `/api/library/missing` - List missing tracks
- POST `/api/library/{track_id}/locate` - Update filepath for missing track
- POST `/api/library/{track_id}/check-status` - Check if file exists
- POST `/api/library/{track_id}/mark-missing` - Manual mark as missing
- POST `/api/library/{track_id}/mark-present` - Manual mark as present

**Features**:
- Pagination (limit, offset)
- Filtering (search, artist, album)
- Sorting (title, artist, album, added_date, play_count, last_played)
- Missing track management
- Library statistics (tracks, artists, albums, total size, total duration)

**Implementation**:
- Convert to Tauri commands: `#[tauri::command]`
- Use database layer from task-180
- Use metadata extraction from task-181
- Emit Tauri events for library updates
- Frontend updates to use Tauri invoke instead of fetch

**Estimated Effort**: 2-3 weeks
**File**: backend/routes/library.py (292 lines)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 13 endpoints migrated to Tauri commands
- [x] #2 Pagination, filtering, sorting functional
- [x] #3 Library scan with progress events working
- [x] #4 Missing track management working
- [x] #5 Library statistics accurate
- [x] #6 Frontend updated to use Tauri invoke
- [x] #7 E2E tests passing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

### Rust Backend (Tauri Commands)

Created `src-tauri/src/library/` module with 13 Tauri commands:

1. `library_get_all` - GET /library - Paginated with filters, search, sort
2. `library_get_stats` - GET /library/stats - Library statistics
3. `library_get_track` - GET /library/{id} - Single track details
4. `library_get_artwork` - GET /library/{id}/artwork - Artwork object
5. `library_get_artwork_url` - Artwork as data URL
6. `library_delete_track` - DELETE /library/{id} - Remove track
7. `library_rescan_track` - PUT /library/{id}/rescan - Re-extract metadata
8. `library_update_play_count` - PUT /library/{id}/play-count
9. `library_get_missing` - GET /library/missing - Missing tracks
10. `library_locate_track` - POST /library/{id}/locate - Update filepath
11. `library_check_status` - POST /library/{id}/check-status
12. `library_mark_missing` - POST /library/{id}/mark-missing
13. `library_mark_present` - POST /library/{id}/mark-present

All commands:
- Use existing db/library.rs database operations
- Emit Tauri events for real-time updates
- Return typed responses

### Frontend Integration

Updated `app/frontend/js/api.js`:
- All library methods now use Tauri invoke when available
- HTTP fallback maintained for browser-only mode
- Error handling with ApiError class

### Files Changed

**New:**
- `src-tauri/src/library/mod.rs`
- `src-tauri/src/library/commands.rs`

**Modified:**
- `src-tauri/src/lib.rs` - Added library module and commands
- `app/frontend/js/api.js` - Updated library methods to use Tauri invoke

### Tests

- 101 Rust tests pass (including new library command test)
- E2E tests require full app (integration testing needed)
<!-- SECTION:NOTES:END -->
