---
id: task-183
title: Migrate queue management API to Rust (Phase 2)
status: In Progress
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-21 18:32'
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
- [ ] #1 All 7 endpoints migrated to Tauri commands
- [ ] #2 Queue operations functional (add, remove, reorder)
- [ ] #3 Shuffle algorithm implemented correctly
- [ ] #4 Drag-drop file support working
- [ ] #5 Queue persistence working
- [ ] #6 Tauri events emitted for updates
- [ ] #7 Frontend updated and E2E tests passing
<!-- AC:END -->
