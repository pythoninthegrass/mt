---
id: task-054
title: Mock VLC for deterministic unit testing
status: To Do
assignee: []
created_date: '2025-10-12 23:28'
labels: []
dependencies: []
---

## Description

Create VLC stub/mock for unit tests to avoid timing issues and external dependencies. Keep E2E tests using real VLC for integration validation, but add fast unit tests with mocked VLC for core logic testing. Use pytest-mock or unittest.mock.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create MockVLCMediaPlayer class mimicking vlc.MediaPlayer API
- [ ] #2 Add unit tests for PlayerCore with mocked VLC
- [ ] #3 Separate unit tests (mocked) from integration tests (real VLC)
- [ ] #4 Unit tests run in <1s total
- [ ] #5 Document when to use unit vs E2E tests
<!-- AC:END -->
