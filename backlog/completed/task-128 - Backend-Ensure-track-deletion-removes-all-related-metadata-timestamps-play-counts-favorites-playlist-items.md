---
id: task-128
title: >-
  Backend: Ensure track deletion removes all related metadata (timestamps, play
  counts, favorites, playlist items)
status: Done
assignee: []
created_date: '2026-01-14 02:31'
updated_date: '2026-01-14 02:38'
labels:
  - backend
  - database
  - data-integrity
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When tracks are deleted from the library (via API or UI), ensure all related metadata is cleaned up so dynamic playlists and user data remain consistent. This includes play_count, last_played, added_date, favorites rows, and playlist_items rows. Also consider bulk removal during library cleanup/rescan for missing files.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Deleting a track from the library removes it from the library table and also removes associated rows in favorites and playlist_items (no orphan records).
- [x] #2 After deletion, the track no longer appears in any dynamic playlists (Recently Played, Recently Added, Top 25) and does not surface via API queries.
- [x] #3 Database foreign key/cascade behavior is verified (or explicit cleanup is implemented) so invariants hold even if deletes occur in different code paths.
- [x] #4 A backend-level test (unit/property) covers deletion cleanup and prevents regressions.

- [x] #5 Play count / last played updates are triggered at 75% playback completion (not 90%), and only once per track play session, in the backend playback reporting flow used by the Tauri app.
<!-- AC:END -->
