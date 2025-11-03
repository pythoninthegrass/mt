---
id: task-088
title: Convert unnecessary E2E tests to unit tests
status: To Do
assignee: []
created_date: '2025-11-03 06:53'
updated_date: '2025-11-03 06:53'
labels: []
dependencies: []
priority: medium
ordinal: 8000
---

## Description

Audit E2E test files and convert tests that don't require full application startup to unit tests. Target: reduce E2E count by ~30-40 tests to improve test suite speed and maintainability.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Audit all E2E test files for conversion candidates
- [ ] #2 Convert tests that can use mocks instead of real Tkinter/VLC
- [ ] #3 Maintain or improve test coverage
- [ ] #4 Reduce test suite runtime by ~5-8 seconds
<!-- AC:END -->
