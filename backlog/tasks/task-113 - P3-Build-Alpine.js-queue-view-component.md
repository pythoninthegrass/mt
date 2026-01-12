---
id: task-113
title: 'P3: Build Alpine.js queue view component'
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
Create the queue view UI component using Alpine.js.

**Features:**
- Display current queue with track info
- Highlight currently playing track
- Drag-and-drop reordering
- Remove tracks from queue
- Clear queue button
- Show queue duration total

**Implementation:**
- Alpine.js store for queue state
- Fetch from sidecar `/api/queue` endpoints
- Use HTML5 drag-and-drop API or sortable library
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Queue displays with track metadata
- [ ] #2 Drag-and-drop reordering works
- [ ] #3 Currently playing track is highlighted
- [ ] #4 Remove and clear operations work
<!-- AC:END -->
