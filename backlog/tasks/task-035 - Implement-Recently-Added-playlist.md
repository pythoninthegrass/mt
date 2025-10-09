---
id: task-035
title: Implement Recently Added playlist
status: To Do
assignee: []
created_date: '2025-10-09 05:26'
labels: []
dependencies: []
---

## Description

Create a dynamic 'Recently Added' playlist that displays tracks added to the library within the last two weeks, using the existing added_date timestamp field.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Recently Added playlist created and visible in left panel navigation, positioned after Liked Songs
- [ ] #2 Playlist displays only tracks where added_date is within the last 14 days
- [ ] #3 Tracks sorted by added_date in descending order (most recent first)
- [ ] #4 Playlist view matches library > music view styling, showing tracks with standard columns (artist, title, album, track#, year)
- [ ] #5 Playlist automatically updates as tracks age in/out of the 14-day window
- [ ] #6 Playlist state persists across application restarts
- [ ] #7 Clicking on tracks in the playlist adds them to queue and plays as expected
- [ ] #8 All playlist interactions logged with Eliot using appropriate trigger sources
<!-- AC:END -->
