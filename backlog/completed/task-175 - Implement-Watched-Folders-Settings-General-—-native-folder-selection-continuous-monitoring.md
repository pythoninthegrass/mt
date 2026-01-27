---
id: task-175
title: >-
  Implement 'Watched Folders' (Settings > General) — native folder selection +
  continuous monitoring
status: Done
assignee: []
created_date: '2026-01-20 00:42'
updated_date: '2026-01-24 22:28'
labels:
  - tauri-migration
  - feature
  - settings
  - file-watcher
dependencies: []
priority: medium
ordinal: 7382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Allow users to add folders using the native file browser (Finder / Explorer) and mark them as Watched Folders. Watched folders should behave like "Add folder to library" today (scan and add tracks), but additionally support a monitoring mode so the app can re-scan for changes automatically.

User story
- As a user I can select a folder from the native file picker and mark it as a Watched Folder.
- I can edit the watch options from Settings > General.
- I can choose either "Scan on startup" or "Continuously monitor". If Continuously monitor is chosen, the cadence (how frequently to perform a full scan) is configurable in minutes.
- Changes discovered in watched folders (new tracks, removed tracks, metadata changes) are reflected in the library automatically (with appropriate debouncing/coalescing of events).

Requirements / Acceptance criteria
1. UI: Settings > General must include a "Watched Folders" section where users can:
   - See a list of watched folders (path, mode, cadence in minutes, enabled/disabled toggle, last scanned timestamp, status)
   - Add a new watched folder using the native folder picker (Finder / Explorer). Adding acts like the existing "Add folder to library" flow and triggers an initial scan.
   - Edit an existing watched folder to change mode (Scan on startup vs Continuously monitor) and cadence (minutes), and to enable/disable or remove it.
   - Manually trigger a rescan for a watched folder.
   - Add multiple watched folders.

2. Persistence: Watched folder entries are persisted in app storage (SQLite settings table or new table) with fields: id, path, mode (startup|continuous), cadence_minutes (nullable), enabled (bool), last_scanned_at (timestamp), created_at, updated_at.

3. Backend behavior (Tauri/Rust):
   - New Tauri commands: list_watched_folders, add_watched_folder, update_watched_folder, remove_watched_folder, rescan_watched_folder.
   - On app startup, load enabled watched folders and:
     * For mode=startup: perform a full scan once at startup (immediately after library initialization).
     * For mode=continuous: start watchers and schedule periodic full scans at the configured cadence (minutes). Full-scan cadence must be in minutes and editable.
   - Use a cross-platform file watcher (notify crate recommended) to receive file-system events and queue incremental updates. Events must be debounced and coalesced into batched rescans to avoid combing repeated events.
   - Provide a configurable debounce window (implementation detail) and ensure long-running scanning runs off the main thread (tokio tasks) so the UI remains responsive.

4. Scanning semantics:
   - Initial add triggers a full recursive scan of the folder (same rules as existing library scanner).
   - Watcher events should schedule incremental scanning of changed directories/files; the system should still run the periodic full scan at the cadence.
   - Changes detected add/remove/update tracks in library (no duplicate entries). All changes must be logged.

5. Events / UI updates:
   - Backend emits events for watched-folder status changes and scan progress/results so the frontend can show status to the user (toast/notifications, newest tracks added count).

6. Tests:
   - Unit tests for watcher code (debouncing, scheduling, error handling)
   - Integration tests for Tauri commands (add/list/remove/update)
   - Playwright E2E test(s) that mock folder selection and validate Settings UI and that a rescan updates the library UI

7. Packaging / Build:
   - Ensure new native watcher dependencies are included in tauri builds and the app bundles properly.

Implementation notes / recommended approach
- Frontend: Use existing pattern for folder selection (current 'Add folder' flow uses Tauri dialog or similar). Reuse the same native folder picker code (Tauri @tauri-apps/api/dialog) so UX is consistent.
- Backend: Implement watcher management in src-tauri (Rust). Use the notify crate (https://crates.io/crates/notify) for cross-platform file watching. Use tokio::spawn for scheduling periodic scans using tokio::time::interval with minutes resolution.
- Persist watched folders in SQLite (new table `watched_folders`) or in existing settings table if that matches project patterns. Provide migrations.
- Expose Tauri commands for CRUD operations and emit events for status/progress.
- Debounce filesystem events (e.g., 500-2000ms configurable) and batch updates to avoid frequent scans on large changes.
- Provide a manual "Rescan now" action for each watched folder.

Questions / clarifications for product
- Default cadence (minutes) for "Continuous monitor" — suggest 10 minutes by default. Accept user preference.
- Should watched folders be monitored recursively by default? (Recommendation: yes.)
- When a watched folder is removed, should the library remove the tracks that were added from that folder? (Recommendation: do NOT auto-delete tracks from library on folder removal; instead, leave them in library unless user explicitly removes them.)

Labels: ["tauri-migration","feature","settings","file-watcher"]
Priority: medium
Status: To Do
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Settings > General includes a 'Watched Folders' section with add/edit/remove/enable/disable/manually rescan actions.
- [x] #2 User can add folders using the OS native folder picker and the initial scan adds tracks to the library.
- [x] #3 Watched folders are persisted and survive app restarts.
- [x] #4 App performs 'scan on startup' or 'continuous monitor' based on the chosen mode; continuous monitor supports a cadence specified in minutes.
- [x] #5 Filesystem events are debounced/coalesced; continuous monitoring plus periodic full-scans keep the library in sync.
- [x] #6 Tauri commands exist for CRUD and rescan operations and backend emits status/progress events.
- [x] #7 Automated unit, integration, and E2E tests are added to cover the new flows.

- [x] #8 Missing tracks (file not found) display an info icon in the left gutter of the library listing.
- [x] #9 Clicking the info icon or hovering shows original path, last-seen timestamp, and actions (Locate / Ignore).
- [x] #10 When user attempts to play a missing track, a modal appears with options: 'Locate file now' or 'Leave as-is'.
- [x] #11 If user locates the file successfully, the track's path is updated in the database and playback resumes.
- [x] #12 If locate fails or user cancels, track remains marked missing and a toast is shown.
<!-- AC:END -->
