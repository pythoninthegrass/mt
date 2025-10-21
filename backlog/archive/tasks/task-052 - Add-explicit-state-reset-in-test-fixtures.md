---
id: task-052
title: Add explicit state reset in test fixtures
status: Done
assignee: []
created_date: '2025-10-12 23:28'
updated_date: '2025-10-13 01:33'
labels: []
dependencies: []
---

## Description

Some test failures may be due to state leaking between tests. playback_context and current_view aren't reset in clean_queue fixture. Add explicit reset of application state variables between tests to ensure isolation.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reset playback_context to default in clean_queue fixture
- [x] #2 Reset current_view to queue in clean_queue fixture
- [x] #3 Clear VLC media player state between tests
- [x] #4 Document all stateful variables that need reset
- [x] #5 Tests don't affect each other's state
<!-- AC:END -->

## Implementation Notes

Implemented explicit state reset in clean_queue fixture.

Reset the following stateful variables:

- Queue content (cleared via clear_queue API)
- VLC media player state (stopped if playing)
- Current view (reset to 'queue')
- Loop state (disabled if enabled)
- Shuffle state (disabled if enabled)
- Volume (set to 80%)

Note: 'playback_context' mentioned in original task description doesn't exist in current codebase. Reset VLC media player state and other playback-related state instead.

All 32 E2E tests pass, confirming state isolation works correctly.
