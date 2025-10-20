---
id: task-041
title: Fix playback and utility controls moving when resizing window
status: Done
assignee: []
created_date: '2025-10-12 07:56'
updated_date: '2025-10-20 03:11'
labels: []
dependencies: []
ordinal: 1250
---

## Description

Controls should stay in fixed position when window is resized

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Playback controls remain stationary during window resize
- [x] #2 Utility controls remain stationary during window resize
<!-- AC:END -->


## Implementation Notes

Fixed by storing initial Y positions during control setup and using those stored positions during resize events instead of recalculating. Controls now maintain fixed vertical positions while only adjusting horizontal positions as needed (utility controls stay anchored to right edge, playback controls stay anchored to left edge).
