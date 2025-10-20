---
id: task-054
title: Mock VLC for deterministic unit testing
status: Done
assignee: []
created_date: '2025-10-12 23:28'
updated_date: '2025-10-13 01:49'
labels: []
dependencies: []
---

## Description

Create VLC stub/mock for unit tests to avoid timing issues and external dependencies. Keep E2E tests using real VLC for integration validation, but add fast unit tests with mocked VLC for core logic testing. Use pytest-mock or unittest.mock.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Create MockVLCMediaPlayer class mimicking vlc.MediaPlayer API
- [x] #2 Add unit tests for PlayerCore with mocked VLC
- [x] #3 Separate unit tests (mocked) from integration tests (real VLC)
- [x] #4 Unit tests run in <1s total
- [x] #5 Document when to use unit vs E2E tests
<!-- AC:END -->

## Implementation Notes

Implemented comprehensive mock VLC for unit testing. Created MockVLCMediaPlayer with deterministic behavior. Added 20 unit tests covering volume, seek, loop, shuffle, stop, and track navigation. Tests run in 0.12s. Documented testing guidelines in tests/README.md.
