---
id: task-111
title: 'P2: Add sidecar queue endpoints (CRUD, reorder)'
status: Done
assignee: []
created_date: '2026-01-12 06:35'
updated_date: '2026-01-26 01:28'
labels:
  - backend
  - python
  - phase-2
milestone: Tauri Migration
dependencies: []
priority: high
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add queue management endpoints to the Python sidecar.

**Endpoints to add:**
- `GET /api/queue` - Get current queue
- `POST /api/queue` - Add track(s) to queue
- `DELETE /api/queue/{id}` - Remove track from queue
- `PUT /api/queue/reorder` - Reorder queue items
- `DELETE /api/queue` - Clear queue
- `GET /api/queue/current` - Get currently playing track

**Implementation:**
- Reuse existing `core/queue.py` logic
- Maintain queue state in SQLite (same schema as main branch)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Queue CRUD endpoints work
- [ ] #2 Reorder endpoint updates positions correctly
- [ ] #3 Queue persists across sidecar restarts
<!-- AC:END -->
