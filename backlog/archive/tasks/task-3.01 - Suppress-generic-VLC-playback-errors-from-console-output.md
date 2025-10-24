---
id: task-3.01
title: Suppress generic VLC playback errors from console output
status: To Do
assignee: []
created_date: '2025-10-23 16:04'
labels: []
dependencies: []
parent_task_id: task-3
---

## Description

VLC outputs verbose error messages to console for minor playback issues (illegal headers, decode errors). These errors don't affect playback but clutter the console output. Need to suppress or redirect VLC's stderr output while preserving important application logs.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 VLC mpg123 decoder errors should not appear in console output
- [ ] #2 Application logs (GUI, MEDIA_KEY, etc.) should still be visible
- [ ] #3 Solution should handle VLC errors without breaking VLC functionality
- [ ] #4 Consider using VLC logging callback or stderr redirection
<!-- AC:END -->
