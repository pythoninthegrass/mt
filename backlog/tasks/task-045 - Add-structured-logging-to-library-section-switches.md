---
id: task-045
title: Add structured logging to library section switches
status: To Do
assignee: []
created_date: '2025-10-07 04:31'
labels:
  - logging
  - ui-navigation
  - phase3
dependencies: []
priority: medium
---

## Description

Implement comprehensive structured logging for the on_section_select method in player.py to track user navigation between Music, Now Playing, and Playlists views. This logging will help understand user navigation patterns and provide context for view changes including content counts.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Navigation between sections (Music/Now Playing/Playlists) is logged with structured Eliot actions,Content count for newly selected view is included in log context,User navigation patterns are trackable through log entries,Logging follows established start_action pattern with appropriate context,All section switch operations include before/after view state
<!-- AC:END -->
