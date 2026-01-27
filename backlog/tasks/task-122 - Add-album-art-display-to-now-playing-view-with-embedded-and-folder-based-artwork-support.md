---
id: task-122
title: >-
  Add album art display to now playing view with embedded and folder-based
  artwork support
status: Done
assignee: []
created_date: '2026-01-14 01:45'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - backend
  - now-playing
  - album-art
  - metadata
dependencies: []
priority: medium
ordinal: 79382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enhance the now playing view to display album art to the left of track metadata. Support multiple artwork sources:

1. **Embedded artwork**: Extract album art embedded in audio file metadata (ID3 tags for MP3, Vorbis comments for FLAC/OGG, etc.)
2. **Folder-based artwork**: Look for common artwork files in the same directory as the audio file:
   - cover.jpg, cover.png
   - folder.jpg, folder.png
   - album.jpg, album.png
   - front.jpg, front.png
   - artwork.jpg, artwork.png

**Layout changes:**
- Move album art placeholder from center to left of track metadata
- Display artwork at appropriate size (e.g., 200x200 or 250x250)
- Show placeholder icon when no artwork is available

**Implementation considerations:**
- Backend endpoint to extract/serve album artwork
- Caching strategy for extracted artwork
- Fallback chain: embedded → folder-based → placeholder
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Album art displays to the left of track metadata in now playing view
- [x] #2 Embedded album art is extracted and displayed when available
- [x] #3 Folder-based artwork files are detected and displayed as fallback
- [x] #4 Placeholder icon shown when no artwork is available
- [x] #5 Artwork loads without blocking playback
- [x] #6 Common artwork filenames supported (cover, folder, album, front, artwork with jpg/png extensions)
<!-- AC:END -->
