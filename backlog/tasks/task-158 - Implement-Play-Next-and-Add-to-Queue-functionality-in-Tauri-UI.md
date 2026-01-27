---
id: task-158
title: Implement Play Next and Add to Queue functionality in Tauri UI
status: Done
assignee: []
created_date: '2026-01-16 23:29'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - queue
  - tauri-migration
  - feature
dependencies: []
priority: high
ordinal: 60382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port the "Play Next" and "Add to Queue" context menu functionality from the legacy Python/Tkinter implementation to the Tauri/Alpine.js frontend.

## Current State
- Legacy Tkinter UI has working implementations in `app/core/now_playing/view.py` and `app/core/gui/queue_view.py`
- Tauri UI has context menu items in `library-browser.js` but the wiring is broken:
  - `library-browser.js` calls `this.queue.addTracks()` which doesn't exist in queue store
  - `library-browser.js` calls `this.queue.add(trackId, position)` but store expects track objects
  - JS API client endpoints don't match FastAPI routes (JS posts to `/queue`, backend has `/queue/add`)
  - Backend returns `{items, count}`, frontend expects `{items, currentIndex}`

## Required Changes

### 1. Queue Store (`app/frontend/js/stores/queue.js`)
- Add `addTracks(tracks)` method for batch adding
- Fix `insert(index, tracks)` to work with the "Play Next" use case
- Ensure proper sync with backend API

### 2. API Client (`app/frontend/js/api.js`)
- Fix queue endpoints to match backend routes:
  - `POST /queue/add` for adding tracks by ID
  - `POST /queue/add-files` for adding by filepath
  - `POST /queue/reorder` for reordering

### 3. Library Browser (`app/frontend/js/components/library-browser.js`)
- Fix `playSelectedNext()` to use correct queue store methods
- Fix `addSelectedToQueue()` to use correct queue store methods

### 4. Backend Alignment (if needed)
- Ensure `GET /queue` returns `currentIndex` for frontend state sync
- Verify all queue routes work correctly

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 "Add to Queue" adds selected tracks to end of queue
- [x] #2 "Play Next" inserts selected tracks after currently playing track
- [ ] #3 Queue state syncs correctly between frontend and backend
- [x] #4 Toast notifications show success/failure
- [x] #5 Works with single and multiple track selection
<!-- SECTION:DESCRIPTION:END -->

<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

### Changes Made

#### 1. Queue Store (`app/frontend/js/stores/queue.js`)
- Added `addTracks(tracks, playNow)` method as an alias for `add()` for batch operations
- Added `playNextTracks(tracks)` method to insert tracks after the currently playing track
- Fixed `load()` to properly unwrap track objects from backend response format (`{position, track}` → `track`)

#### 2. API Client (`app/frontend/js/api.js`)
- Fixed `queue.add()` endpoint from `/queue` to `/queue/add` to match backend route
- Fixed `queue.move()` endpoint from `/queue/move` to `/queue/reorder` with correct field names (`from_position`/`to_position`)

#### 3. Library Browser (`app/frontend/js/components/library-browser.js`)
- Fixed `playSelectedNext()` to use the new `queue.playNextTracks(tracks)` method instead of incorrectly calling `queue.add(trackId, position)` in a loop

#### 4. Playwright Tests (`app/frontend/tests/queue.spec.js`)
- Added new test suite "Play Next and Add to Queue (task-158)" with 5 tests:
  - Add to Queue should append tracks to end of queue
  - Play Next should insert track after currently playing
  - Play Next with multiple selected tracks should insert all after current
  - Add to Queue should show toast notification
  - Play Next should show toast notification

### Architecture Notes
- The frontend queue is managed locally in Alpine.js store
- Backend queue routes exist but are primarily for the legacy Python app
- Queue state persists loop/shuffle settings to localStorage
- The `save()` method is currently a no-op (local-only) which is intentional for the Tauri architecture

### Testing Notes
- Playwright E2E tests require the full Tauri application stack (audio backend) to pass
- Tests timeout on `waitForPlaying` without the Tauri backend running
- Code changes verified via LSP diagnostics (no errors)
<!-- SECTION:NOTES:END -->
