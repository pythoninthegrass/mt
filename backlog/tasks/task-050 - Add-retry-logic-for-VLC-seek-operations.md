---
id: task-050
title: Add retry logic for VLC seek operations
status: To Do
assignee: []
created_date: '2025-10-12 23:28'
labels: []
dependencies: []
---

## Description

VLC's set_time() and get_time() don't synchronize immediately due to asynchronous media operations. Test test_seek_position fails because get_time() returns old position immediately after set_time(). Implement polling with timeout to verify seek completed before returning success.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Poll get_time() after set_time() with configurable timeout
- [ ] #2 Return success only when position matches requested time
- [ ] #3 Add timeout parameter (default 2s) for seek verification
- [ ] #4 Test test_seek_position passes reliably
<!-- AC:END -->
