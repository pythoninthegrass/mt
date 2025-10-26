---
id: task-067
title: Suppress generic VLC playback errors from console output
status: Done
assignee: []
created_date: '2025-10-23 16:06'
updated_date: '2025-10-24 03:16'
labels: []
dependencies: []
priority: low
ordinal: 3000
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
