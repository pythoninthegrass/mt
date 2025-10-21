---
id: task-056
title: >-
  Fix Now Playing empty state not showing when last track finishes in loop OFF
  mode
status: Done
assignee: []
created_date: '2025-10-17 06:02'
updated_date: '2025-10-20 02:04'
labels: []
dependencies: []
priority: high
ordinal: 500
---

## Description

When the last track in the queue finishes playing in loop OFF mode, the Now Playing view shows stale track data instead of the empty state message. Specifically, it displays the track that was before the last track in the library, and
      the playback time remains at the finished track's duration instead of clearing.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 When last track finishes in loop OFF mode, both 'Now Playing' and 'Next' sections show empty state
- [x] #2 Playback time indicator clears when queue becomes empty
- [x] #3 No stale track data is displayed after queue becomes empty
- [x] #4 Empty state message 'Queue is empty / Double-click a track in Library to start playing' is shown
<!-- AC:END -->

## Implementation Notes

Fixed by:

1. Connected on_track_change callback from MusicPlayer to PlayerCore so track end events properly refresh the Now Playing view
2. Modified NowPlayingView.refresh_from_queue() to check if media is actually loaded before showing tracks
3. Added player_core reference to NowPlayingView so it can check media state

The fix ensures the Now Playing view shows the empty state when the last track finishes in loop OFF mode, instead of showing stale track data.
