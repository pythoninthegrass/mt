---
id: task-185
title: Migrate playlists API to Rust (Phase 3)
status: Done
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-24 22:28'
labels:
  - rust
  - migration
  - playlists
  - phase-3
  - api
dependencies:
  - task-173
  - task-180
priority: medium
ordinal: 50382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate playlist management endpoints from FastAPI to Rust Tauri commands, providing full playlist CRUD functionality.

**Endpoints to Migrate** (9 total):
- GET `/api/playlists` - List all playlists with track counts
- POST `/api/playlists` - Create playlist
- GET `/api/playlists/{id}` - Get playlist with tracks
- PUT `/api/playlists/{id}` - Update playlist name
- DELETE `/api/playlists/{id}` - Delete playlist
- POST `/api/playlists/{id}/tracks` - Add tracks to playlist
- DELETE `/api/playlists/{id}/tracks/{position}` - Remove track from playlist
- POST `/api/playlists/{id}/reorder` - Reorder tracks within playlist
- POST `/api/playlists/reorder` - Reorder playlists in sidebar

**Features**:
- Playlist CRUD operations
- Track management within playlists
- Position-based ordering
- Unique playlist names validation
- Track count aggregation
- Sidebar ordering

**Database Operations**:
- playlists table (id, name, position, created_at)
- playlist_items table (id, playlist_id, track_id, position)
- Foreign key constraints (CASCADE delete)
- Unique constraints

**Implementation**:
- Convert to Tauri commands
- Use database layer from task-180
- Emit Tauri events for playlist updates
- Handle duplicate track/name errors gracefully
- Position reindexing after removals

**Estimated Effort**: 1-2 weeks
**File**: backend/routes/playlists.py (150 lines)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 9 endpoints migrated to Tauri commands
- [x] #2 Playlist CRUD operations functional
- [x] #3 Track management working
- [x] #4 Unique name validation working
- [x] #5 Position ordering functional
- [x] #6 Sidebar reordering working
- [ ] #7 Frontend updated and E2E tests passing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Migrated all playlist management operations from Python FastAPI to Rust Tauri commands.

### Created Files
- `src-tauri/src/commands/playlists.rs` - Tauri commands for all 10 playlist operations

### Modified Files
- `src-tauri/src/commands/mod.rs` - Export playlist commands
- `src-tauri/src/lib.rs` - Register playlist commands in invoke_handler
- `app/frontend/js/api.js` - Update playlists API to use Tauri commands with HTTP fallback

### Tauri Commands Implemented
1. `playlist_list` - Get all playlists with track counts
2. `playlist_create` - Create new playlist
3. `playlist_get` - Get playlist with tracks
4. `playlist_update` - Update playlist name
5. `playlist_delete` - Delete playlist
6. `playlist_add_tracks` - Add tracks to playlist
7. `playlist_remove_track` - Remove track from playlist
8. `playlist_reorder_tracks` - Reorder tracks within playlist
9. `playlists_reorder` - Reorder playlists in sidebar
10. `playlist_generate_name` - Generate unique playlist name

### Already Existing
- `db/playlists.rs` - Database operations (already implemented)
- `events.rs` - PlaylistsUpdatedEvent and emit_playlists_updated (already implemented)

### Technical Details
- All commands emit Tauri events via EventEmitter trait
- Frontend API maintains HTTP fallback for non-Tauri environments
- All 109 Rust tests pass
<!-- SECTION:NOTES:END -->
