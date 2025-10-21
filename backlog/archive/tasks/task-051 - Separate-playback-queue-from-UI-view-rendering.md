---
id: task-051
title: Separate playback queue from UI view rendering
status: Done
assignee: []
created_date: '2025-10-12 23:28'
updated_date: '2025-10-13 01:20'
labels: []
dependencies: []
---

## Description

Architectural refactor to decouple queue management from UI display. Currently load_queue() populates queue_view based on playback_context, mixing concerns. Queue table should be single source of truth for playback, with separate methods for rendering different views (library, liked, top25) without affecting queue state.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Queue table is sole source of truth for playback order
- [x] #2 load_queue() only shows queue table items
- [x] #3 Add separate methods: load_library_view(), load_liked_view(), load_top_played_view()
- [x] #4 playback_context doesn't affect queue operations
- [x] #5 All queue-related tests pass without view confusion
<!-- AC:END -->

## Implementation Notes

Successfully refactored queue and view separation:

- load_queue() now only loads from queue table
- Removed playback_context attribute entirely  
- Separate view methods already existed (load_library, load_liked_songs, load_top_25_most_played)
- All 18 queue and playback tests pass
