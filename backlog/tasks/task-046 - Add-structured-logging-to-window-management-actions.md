---
id: task-046
title: Add structured logging to window management actions
status: To Do
assignee: []
created_date: '2025-10-07 04:31'
labels:
  - logging
  - window-management
  - phase3
dependencies: []
priority: medium
---

## Description

Implement comprehensive structured logging for stoplight buttons (close/minimize/maximize) in gui.py to track window management actions. This logging will help understand user window behavior patterns and provide context for window state changes including position and size information.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Close/minimize/maximize actions from stoplight buttons are logged with structured Eliot actions,Window state and position context is included in log entries,User window management patterns are trackable through log entries,Logging differentiates stoplight actions from keyboard shortcuts,All window management operations include before/after window state
<!-- AC:END -->
