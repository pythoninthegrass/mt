---
id: task-048
title: Add structured logging for queue reordering operations
status: To Do
assignee: []
created_date: '2025-10-07 04:32'
labels:
  - logging
  - queue-management
  - phase3
dependencies: []
priority: medium
---

## Description

Implement comprehensive structured logging for queue drag-and-drop reordering operations to track user queue management actions. This logging will help understand how users organize their playback queue and provide context for track positioning and metadata.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Track reordering operations are logged with before and after positions in structured Eliot actions,Moved track metadata is included in log context for identification,Queue management actions are trackable through structured log entries,Drag-and-drop operations include source and destination position data,All reordering operations follow established start_action logging pattern with appropriate context
<!-- AC:END -->
