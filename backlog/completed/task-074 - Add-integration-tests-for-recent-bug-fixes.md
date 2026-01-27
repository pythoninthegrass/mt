---
id: task-074
title: Add integration tests for recent bug fixes
status: Done
assignee: []
created_date: '2025-10-26 04:51'
updated_date: '2026-01-24 22:28'
labels: []
dependencies: []
priority: high
ordinal: 26382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add automated tests for code paths added during Python 3.12 migration bug fixes. These areas currently lack test coverage and caused regressions during manual testing.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add E2E test: Media key with empty queue populates from library view
- [x] #2 Add E2E test: Search filtering correctly populates queue view without reloading library
- [x] #3 Add unit test: update_play_button() changes icon for play/pause states
- [x] #4 Add unit test: _get_all_filepaths_from_view() extracts correct filepath order
- [x] #5 Add integration test: Double-click track → queue populated → playback starts
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added comprehensive test coverage for Python 3.12 migration bug fixes. Created two test files:

1. test_e2e_bug_fixes.py with 3 passing E2E/integration tests:
   - test_media_key_with_empty_queue_populates_from_library (NOW PASSING)
   - test_search_filtering_populates_queue_view_without_reload
   - test_double_click_track_populates_queue_and_starts_playback

2. test_unit_bug_fixes.py with 9 passing unit tests:
   - 3 tests for update_play_button()
   - 6 tests for _get_all_filepaths_from_view()

All 12 tests pass successfully. 

CORRECTION: AC #1 was initially skipped because I incorrectly thought the feature wasn't implemented. After user confirmation that the feature works, I unskipped the test and it passes. The feature was implemented during Python 3.12 migration bug fixes in PlayerCore.play_pause() (lines 80-93) which populates queue from current view when queue is empty.
<!-- SECTION:NOTES:END -->
