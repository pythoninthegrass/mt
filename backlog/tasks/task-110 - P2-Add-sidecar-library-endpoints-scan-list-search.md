---
id: task-110
title: 'P2: Add sidecar library endpoints (scan, list, search)'
status: To Do
assignee: []
created_date: '2026-01-12 06:35'
labels:
  - backend
  - python
  - phase-2
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the Python sidecar with library management endpoints.

**Endpoints to add:**
- `POST /api/library/scan` - Scan directory for music files
- `GET /api/library` - List all tracks with pagination
- `GET /api/library/search?q=` - Search tracks by title/artist/album
- `GET /api/library/{id}` - Get single track metadata
- `DELETE /api/library/{id}` - Remove track from library

**Implementation:**
- Reuse existing `core/db/` and `core/library.py` from main branch
- Copy relevant modules to `backend/core/`
- Use aiosqlite for async database access
- WebSocket endpoint for scan progress updates
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Library scan endpoint works and reports progress
- [ ] #2 List/search endpoints return track data
- [ ] #3 Database schema matches existing mt.db
- [ ] #4 WebSocket sends scan progress events
<!-- AC:END -->
