---
id: task-149
title: Add context menu to edit track metadata from library view
status: Done
assignee: []
created_date: '2026-01-16 06:29'
updated_date: '2026-01-17 08:50'
labels:
  - feature
  - ui
  - metadata
dependencies: []
priority: medium
ordinal: 250
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a right-click context menu on tracks in the library browser that allows users to edit track metadata (title, artist, album, track number, etc.) directly from the UI.

## Background
During debugging of track sorting, discovered that metadata inconsistencies (e.g., same album stored as "Clair Obscur Expedition 33" vs "Clair Obscur: Expedition 33") cause tracks to appear incorrectly grouped. Users need a way to fix metadata without leaving the app.

## Requirements
- Right-click on a track row opens a context menu
- Context menu includes "Edit Metadata..." option
- Opens a modal/dialog with editable fields:
  - Title
  - Artist
  - Album
  - Album Artist
  - Track Number
  - Disc Number
  - Year
  - Genre
- Save button writes changes to the audio file's metadata tags
- Changes reflect immediately in the library view
- Support batch editing (select multiple tracks, edit common fields)

## Technical Considerations
- Use mutagen (Python) or lofty/symphonia (Rust) for metadata writing
- Need to handle different audio formats (MP3, FLAC, M4A, etc.)
- Consider undo functionality
- May need to re-scan the file after editing to update database
<!-- SECTION:DESCRIPTION:END -->
