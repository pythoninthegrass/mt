---
id: task-063
title: Fix Now Playing viewport to show maximum complete tracks
status: To Do
assignee: []
created_date: '2025-10-21 22:49'
labels: []
dependencies: []
---

## Description

The Now Playing view should calculate and display the maximum number of complete track rows that fit in the viewport. Currently showing only 3-4 tracks when there's room for 6-8. Each track row is 71px (70px + 1px padding). Need to properly calculate available viewport height and show all tracks that completely fit without partial rows at bottom.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Calculate viewport height correctly (total height - current section 100px - divider 1px - next label 30px)
- [ ] #2 Show maximum number of complete 71px rows that fit
- [ ] #3 No partial/cut-off rows at bottom
- [ ] #4 All row heights stay consistent (70px)
- [ ] #5 Layout remains stable when navigating through queue with next button
- [ ] #6 Empty space remains at bottom when fewer tracks than viewport capacity
<!-- AC:END -->
