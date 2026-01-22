---
id: task-186
title: Migrate favorites API to Rust (Phase 3)
status: Done
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-22 16:48'
labels:
  - rust
  - migration
  - favorites
  - phase-3
  - api
dependencies:
  - task-173
  - task-180
priority: medium
ordinal: 1656.25
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate favorites management endpoints from FastAPI to Rust Tauri commands, providing favorites and smart lists functionality.

**Endpoints to Migrate** (7 total):
- GET `/api/favorites` - Get favorited tracks (paginated)
- POST `/api/favorites/{track_id}` - Add track to favorites
- DELETE `/api/favorites/{track_id}` - Remove track from favorites
- GET `/api/favorites/{track_id}` - Check if track is favorited
- GET `/api/favorites/top-25` - Top 25 most played tracks
- GET `/api/favorites/recently-played` - Recently played (14 days)
- GET `/api/favorites/recently-added` - Recently added (14 days)

**Features**:
- Favorites CRUD operations
- Smart lists (top 25, recent plays, recent adds)
- Timestamp tracking
- Duplicate prevention (UNIQUE constraint)
- Pagination support

**Database Operations**:
- favorites table (id, track_id, timestamp)
- Foreign key to library table
- Unique constraint on track_id
- Time-based queries (datetime arithmetic)

**Implementation**:
- Convert to Tauri commands
- Use database layer from task-180
- Emit Tauri events for favorite updates
- Handle duplicate add attempts gracefully
- SQL time-based filtering (14 days lookback)

**Estimated Effort**: 1 week
**File**: backend/routes/favorites.py (86 lines)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 7 endpoints migrated to Tauri commands
- [x] #2 Favorites CRUD operations functional
- [x] #3 Top 25 query working correctly
- [x] #4 Recently played query functional (14 days)
- [x] #5 Recently added query functional (14 days)
- [x] #6 Duplicate prevention working
- [x] #7 Frontend updated and E2E tests passing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary (2026-01-22)

### Changes Made

1. **Created `src-tauri/src/commands/favorites.rs`**
   - 7 Tauri commands: `favorites_get`, `favorites_check`, `favorites_add`, `favorites_remove`, `favorites_get_top25`, `favorites_get_recently_played`, `favorites_get_recently_added`
   - All commands use existing database layer functions from `db::favorites`
   - Events emitted via `FavoritesUpdatedEvent` for add/remove operations
   - Response types match Python API for frontend compatibility

2. **Updated `src-tauri/src/commands/mod.rs`**
   - Added `favorites` module
   - Re-exported all 7 favorites commands

3. **Updated `src-tauri/src/lib.rs`**
   - Imported favorites commands
   - Registered all 7 commands in `invoke_handler`

4. **Updated `app/frontend/js/api.js`**
   - All 7 favorites methods now use Tauri commands when available
   - HTTP fallback preserved for browser development mode
   - Error handling maps Rust errors to appropriate HTTP status codes

### Testing
- All Rust tests passing (8 favorites-related tests)
- Frontend unit tests passing (10 tests)
- E2E tests: 254 passed, 15 failed (all failures pre-existing, unrelated to favorites)
  - "Liked Songs section" test passed
  - Failures are in Last.fm (not migrated), drag/reorder UI, and metadata editor navigation
<!-- SECTION:NOTES:END -->
