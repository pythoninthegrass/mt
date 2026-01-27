---
id: task-123
title: Fix drag and drop of directories to recursively add music files and album art
status: Done
assignee: []
created_date: '2026-01-14 01:46'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - backend
  - library
  - drag-drop
  - file-scanning
dependencies: []
priority: high
ordinal: 77382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix the drag and drop functionality for adding directories to the music library. When a user drags a folder onto the library view, it should:

1. **Recursive scanning**: Traverse all subdirectories to find audio files
2. **Supported formats**: Detect and add compatible audio files (MP3, FLAC, OGG, WAV, M4A, AAC, AIFF, etc.)
3. **Album art detection**: While scanning, also detect and associate album art files with tracks:
   - Embedded artwork in audio file metadata
   - Folder-based artwork (cover.jpg, folder.png, album.jpg, etc.)
4. **Progress feedback**: Show scanning progress for large directories
5. **Deduplication**: Skip files already in the library (based on path or content hash)

**Current behavior**: Drag and drop may not work or may not recursively scan directories.

**Expected behavior**: Dropping a music folder adds all audio files from that folder and its subfolders to the library, with associated album art metadata.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Dragging a directory onto library view triggers recursive scan
- [ ] #2 All supported audio formats are detected and added
- [ ] #3 Subdirectories are scanned recursively
- [ ] #4 Album art files in folders are detected and associated with tracks
- [ ] #5 Duplicate files are skipped
- [ ] #6 Progress indicator shown during scan
- [ ] #7 Toast notification shows count of added tracks on completion
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Complete (2026-01-14)

Commit: 98a3432

### Changes Made:
1. **library.js**: Increased track limit from 100 to 10000, switched Add Music dialog to use Rust invoke command
2. **capabilities/default.json**: Added core:webview:default permission for drag-drop
3. **dialog.rs**: Async dialog implementation with oneshot channels

### Root Cause:
- Library was limited to 100 tracks by default API call
- JS dialog plugin API was unreliable; Rust command is more stable
- Missing webview permission for drag-drop events
<!-- SECTION:NOTES:END -->
