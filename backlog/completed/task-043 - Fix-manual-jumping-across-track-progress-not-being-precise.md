---
id: task-043
title: Fix manual jumping across track progress not being precise
status: Done
assignee: []
created_date: '2025-10-12 07:56'
updated_date: '2025-10-20 03:22'
labels: []
dependencies: []
ordinal: 500
---

## Description

Clicking 1:00 mark goes to 0:40 instead, first click works but subsequent don't

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Progress bar clicking jumps to correct time position
- [x] #2 Multiple clicks work consistently
<!-- AC:END -->

## Implementation Notes

Fixed by increasing grace period from 0.1s to 0.5s in update_progress() to allow VLC time to complete seek operations. Added E2E test to verify seeking stability.
