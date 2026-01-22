---
id: task-185
title: Migrate playlists API to Rust (Phase 3)
status: In Progress
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-21 18:32'
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
- [ ] #1 All 9 endpoints migrated to Tauri commands
- [ ] #2 Playlist CRUD operations functional
- [ ] #3 Track management working
- [ ] #4 Unique name validation working
- [ ] #5 Position ordering functional
- [ ] #6 Sidebar reordering working
- [ ] #7 Frontend updated and E2E tests passing
<!-- AC:END -->
