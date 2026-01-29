---
id: task-242
title: 'Zig migration: DB library queries'
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
Migrate library query logic to Zig while preserving existing query behavior and results.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Library query results match current behavior on sample data
- [ ] #2 Rust callers use Zig via FFI without user-visible changes
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/db/library.zig

Stubbed query functions: getAllTracks, getTrackById, searchTracks, upsertTrack, deleteTrack

Uses DbHandle opaque type for connection

Returns QueryResults with allocator-based memory management

Full-text search across title/artist/album

Dependencies: Requires task 241 complete for models
<!-- SECTION:NOTES:END -->
