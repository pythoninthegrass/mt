---
id: task-126
title: 'Tauri UI: Fix Recently Added dynamic playlist (added timestamp + API query)'
status: Done
assignee: []
created_date: '2026-01-14 02:31'
updated_date: '2026-01-14 05:36'
labels:
  - tauri
  - frontend
  - backend
  - dynamic-playlist
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Alpine.js/Tauri “Recently Added” view should be a true dynamic playlist based on import time, showing when each track was added and limiting to a defined recency window (e.g., last 14 days). Currently it appears to just show the full library sorted client-side without a visible “Added” time column.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Recently Added view shows a visible “Added” column (timestamp or humanized time) matching design expectations.
- [x] #2 Recently Added view is populated only with tracks whose added timestamp is within the configured recency window (default: last 14 days).
- [x] #3 The list ordering is descending by added timestamp.
- [x] #4 Library scan/import sets added timestamps correctly for new tracks.
- [x] #5 When a track is removed from the library, its added/play metadata is removed as well so it cannot appear in dynamic playlists.
<!-- AC:END -->
