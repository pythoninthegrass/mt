---
id: task-132
title: Implement custom (manual) playlists in Tauri UI (replace stubs)
status: Done
assignee: []
created_date: '2026-01-14 19:21'
updated_date: '2026-01-14 19:45'
labels:
  - ui
  - playlists
  - tauri-migration
  - backend
milestone: Tauri Migration
dependencies:
  - task-006
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Tauri migration UI currently shows a Playlists section in the sidebar (e.g., “Chill Vibes”, “Workout Mix”, “Focus Music”) and an “Add to playlist” context-menu entry, but these are placeholders (non-functional).

Implement **manual/custom playlists** end-to-end in the Tauri app, mirroring the business logic and UX from the Tkinter implementation on the `main` branch (see `docs/custom-playlists.md` and the playlist CRUD/order semantics in the legacy app).

Notes:
- Backend already appears to expose playlist endpoints under `/api/playlists` and persists `playlists` + `playlist_items`.
- Frontend should stop using hard-coded playlists in `app/frontend/js/components/sidebar.js` and replace any “Playlists coming soon!” stubs.
- Must preserve the distinction between **dynamic playlists** (Liked/Recently Added/Recently Played/Top 25) vs **custom playlists** (user-created).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sidebar Playlists section loads real playlists from backend and no longer uses hard-coded placeholder items
- [ ] #2 User can create a new playlist from the UI (button/pill) and it persists via backend
- [ ] #3 User can rename and delete custom playlists from the UI with appropriate validation/confirmation (match Tkinter behavior: unique names, non-empty)
- [ ] #4 Selecting a custom playlist loads its tracks into the main library table view (playlist view)
- [ ] #5 User can add tracks to a playlist from the library context menu (Add to playlist submenu populated from backend playlists)
- [ ] #6 User can remove tracks from a playlist without deleting them from the library (playlist view delete/remove semantics match Tkinter)
- [ ] #7 User can reorder tracks inside a playlist and the new order persists (drag-and-drop reorder + backend update)
- [ ] #8 UI updates appropriately after playlist CRUD/track changes (refresh list, track counts if shown; optionally via websocket playlists:updated)
<!-- AC:END -->
