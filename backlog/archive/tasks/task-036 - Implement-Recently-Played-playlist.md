---
id: task-036
title: Implement Recently Played playlist
status: Done
assignee: []
created_date: '2025-10-09 05:26'
updated_date: '2025-10-21 19:18'
labels: []
dependencies: []
ordinal: 2000
---

## Description

Create a dynamic 'Recently Played' playlist that displays tracks played within the last two weeks, using the existing last_played timestamp field that is updated by the update_play_count method.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Recently Played playlist created and visible in left panel navigation, positioned after Recently Added
- [x] #2 Playlist displays only tracks where last_played is within the last 14 days
- [x] #3 Tracks sorted by last_played timestamp in descending order (most recent first)
- [x] #4 Playlist view matches library > music view styling, showing tracks with standard columns (artist, title, album, track#, year)
- [x] #5 Playlist automatically updates when tracks are played and as tracks age in/out of the 14-day window
- [x] #6 Playlist only shows tracks that have been played at least once (last_played IS NOT NULL)
- [x] #7 Playlist state persists across application restarts
- [x] #8 Clicking on tracks in the playlist adds them to queue and plays as expected
- [x] #9 All playlist interactions logged with Eliot using appropriate trigger sources
<!-- AC:END -->

## Implementation Notes

Implementation complete. Added database query method (get_recently_played), library manager wrapper, player load method (load_recently_played), and section handlers in on_section_select. Playlist displays tracks played in last 14 days with 'Last Played' timestamp column. All acceptance criteria met.
