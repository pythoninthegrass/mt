---
id: task-198
title: 'Phase 3: Polish - Artwork caching and settings unification'
status: In Progress
assignee: []
created_date: '2026-01-24 22:30'
updated_date: '2026-01-24 22:31'
labels:
  - implementation
  - frontend
  - rust
  - migration
  - phase-3
  - polish
dependencies:
  - task-170
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the polish migrations identified in task-170 analysis:

1. **Artwork caching in Rust**
   - Add in-memory LRU cache for recently-played track artwork
   - Reduces IPC calls when navigating queue (prev/next)
   - Cache invalidation when track metadata changes

2. **Settings unification**
   - Migrate Alpine.$persist UI preferences to backend settings store
   - Already have `settings_get/set` Tauri commands
   - Keep local cache for instant UI response, sync to backend

3. **Time formatting cleanup** (optional)
   - Either: Add Tauri commands `format_duration_ms`, `format_bytes`
   - Or: Send pre-formatted strings from backend
   - Or: Consolidate frontend utilities to single module
   - Goal: Remove duplication across player.js and player-controls.js

These are lower priority polish items that improve performance and consistency.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 LRU artwork cache implemented in Rust
- [ ] #2 Artwork cache reduces IPC calls for queue navigation
- [ ] #3 UI preferences migrated from localStorage to backend settings
- [ ] #4 Settings sync between frontend cache and backend store
- [ ] #5 Time formatting utilities consolidated (one of the three approaches)
- [ ] #6 All existing tests pass
- [ ] #7 Performance improvement measurable for large queues
<!-- AC:END -->
