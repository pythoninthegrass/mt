---
id: task-127
title: 'Tauri UI: Fix Top 25 dynamic playlist (play count column + API query)'
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
The Alpine.js/Tauri “Top 25” view should be a true dynamic playlist ranked by play count, showing play counts and updating as playback occurs. Currently it appears to show the full library without displaying play count and without guaranteeing a top-25-by-plays filter.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Top 25 view shows a visible “Play Count” column.
- [x] #2 Top 25 view only shows up to 25 tracks ranked by play count (descending), with a stable tie-breaker (e.g., last played desc).
- [x] #3 Playback increments play count and updates the Top 25 view accordingly.
- [x] #4 If no tracks have play counts yet, the view shows an appropriate empty state.
- [x] #5 When a track is removed from the library, its play-count metadata is removed as well so it cannot appear in Top 25.

- [x] #6 Play count increments at 75% playback completion (not 90%), and only once per track play session.
<!-- AC:END -->
