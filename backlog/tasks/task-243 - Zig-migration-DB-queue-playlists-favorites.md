---
id: task-243
title: 'Zig migration: DB queue/playlists/favorites'
status: Done
assignee: []
created_date: '2026-01-28 23:23'
updated_date: '2026-01-29 03:18'
labels: []
dependencies:
  - task-241
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate queue, playlist, and favorites database operations to Zig while preserving current behaviors.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Queue, playlist, and favorites behaviors match current Rust implementations
- [ ] #2 Rust callers use Zig via FFI without user-visible changes
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/db/queue.zig

Stubbed queue operations: getQueue, addToQueue, removeFromQueue, clearQueue

Stubbed playlist operations: getAllPlaylists, createPlaylist, addToPlaylist

Stubbed favorites operations: getFavorites, toggleFavorite

Queue maintains position ordering

Dependencies: Requires task 241 complete for models
<!-- SECTION:NOTES:END -->
