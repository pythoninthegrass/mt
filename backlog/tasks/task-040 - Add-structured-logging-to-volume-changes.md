---
id: task-040
title: Add structured logging to volume changes
status: To Do
assignee: []
created_date: '2025-10-07 04:27'
labels:
  - logging
  - volume-control
  - high-priority
dependencies: []
priority: high
---

## Description

Replace existing print statements in volume_change method in player.py with comprehensive structured logging using start_action pattern. The logging should capture volume adjustment events with both old and new volume levels to provide complete tracking of user audio preferences.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Print statements in volume_change method are replaced with start_action logging,Volume change events include both old and new volume level values,Logging captures the source of volume change (slider, media keys, etc),All volume adjustments include appropriate context and metadata,Logging follows established pattern with log_player_action helper function,No existing functionality is broken by the logging additions
<!-- AC:END -->
