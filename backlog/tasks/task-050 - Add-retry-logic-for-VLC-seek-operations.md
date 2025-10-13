---
id: task-050
title: Add retry logic for VLC seek operations
status: Done
assignee: []
created_date: '2025-10-12 23:28'
updated_date: '2025-10-13 01:13'
labels: []
dependencies: []
---

## Description

VLC's set_time() and get_time() don't synchronize immediately due to asynchronous media operations. Test test_seek_position fails because get_time() returns old position immediately after set_time(). Implement polling with timeout to verify seek completed before returning success.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Poll get_time() after set_time() with configurable timeout
- [x] #2 Return success only when position matches requested time
- [x] #3 Add timeout parameter (default 2s) for seek verification
- [x] #4 Test test_seek_position passes reliably
<!-- AC:END -->

## Implementation Notes

Implemented seek_to_time() method in PlayerCore with polling/verification logic. Fixed API handlers to use seconds consistently and call seek_to_time(). All control tests pass.
