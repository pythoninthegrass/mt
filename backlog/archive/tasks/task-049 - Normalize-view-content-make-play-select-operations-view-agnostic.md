---
id: task-049
title: Normalize view content - make play/select operations view-agnostic
status: Done
assignee: []
created_date: '2025-10-12 23:28'
updated_date: '2025-10-13 01:04'
labels: []
dependencies: []
---

## Description

Currently, queue_view.queue serves dual purposes: showing actual queue OR showing library/liked/top25 based on playback_context. This makes play_track_at_index() and select_queue_item() ambiguous - they rely on UI widget children count which varies by active view. Refactor to always use database queue as source of truth for playback operations, making them independent of current UI view.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 play_track_at_index uses queue table, not UI children
- [x] #2 select_queue_item validates index against queue table
- [x] #3 Index validation works regardless of active view
- [x] #4 Tests test_play_track_at_index and test_play_invalid_index pass
<!-- AC:END -->

## Implementation Notes

Refactored _handle_play_track_at_index and _handle_select_queue_item in api/api.py to use database queue as source of truth instead of UI widget children count. Both functions now validate index against queue_manager.get_queue_items() before operations. Tests pass successfully.
