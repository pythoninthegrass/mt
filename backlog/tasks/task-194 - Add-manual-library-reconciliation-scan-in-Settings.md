---
id: task-194
title: Add manual library reconciliation scan in Settings
status: Done
assignee: []
created_date: '2026-01-22 21:35'
updated_date: '2026-01-24 22:28'
labels:
  - settings
  - library
  - deduplication
  - move-detection
  - ux
dependencies:
  - task-193
priority: high
ordinal: 19382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a manual "Manual Scan" option in Settings > Library > Scanning that fixes legacy tracks and deduplicates entries.

### Problem
Tracks added before the move detection refactor have NULL inode/content_hash values. This means:
- Move detection doesn't work for these tracks
- Moving files creates orphaned entries and duplicates
- Manual "Locate file..." doesn't update inode/hash, so future moves still fail

### Requested Feature
A settings button that triggers a reconciliation scan:

1. **Backfill inode/hash**: For all tracks where file exists but inode or content_hash is NULL, compute and store these values

2. **Deduplicate**: Find tracks with matching inode OR matching content_hash, merge them:
   - Keep the non-missing entry (or most recently seen)
   - Preserve metadata (play count, favorites, playlist membership)
   - Delete the duplicate row

3. **Update Locate flow**: When user manually locates a file, also update inode + content_hash (related but could be separate task)

### UI Location
Settings > Library > Scanning > "Manual Scan"

Use miller column navigation pattern:
- Settings sidebar shows top-level categories (General, Library, etc.)
- Selecting "Library" shows sub-categories (Scanning, etc.)
- Selecting "Scanning" shows the scanning options including Manual Scan

### Implementation Notes
- New Tauri command: `library_reconcile_scan`
- Iterates all tracks, checks file existence, updates inode/hash
- Groups by inode and hash to find duplicates
- Emits progress events for UI feedback
- Should match existing settings UI patterns (basecoat components)
- Miller column layout enables future grouping of related library settings
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Settings sidebar shows Library category with Scanning sub-section (miller column pattern)
- [x] #2 Manual Scan button visible in Settings > Library > Scanning
- [x] #3 Button styling matches existing settings UI patterns (basecoat components)
- [x] #4 Clicking button triggers a scan that backfills inode/content_hash for all tracks with NULL values
- [x] #5 Scan identifies and merges duplicate tracks (same inode or same content_hash)
- [x] #6 Merge logic preserves non-missing track, keeps metadata from most complete record
- [x] #7 Progress indicator shown during reconciliation scan
- [x] #8 Summary displayed after completion (e.g., 'Updated X tracks, merged Y duplicates')

- [x] #9 Works for all watched folders, not just one
- [x] #10 Miller column navigation allows future expansion of Library sub-settings
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- New Tauri command: `library_reconcile_scan`
- Iterates all tracks, checks file existence, updates inode/hash
- Groups by inode and hash to find duplicates
- Emits progress events for UI feedback
- Should match existing settings UI patterns (see watched folders UI)
<!-- SECTION:DESCRIPTION:END -->
<!-- SECTION:NOTES:END -->
