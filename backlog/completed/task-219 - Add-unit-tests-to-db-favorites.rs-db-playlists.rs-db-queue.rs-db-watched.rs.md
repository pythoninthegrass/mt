---
id: task-219
title: 'Add unit tests to db/favorites.rs, db/playlists.rs, db/queue.rs, db/watched.rs'
status: Done
assignee: []
created_date: '2026-01-27 22:33'
updated_date: '2026-01-27 22:52'
labels:
  - testing
  - coverage
  - rust
dependencies:
  - task-209
priority: low
ordinal: 18375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
These db modules have coverage gaps that can be improved without Tauri runtime.

## Current Coverage
- db/favorites.rs: 57% (73/127 lines)
- db/playlists.rs: 68% (125/184 lines)
- db/queue.rs: 67% (109/163 lines)
- db/watched.rs: 71% (70/98 lines)

## Tests to Add

### db/favorites.rs (~10 tests)
- `remove_favorite()`
- `is_favorite()`
- `get_favorite_track_ids()`
- `add_multiple_favorites()`

### db/playlists.rs (~12 tests)
- `delete_playlist()`
- `reorder_playlist_items()`
- `remove_track_from_playlist()`
- `get_playlist_track_ids()`

### db/queue.rs (~10 tests)
- `move_queue_item()`
- `get_queue_item_at_position()`
- `insert_at_position()`
- `remove_from_queue_by_position()`

### db/watched.rs (~6 tests)
- `update_watched_folder()`
- `delete_watched_folder()`
- `get_watched_folder_paths()`

## Expected Outcome
~135 additional lines covered, bringing testable code coverage to ~62%
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All new tests pass
- [x] #2 No test regressions
- [x] #3 db/favorites.rs coverage > 75%
- [x] #4 db/playlists.rs coverage > 80%
- [x] #5 db/queue.rs coverage > 80%
- [x] #6 db/watched.rs coverage > 85%
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Status Update (2026-01-27)

This task is now **optional** - with the tarpaulin exclusions configured in task-220, coverage is already 54.07% (above the 50% threshold).

These tests can still be added incrementally to further improve coverage and catch more bugs, but they're not blocking CI.

## Completed 2026-01-27

### Tests Added

**db/favorites.rs** (+12 tests):
- test_get_recently_played_empty
- test_get_recently_played_with_tracks
- test_get_recently_played_respects_limit
- test_get_recently_added_empty
- test_get_recently_added_with_tracks
- test_get_recently_added_respects_limit
- test_remove_favorite_nonexistent
- test_is_favorite_nonexistent_track
- test_get_favorites_pagination
- test_get_top_25_with_zero_plays
- test_get_top_25_orders_by_play_count

**db/playlists.rs** (+17 tests):
- test_create_playlist_duplicate_name
- test_get_playlist_nonexistent
- test_update_playlist_name
- test_update_playlist_name_conflict
- test_update_playlist_nonexistent
- test_update_playlist_no_changes
- test_add_duplicate_track_to_playlist
- test_remove_track_invalid_position
- test_reorder_playlist_invalid_from
- test_reorder_playlist_invalid_to
- test_reorder_playlists
- test_reorder_playlists_invalid_positions
- test_get_playlist_track_count
- test_get_playlist_track_count_empty
- test_delete_playlist_nonexistent
- test_playlist_with_tracks_returns_track_data

**db/queue.rs** (+16 tests):
- test_remove_from_queue_invalid_position
- test_reorder_queue_invalid_from
- test_reorder_queue_invalid_to
- test_get_queue_state_default
- test_set_queue_state
- test_set_current_index
- test_set_shuffle_enabled
- test_set_loop_mode
- test_set_original_order_json
- test_add_files_to_queue_new_files
- test_add_files_to_queue_existing_files
- test_add_files_to_queue_at_position
- test_get_queue_empty
- test_get_queue_length
- test_add_to_queue_nonexistent_tracks

**db/watched.rs** (+11 tests):
- test_get_watched_folder_nonexistent
- test_get_watched_folder_by_path
- test_get_watched_folder_by_path_nonexistent
- test_update_watched_folder_no_changes
- test_update_watched_folder_partial
- test_update_watched_folder_nonexistent
- test_remove_watched_folder_nonexistent
- test_update_last_scanned_nonexistent
- test_get_watched_folders_multiple
- test_watched_folder_disabled_by_default

### Results

| Metric | Before | After |
|--------|--------|-------|
| Total tests | 469 | **521** (+52) |
| Coverage | 54.07% | **62.35%** (+8.28%) |
| db/favorites.rs | 57% | **98.4%** |
| db/playlists.rs | 68% | **97.3%** |
| db/queue.rs | 67% | **99.4%** |
| db/watched.rs | 71% | **96.9%** |
<!-- SECTION:NOTES:END -->
