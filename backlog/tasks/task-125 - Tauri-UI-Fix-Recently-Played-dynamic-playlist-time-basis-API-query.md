---
id: task-125
title: 'Tauri UI: Fix Recently Played dynamic playlist (time-basis + API query)'
status: Done
assignee: []
created_date: '2026-01-14 02:31'
updated_date: '2026-01-24 22:28'
labels:
  - tauri
  - frontend
  - backend
  - dynamic-playlist
dependencies: []
priority: high
ordinal: 74382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Alpine.js/Tauri “Recently Played” view should be a true dynamic playlist based on playback history, showing when each track was last played and limiting to a defined recency window (e.g., last 14 days). Currently it appears to just show the full library sorted client-side without a visible “Last Played” time column.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Recently Played view shows a visible “Last Played” column (timestamp or humanized time) matching design expectations.
- [x] #2 Recently Played view is populated only with tracks that have been played within the configured recency window (default: last 14 days).
- [x] #3 The list ordering is descending by last played time.
- [x] #4 Playback updates last played metadata so the view updates after listening activity.
- [x] #5 When a track is removed from the library, its playback metadata (last played, play count) is removed as well so it cannot appear in dynamic playlists.

- [x] #6 Play count/last played are updated when a track reaches 75% playback completion (not 90%), and only once per track play session.
<!-- AC:END -->
