---
id: task-076
title: Increase PlayerCore test coverage from 29% to 50%+
status: To Do
assignee: []
created_date: '2025-10-26 04:51'
updated_date: '2025-10-27 02:08'
labels: []
dependencies: []
priority: medium
ordinal: 7000
---

## Description

PlayerCore currently has only 29% test coverage (103/357 lines tested). Key untested areas include track-end handling, play count tracking, and media event callbacks. Improve coverage to at least 50%.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Add unit tests for _handle_track_end() loop/shuffle logic
- [ ] #2 Add unit tests for _update_play_count() play count tracking
- [ ] #3 Add unit tests for track navigation edge cases (empty queue, single track, etc.)
- [ ] #4 Add unit tests for media event callbacks (MediaEnded, MediaPaused, etc.)
- [ ] #5 Add property-based tests for queue navigation invariants
- [ ] #6 Achieve >50% coverage for core/controls/player_core.py
<!-- AC:END -->
