---
id: task-037
title: Add structured logging to media key handling
status: To Do
assignee: []
created_date: '2025-10-07 04:27'
labels:
  - logging
  - media-keys
  - high-priority
dependencies: []
priority: high
---

## Description

Implement comprehensive structured logging for hardware media key press events in utils/mediakeys.py to track user interactions with physical media controls. This logging should differentiate between different trigger sources (GUI vs media_key vs keyboard) and provide detailed context about which media key was pressed.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Media key press events are logged with start_action context including key type (play/pause, next, previous),Logging differentiates between trigger sources (gui vs media_key vs keyboard),All media key interactions include appropriate metadata and context,Logging follows established pattern with log_player_action helper function,No existing functionality is broken by the logging additions
<!-- AC:END -->
