---
id: task-112
title: 'P3: Build Alpine.js library browser component'
status: To Do
assignee: []
created_date: '2026-01-12 06:35'
labels:
  - frontend
  - alpine
  - phase-3
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the library browser UI component using Alpine.js.

**Features:**
- Collapsible sidebar sections (All Tracks, Recently Added, Favorites, Playlists)
- Virtual scrolling for large libraries
- Search input with instant filtering
- Track list with columns (title, artist, album, duration)
- Double-click to play, right-click context menu
- Drag tracks to queue

**Implementation:**
- Alpine.js store for library state
- Fetch from sidecar `/api/library` endpoints
- Use Tailwind CSS for styling (Basecoat components if available)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Library sections display correctly
- [ ] #2 Search filters tracks in real-time
- [ ] #3 Virtual scrolling handles 10k+ tracks
- [ ] #4 Tracks can be added to queue
<!-- AC:END -->
