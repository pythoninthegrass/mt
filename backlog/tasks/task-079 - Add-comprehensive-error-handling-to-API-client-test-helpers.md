---
id: task-079
title: Add comprehensive error handling to API client test helpers
status: Done
assignee: []
created_date: '2025-10-26 18:40'
updated_date: '2026-01-24 22:28'
labels: []
dependencies: []
priority: medium
ordinal: 30382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The API client in tests should gracefully handle server disconnections and provide better error messages. Currently, when the app crashes mid-test, cascading failures occur because the client doesn't handle connection failures robustly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add connection retry logic with exponential backoff in APIClient.send()
- [x] #2 Add connection health checks before each test operation
- [x] #3 Wrap API calls in tests with try/except to catch ConnectionError
- [x] #4 Add logging to identify which API call caused server disconnect
- [x] #5 Consider circuit breaker pattern for test stability
<!-- AC:END -->
