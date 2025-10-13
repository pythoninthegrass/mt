---
id: task-052
title: Add explicit state reset in test fixtures
status: To Do
assignee: []
created_date: '2025-10-12 23:28'
labels: []
dependencies: []
---

## Description

Some test failures may be due to state leaking between tests. playback_context and current_view aren't reset in clean_queue fixture. Add explicit reset of application state variables between tests to ensure isolation.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reset playback_context to default in clean_queue fixture
- [ ] #2 Reset current_view to queue in clean_queue fixture
- [ ] #3 Clear VLC media player state between tests
- [ ] #4 Document all stateful variables that need reset
- [ ] #5 Tests don't affect each other's state
<!-- AC:END -->
