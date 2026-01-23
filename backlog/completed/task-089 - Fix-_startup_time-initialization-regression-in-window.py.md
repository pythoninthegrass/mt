---
id: task-089
title: Fix _startup_time initialization regression in window.py
status: Done
assignee: []
created_date: '2026-01-10 05:31'
updated_date: '2026-01-10 05:45'
labels: []
dependencies: []
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TypeError in on_window_configure: self._startup_time is None when it should be a float. The startup time tracking was not properly initialized, causing crashes during window configuration events in the first 2 seconds after startup.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 self._startup_time is properly initialized as float in __init__
- [x] #2 No TypeError occurs during window configuration events
- [x] #3 Startup window resize filtering works as intended
<!-- AC:END -->
