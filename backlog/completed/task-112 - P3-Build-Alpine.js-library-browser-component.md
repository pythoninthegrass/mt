---
id: task-112
title: 'P3: Build Alpine.js library browser component'
status: Done
assignee: []
created_date: '2026-01-12 06:35'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - alpine
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-110
  - task-117
priority: high
ordinal: 45382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the library browser UI component using Alpine.js and Basecoat.

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
- Use Basecoat UI components (static file approach)

**Basecoat Setup (static files):**
Copy from lunch repo or CDN:
```html
<link href="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/basecoat.cdn.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/js/all.min.js" defer></script>
```

**Basecoat Components to Use:**
- `.sidebar` - Collapsible navigation with `aria-current="page"` for active section
- `.tabs` - For library view tabs (if needed)
- `.dropdown-menu` - Right-click context menu (`role="menu"`, `role="menuitem"`)
- `.input` - Search input styling
- `.btn` - Action buttons

**Sidebar HTML Structure:**
```html
<nav class="sidebar">
  <div class="sidebar-item" aria-current="page">All Tracks</div>
  <div class="sidebar-item">Recently Added</div>
  <div class="sidebar-item">Favorites</div>
</nav>
```

**Dropdown Menu Structure:**
```html
<div class="dropdown-menu">
  <button type="button">...</button>
  <div role="menu">
    <button role="menuitem">Play</button>
    <button role="menuitem">Add to Queue</button>
    <button role="menuitem">Add to Playlist</button>
  </div>
</div>
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Library sections display correctly
- [ ] #2 Search filters tracks in real-time
- [ ] #3 Virtual scrolling handles 10k+ tracks
- [ ] #4 Tracks can be added to queue
<!-- AC:END -->
