---
id: task-010
title: Implement lyrics functionality
status: Done
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2025-10-24 03:00'
labels: []
dependencies: []
ordinal: 375
---

## Description

Add lyrics display and integration with lyricsgenius

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Research lyrics API providers
- [x] #2 Implement lyrics fetching and caching
- [x] #3 Create lyrics display UI component
- [x] #4 Test lyrics with various track formats
<!-- AC:END -->


## Implementation Plan

- Show under the now playing queue view (i.e., to the right of queue)


## Implementation Notes

Split Now Playing into two columns: Album Art (left ~25-30%) + Tabbed Content (right ~70-75%). Right side has UP NEXT and LYRICS tabs. Album art shows placeholder musical note icon. Lyrics fetched via Genius API with SQLite caching.
