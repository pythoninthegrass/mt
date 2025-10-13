---
id: task-053
title: Increase sleep timeouts in E2E tests for reliability
status: Done
assignee: []
created_date: '2025-10-12 23:28'
updated_date: '2025-10-13 01:42'
labels: []
dependencies: []
---

## Description

Current 0.5s sleep timeouts may be insufficient on slower systems or under load. VLC operations and UI updates may take longer than expected. Increase timeouts to 1-2 seconds and add configurable TEST_TIMEOUT environment variable.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Increase time.sleep() from 0.5s to 1s in critical tests
- [x] #2 Add TEST_TIMEOUT env var (default 1.0)
- [x] #3 Use TEST_TIMEOUT in helpers/api_client.py
- [x] #4 Document timeout rationale in test files
- [x] #5 Tests pass reliably on slower systems
<!-- AC:END -->
