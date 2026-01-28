---
id: task-229
title: 'E2E: Search result ranking tests'
status: In Progress
assignee: []
created_date: '2026-01-28 05:40'
updated_date: '2026-01-28 08:13'
labels:
  - e2e
  - library
  - search
  - P1
dependencies: []
priority: high
ordinal: 953.125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Playwright E2E tests for search result ranking logic. Search tests exist but don't verify result ordering logic.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Exact title match ranks first
- [ ] #2 Artist match ranks appropriately
- [ ] #3 Partial matches appear after exact matches
- [ ] #4 Search with multiple terms returns expected order
<!-- AC:END -->
