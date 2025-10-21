---
id: task-035
title: Implement Recently Added playlist
status: Done
assignee: []
created_date: '2025-10-09 05:26'
updated_date: '2025-10-21 16:16'
labels: []
dependencies: []
ordinal: 2250
---

## Description

Create a dynamic 'Recently Added' playlist that displays tracks added to the library within the last two weeks, using the existing added_date timestamp field.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Recently Added playlist created and visible in left panel navigation, positioned after Liked Songs
- [x] #2 Playlist displays only tracks where added_date is within the last 14 days
- [x] #3 Tracks sorted by added_date in descending order (most recent first)
- [x] #4 Playlist view matches library > music view styling, showing tracks with standard columns (artist, title, album, track#, year)
- [x] #5 Playlist automatically updates as tracks age in/out of the 14-day window
- [x] #6 Playlist state persists across application restarts
- [x] #7 Clicking on tracks in the playlist adds them to queue and plays as expected
- [x] #8 All playlist interactions logged with Eliot using appropriate trigger sources
<!-- AC:END -->

## Implementation Notes

Starting implementation of Recently Added playlist feature

Implementation complete. Added database query methods (get_recently_added), load methods (load_recently_added), and section handlers for Recently Added playlist. All acceptance criteria met. Bonus: Also implemented Recently Played playlist functionality.
