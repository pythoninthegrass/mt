---
id: task-186
title: Migrate favorites API to Rust (Phase 3)
status: In Progress
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-21 18:32'
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
- [ ] #1 All 7 endpoints migrated to Tauri commands
- [ ] #2 Favorites CRUD operations functional
- [ ] #3 Top 25 query working correctly
- [ ] #4 Recently played query functional (14 days)
- [ ] #5 Recently added query functional (14 days)
- [ ] #6 Duplicate prevention working
- [ ] #7 Frontend updated and E2E tests passing
<!-- AC:END -->
