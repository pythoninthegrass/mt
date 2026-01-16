---
id: task-147
title: 'Finish playlists in Tauri UI (remove sidebar stubs, wire real flows)'
status: In Progress
assignee: []
created_date: '2026-01-16 04:59'
updated_date: '2026-01-16 04:59'
labels:
  - ui
  - playlists
  - sidebar
  - tauri-migration
milestone: Tauri Migration
dependencies:
  - task-104
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
The sidebar playlists are still stubbed:
- `sidebar.js` has `// TODO: Load playlists from backend` and hardcoded playlist items (`Chill Vibes`, `Workout Mix`, `Focus Music`)
- `loadPlaylist()` shows "Playlists coming soon!" toast instead of loading tracks

Meanwhile, `library-browser.js` already has real playlist API calls (`api.playlists.getAll()`, `create()`, `addTracks()`, `removeTrack()`, `reorder()`, `get()`).

## Scope (Minimum Spec)
1. **Sidebar loads real playlists** from backend
2. **Click playlist** → loads playlist tracks into library view
3. **Create playlist** button works end-to-end
4. **Context menu** on playlist name (right-click) with Rename and Delete options
5. **Drag-and-drop** tracks from library view to sidebar playlist names

## Files to modify

### Sidebar (`app/frontend/js/components/sidebar.js`)
- Replace stubbed `loadPlaylists()` with real `api.playlists.getAll()` call
- Replace stubbed `loadPlaylist(playlistId)` with:
  - `this.library.setSection('playlist-' + playlistId)`
  - Trigger library-browser to fetch playlist tracks
- Add right-click context menu binding for custom playlists
- Add context menu component (Rename, Delete options)
- Wire `createPlaylist()` to real API flow (prompt for name → `api.playlists.create()`)

### Library Browser (`app/frontend/js/components/library-browser.js`)
- Ensure `section.startsWith('playlist-')` branch loads playlist tracks correctly
- Wire drag-start on track rows to enable drop on sidebar playlists

### Index HTML (`app/frontend/index.html`)
- Add `data-testid` attributes for playlist items if needed
- Add context menu markup for playlist rename/delete

### Tests
- `app/frontend/tests/sidebar.spec.js` - Update playlist tests to use real/mocked API data
- Add test: clicking playlist loads playlist view
- Add test: create playlist updates sidebar list
- Add test: context menu shows rename/delete options

## Backend (already implemented)
- `GET /api/playlists` - list all playlists
- `POST /api/playlists` - create playlist
- `GET /api/playlists/:id` - get playlist with tracks
- `PUT /api/playlists/:id` - rename playlist
- `DELETE /api/playlists/:id` - delete playlist
- `POST /api/playlists/:id/tracks` - add tracks
- `DELETE /api/playlists/:id/tracks/:position` - remove track
- `POST /api/playlists/:id/tracks/reorder` - reorder tracks
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sidebar playlists list loads from backend (no hardcoded items)
- [ ] #2 Clicking a playlist loads its tracks into library view
- [ ] #3 Active playlist is highlighted in sidebar
- [ ] #4 Create playlist button prompts for name and creates via API
- [ ] #5 Right-click context menu on playlist shows Rename and Delete options
- [ ] #6 Rename playlist updates name in sidebar and backend
- [ ] #7 Delete playlist removes from sidebar and backend (with confirmation)
- [ ] #8 Drag tracks from library view to sidebar playlist adds them to that playlist
- [ ] #9 Playlist changes refresh sidebar list (via mt:playlists-updated event)
- [ ] #10 Playwright tests cover: load playlists, click playlist, create playlist, context menu
<!-- AC:END -->
