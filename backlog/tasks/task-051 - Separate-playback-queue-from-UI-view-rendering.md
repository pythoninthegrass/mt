---
id: task-051
title: Separate playback queue from UI view rendering
status: To Do
assignee: []
created_date: '2025-10-12 23:28'
labels: []
dependencies: []
---

## Description

Architectural refactor to decouple queue management from UI display. Currently load_queue() populates queue_view based on playback_context, mixing concerns. Queue table should be single source of truth for playback, with separate methods for rendering different views (library, liked, top25) without affecting queue state.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Queue table is sole source of truth for playback order
- [ ] #2 load_queue() only shows queue table items
- [ ] #3 Add separate methods: load_library_view(), load_liked_view(), load_top_played_view()
- [ ] #4 playback_context doesn't affect queue operations
- [ ] #5 All queue-related tests pass without view confusion
<!-- AC:END -->
