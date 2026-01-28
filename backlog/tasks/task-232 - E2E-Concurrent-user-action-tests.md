---
id: task-232
title: 'E2E: Concurrent user action tests'
status: In Progress
assignee: []
created_date: '2026-01-28 05:40'
updated_date: '2026-01-28 08:13'
labels:
  - e2e
  - playback
  - P2
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Playwright E2E tests for rapid sequential user actions to verify debouncing and edge case stability.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Rapid play/pause clicking is debounced correctly
- [ ] #2 Double-click during pending action handled gracefully
- [ ] #3 Multiple track selections in quick succession work
- [ ] #4 Queue operations during playback transition are stable
<!-- AC:END -->
