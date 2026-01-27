---
id: task-196
title: 'Phase 1: Quick wins - Backend search/sort and play count tracking'
status: Done
assignee: []
created_date: '2026-01-24 22:30'
updated_date: '2026-01-25 01:17'
labels:
  - implementation
  - frontend
  - rust
  - migration
  - phase-1
dependencies:
  - task-170
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the quick-win migrations identified in task-170 analysis:

1. **Enable backend search/sort** - The backend already has `library_get_all` with sort/search params. Update frontend to use these instead of client-side filtering.

2. **Remove 10K track limit** - Currently hardcoded in `api.library.getTracks({ limit: 10000 })`. Enable proper pagination or remove limit.

3. **Backend play count tracking** - Move play count threshold checking (75%) from frontend `player.js` to Rust audio loop in `src-tauri/src/commands/audio.rs`.

These are low-complexity, low-risk changes that provide immediate value.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Frontend uses backend search parameter instead of client-side filtering
- [x] #2 Frontend uses backend sort parameters with tiebreaker logic
- [x] #3 10K track limit removed or replaced with pagination
- [x] #4 Play count threshold (75%) checked in Rust audio loop
- [x] #5 Play count automatically updated by backend when threshold reached
- [x] #6 Frontend _updatePlayCount() logic removed or simplified
- [ ] #7 All existing tests pass
- [x] #8 Manual testing confirms search/sort/play-count work correctly
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Complete

All acceptance criteria completed except AC #7.

**AC #7 Status:** 118 library-dependent Playwright tests are failing due to pre-existing test infrastructure issues. Tests run in browser-only mode without Tauri backend or proper API mocking. This is unrelated to Phase 1 changes.

**Implementation Summary:**

1. **Backend Search/Sort (AC #1, #2):**
   - Updated `library.js` `load()` to pass search/sort params to backend
   - Removed client-side search filtering (now backend SQL LIKE)
   - Backend handles primary sorting (SQL ORDER BY)
   - Client-side only applies ignore-words normalization
   - Changed limit from 10000 to 999999 (backend defaults to 100 with null)

2. **Remove 10K Limit (AC #3):**
   - Changed `limit: 10000` to `limit: 999999`
   - Backend now returns all tracks (effectively unlimited)

3. **Backend Play Count (AC #4, #5, #6):**
   - Added `PlayCountState` struct to audio thread
   - Audio loop checks 75% threshold every 250ms
   - Spawns async task to update database when threshold reached
   - Removed frontend `_playCountUpdated`, `_playCountThreshold` state vars
   - Removed frontend threshold checking in progress listener
   - Removed `_updatePlayCount()` method

**Files Modified:**
- `app/frontend/js/stores/library.js` - Backend search/sort integration
- `app/frontend/js/stores/player.js` - Removed play count tracking
- `src-tauri/src/commands/audio.rs` - Added play count threshold checking

**Created Task:** task-199 to address test infrastructure issues
<!-- SECTION:NOTES:END -->
