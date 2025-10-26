---
id: task-074
title: Add integration tests for recent bug fixes
status: In Progress
assignee: []
created_date: '2025-10-26 04:51'
updated_date: '2025-10-26 04:53'
labels: []
dependencies: []
priority: high
ordinal: 2000
---

## Description

Add automated tests for code paths added during Python 3.12 migration bug fixes. These areas currently lack test coverage and caused regressions during manual testing.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Add E2E test: Media key with empty queue populates from library view
- [ ] #2 Add E2E test: Search filtering correctly populates queue view without reloading library
- [ ] #3 Add unit test: update_play_button() changes icon for play/pause states
- [ ] #4 Add unit test: _get_all_filepaths_from_view() extracts correct filepath order
- [ ] #5 Add integration test: Double-click track → queue populated → playback starts
<!-- AC:END -->
