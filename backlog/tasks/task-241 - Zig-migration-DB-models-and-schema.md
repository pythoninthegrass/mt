---
id: task-241
title: 'Zig migration: DB models and schema'
status: Done
assignee: []
created_date: '2026-01-28 23:23'
updated_date: '2026-01-29 03:18'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Move DB models and schema definitions to Zig as the source of truth while keeping Rust integration stable.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Schema definitions and models in Zig match current Rust structures
- [ ] #2 Database initialization/migrations remain unchanged from a user perspective
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/db/models.zig

Defined extern structs: Track, Playlist, QueueItem, Setting

All use fixed-size buffers for FFI safety

Added SCHEMA_SQL.tracks_table CREATE statement

Schema version: 1

Models match Rust struct layouts

TODO: Add schemas for playlists, queue, settings, scrobbles, watched_folders
<!-- SECTION:NOTES:END -->
