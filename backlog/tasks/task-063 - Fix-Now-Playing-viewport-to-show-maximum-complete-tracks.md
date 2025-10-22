---
id: task-063
title: Fix Now Playing viewport to show maximum complete tracks
status: Done
assignee: []
created_date: '2025-10-21 22:49'
updated_date: '2025-10-22 01:35'
labels: []
dependencies: []
ordinal: 500
---

## Description

The Now Playing view should calculate and display the maximum number of complete track rows that fit in the viewport. Currently showing only 3-4 tracks when there's room for 6-8. Each track row is 71px (70px + 1px padding). Need to properly calculate available viewport height and show all tracks that completely fit without partial rows at bottom.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Calculate viewport height correctly (total height - current section 100px - divider 1px - next label 30px)
- [x] #2 Show maximum number of complete 71px rows that fit
- [x] #3 No partial/cut-off rows at bottom
- [x] #4 All row heights stay consistent (70px)
- [x] #5 Layout remains stable when navigating through queue with next button
- [x] #6 Empty space remains at bottom when fewer tracks than viewport capacity
<!-- AC:END -->


## Implementation Notes

Fixed two issues:
1. Viewport now correctly calculates and displays maximum complete tracks that fit (typically 10-11 tracks)
2. Shuffle mode now properly rotates the shuffled queue to show current track first, followed by remaining tracks in shuffled order

The shuffle bug was that when shuffle was enabled, the code displayed the shuffled queue from the beginning instead of rotating from the current track position. Added rotation logic for shuffle mode to match non-shuffle behavior.
