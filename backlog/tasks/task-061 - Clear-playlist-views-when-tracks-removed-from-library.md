---
id: task-061
title: Clear playlist views when tracks removed from library
status: Done
assignee: []
created_date: '2025-10-21 20:10'
updated_date: '2025-10-21 20:20'
labels: []
dependencies: []
---

## Description

When tracks are removed from the library, ensure they are also removed from: Liked Songs playlist, Recently Added playlist, Recently Played playlist, and Top 25 Most Played playlist. Currently deleted tracks may still appear in these views until they're manually refreshed.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Liked Songs view automatically removes deleted tracks
- [x] #2 Recently Added view automatically removes deleted tracks
- [x] #3 Recently Played view automatically removes deleted tracks
- [x] #4 Top 25 Most Played view automatically removes deleted tracks
- [x] #5 Database integrity maintained after track deletion
- [x] #6 View refreshes automatically when deletion occurs while view is active
<!-- AC:END -->
