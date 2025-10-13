---
id: task-053
title: Increase sleep timeouts in E2E tests for reliability
status: To Do
assignee: []
created_date: '2025-10-12 23:28'
labels: []
dependencies: []
---

## Description

Current 0.5s sleep timeouts may be insufficient on slower systems or under load. VLC operations and UI updates may take longer than expected. Increase timeouts to 1-2 seconds and add configurable TEST_TIMEOUT environment variable.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Increase time.sleep() from 0.5s to 1s in critical tests
- [ ] #2 Add TEST_TIMEOUT env var (default 1.0)
- [ ] #3 Use TEST_TIMEOUT in helpers/api_client.py
- [ ] #4 Document timeout rationale in test files
- [ ] #5 Tests pass reliably on slower systems
<!-- AC:END -->
