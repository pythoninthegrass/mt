---
id: task-086
title: Fix test suite regression - app crashes causing cascade failures
status: Done
assignee: []
created_date: '2025-10-27 04:38'
updated_date: '2025-10-27 05:03'
labels: []
dependencies: []
priority: high
ordinal: 2000
---

## Description

The full test suite is experiencing cascading failures where the app process crashes and subsequent E2E tests fail with 'Connection refused' errors. Analysis shows: (1) Property tests contaminate VLC state when run after E2E tests, returning -1 for time/duration operations with mock media; (2) App crashes during property tests cause 56+ E2E test errors; (3) Test ordering via pytest-order markers isn't sufficient. Root cause: Inadequate test isolation between unit/property tests (which mock VLC) and E2E tests (which use real VLC). The shared VLC instance state persists across tests causing conflicts.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Investigate why app crashes during/after property tests in full suite
- [x] #2 Implement proper VLC cleanup between test sessions or enforce strict test ordering
- [x] #3 Fix property tests to handle real VLC gracefully or skip when VLC is already loaded
- [x] #4 Verify full test suite passes with no cascade failures (487+ tests passing)
<!-- AC:END -->


## Implementation Notes

Fixed module caching issue preventing proper VLC mocking in property tests. Root cause: E2E tests import PlayerCore with real VLC at module level, then property tests cannot properly mock it due to Python's import cache. Solution: Property test fixture now removes cached player_core modules before patching VLC, then restores them after test completes. This ensures clean isolation between unit/property tests (mocked VLC) and E2E tests (real VLC).
