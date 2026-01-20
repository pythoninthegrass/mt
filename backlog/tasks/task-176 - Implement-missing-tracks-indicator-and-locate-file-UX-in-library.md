---
id: task-176
title: Implement missing-tracks indicator and locate-file UX in library
status: In Progress
assignee: []
created_date: '2026-01-20 00:51'
updated_date: '2026-01-20 07:18'
labels:
  - tauri-migration
  - feature
  - library
  - ux
dependencies:
  - task-175
priority: medium
ordinal: 1500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When a track's file becomes unreachable (e.g., watched folder removed, network share disconnected, file deleted), the library should:

1. Mark the track as "missing" in the database (do NOT auto-delete from library).
2. Display a visual indicator (info icon) in a new left gutter column in the library listing.
3. Provide hover/click tooltip showing: original file path, last-seen timestamp, and action options (Locate / Ignore).
4. When the user attempts to play a missing track, show a modal dialog with options:
   - "Locate file now" — opens native file picker; on success, update the track's path in the DB and resume playback.
   - "Leave as-is" — dismiss the modal, leave track marked missing, show toast.
5. If locate fails or user cancels, track remains missing and a toast notification is shown.

Reference UX: MusicBee missing-tracks UI (see screenshots in /Users/lance/Desktop/musicbee_missing_tracks.png and musicbee_locate_track.png).

This task is a dependency/companion to task-175 (Watched Folders) but can also apply to any track whose file becomes unreachable for any reason.

User story:
- As a user, I can see at a glance which tracks in my library are missing their files.
- When I try to play a missing track, I'm prompted to locate it or leave it as-is.
- If I locate the file, playback resumes automatically.

Technical notes:
- Add a `missing` (or `file_status`) column to the tracks/library table (e.g., 0=present, 1=missing).
- Add `last_seen_at` timestamp column to track when the file was last verified.
- Backend: On scan or playback attempt, check file existence; update status accordingly.
- Frontend: Add left gutter column to library list component; render info icon for missing tracks.
- Modal: Reuse existing modal patterns; integrate native file picker via Tauri dialog.
- Tauri commands: `locate_track(track_id, new_path)` to update path and clear missing status.
- Events: Emit `track:status-changed` when a track's missing status changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Library listing includes a left gutter column that shows an info icon for missing tracks.
- [ ] #2 Hovering or clicking the info icon displays: original path, last-seen timestamp, Locate action, Ignore action.
- [ ] #3 Attempting to play a missing track opens a modal with 'Locate file now' and 'Leave as-is' options.
- [ ] #4 Selecting 'Locate file now' opens the native file picker; on success, the track path is updated and playback starts.
- [ ] #5 Selecting 'Leave as-is' dismisses the modal, leaves the track marked missing, and shows a toast.
- [ ] #6 If locate fails or is cancelled, track remains missing and a toast is shown.
- [ ] #7 Database schema includes missing status and last_seen_at columns for tracks.
- [ ] #8 Tauri command exists: locate_track(track_id, new_path) to update path and clear missing flag.
- [ ] #9 Unit and integration tests cover missing-track detection and locate flow.
- [ ] #10 Playwright E2E test validates the missing-track icon appears and the locate modal works.
<!-- AC:END -->
