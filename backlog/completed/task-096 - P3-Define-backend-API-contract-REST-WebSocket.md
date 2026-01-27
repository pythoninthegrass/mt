---
id: task-096
title: 'P3: Define backend API contract (REST + WebSocket)'
status: Done
assignee: []
created_date: '2026-01-12 04:07'
updated_date: '2026-01-13 06:08'
labels:
  - documentation
  - api
  - phase-3
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Define the API contract between frontend and Python sidecar backend, based on the existing `api/server.py` command surface.

**REST Endpoints:**

Library:
- `GET /api/library` - list all tracks (with optional search query)
- `GET /api/library/stats` - library statistics
- `POST /api/library/scan` - trigger directory scan
- `DELETE /api/library/{track_id}` - remove track from library

Queue:
- `GET /api/queue` - get current queue
- `POST /api/queue/add` - add tracks to queue
- `POST /api/queue/clear` - clear queue
- `DELETE /api/queue/{index}` - remove track at index
- `POST /api/queue/reorder` - reorder queue items

Playlists:
- `GET /api/playlists` - list playlists
- `POST /api/playlists` - create playlist
- `GET /api/playlists/{id}` - get playlist tracks
- `PUT /api/playlists/{id}` - update playlist
- `DELETE /api/playlists/{id}` - delete playlist

Favorites:
- `GET /api/favorites` - list favorites
- `POST /api/favorites/{track_id}` - add to favorites
- `DELETE /api/favorites/{track_id}` - remove from favorites

Settings:
- `GET /api/settings` - get all settings
- `PUT /api/settings/{key}` - update setting

**WebSocket Events (backend → frontend):**
- `library:updated` - library changed
- `queue:updated` - queue changed
- `favorites:updated` - favorites changed

**Document in:** `docs/api-contract.md`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 API contract documented in docs/api-contract.md
- [x] #2 All existing api/server.py actions mapped to REST endpoints
- [x] #3 WebSocket event schema defined
- [x] #4 Request/response schemas defined (JSON)
<!-- AC:END -->
