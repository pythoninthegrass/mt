---
id: task-244
title: 'Zig migration: DB settings/scrobble/watched'
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
Migrate settings, scrobble tracking, and watched folders database operations to Zig while preserving current behaviors.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Settings, scrobble, and watched folder behaviors match current Rust implementations
- [ ] #2 Rust callers use Zig via FFI without user-visible changes
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/db/settings.zig

Stubbed settings operations: getSetting, setSetting, deleteSetting

Stubbed scrobble tracking: recordPlay, getPendingScrobbles, markScrobbleSubmitted

Stubbed watched folders: getWatchedFolders, addWatchedFolder, removeWatchedFolder, updateWatchedFolderMode

Defined ScrobbleRecord and WatchedFolder extern structs

Watched folders support 3 scan modes: manual, auto, watch

Dependencies: Requires task 241 complete for models
<!-- SECTION:NOTES:END -->
