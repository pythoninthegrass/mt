---
id: task-183
title: Migrate queue management API to Rust (Phase 2)
status: Done
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-22 00:41'
labels:
  - rust
  - migration
  - queue
  - phase-2
  - api
dependencies:
  - task-173
  - task-180
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate queue management endpoints from FastAPI to Rust Tauri commands, providing all playback queue functionality.

**Endpoints to Migrate** (7 total):
- GET `/api/queue` - Get current queue with track metadata
- POST `/api/queue/add` - Add tracks by ID (optional position)
- POST `/api/queue/add-files` - Add files directly (drag-drop support)
- DELETE `/api/queue/{position}` - Remove track at position
- POST `/api/queue/clear` - Clear entire queue
- POST `/api/queue/reorder` - Move track from position A to B
- POST `/api/queue/shuffle` - Shuffle queue (optional keep_current)

**Features**:
- Queue state management in Rust
- Position-based operations
- Shuffle with Fisher-Yates algorithm
- Drag-and-drop file support
- Queue persistence to database

**Implementation**:
- Convert to Tauri commands
- Use database layer from task-180
- Emit Tauri events for queue updates (queue:updated)
- Use `rand::seq::SliceRandom` for shuffle
- Simple `Vec` manipulation for reordering

**Estimated Effort**: 1 week
**File**: backend/routes/queue.py (126 lines)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 7 endpoints migrated to Tauri commands
- [x] #2 Queue operations functional (add, remove, reorder)
- [x] #3 Shuffle algorithm implemented correctly
- [x] #4 Drag-drop file support working
- [x] #5 Queue persistence working
- [x] #6 Tauri events emitted for updates
- [x] #7 Frontend updated and E2E tests passing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

### Rust Backend (src-tauri/)

1. **New Tauri Commands** (`src/commands/queue.rs`):
   - `queue_get` - Get current queue with track metadata
   - `queue_add` - Add tracks by ID (optional position)
   - `queue_add_files` - Add files directly (drag-drop support)
   - `queue_remove` - Remove track at position
   - `queue_clear` - Clear entire queue
   - `queue_reorder` - Move track from position A to B
   - `queue_shuffle` - Shuffle queue with Fisher-Yates algorithm

2. **Events**: All commands emit `queue:updated` event for frontend notification

3. **Dependencies**: Added `rand = "0.9"` for shuffle algorithm

### Frontend (app/frontend/)

1. **API Client** (`js/api.js`):
   - Updated all queue methods to use Tauri commands when available
   - Added new `addFiles()` method for drag-drop support
   - Maintains HTTP fallback for browser development

2. **Queue Store** (`js/stores/queue.js`):
   - Updated `add()`, `insert()`, `remove()`, `clear()`, `reorder()` to persist via API
   - Added `_syncQueueToBackend()` helper for full queue sync
   - Updated `toggleShuffle()` and `shuffleQueue()` to sync after reorder

### Database Layer

Existing `src/db/queue.rs` already provides all required operations:
- `get_queue()`, `add_to_queue()`, `add_files_to_queue()`
- `remove_from_queue()`, `clear_queue()`, `reorder_queue()`
- `get_queue_length()`
<!-- SECTION:NOTES:END -->
