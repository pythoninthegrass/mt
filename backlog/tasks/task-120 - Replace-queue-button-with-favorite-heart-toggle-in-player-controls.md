---
id: task-120
title: Replace queue button with favorite/heart toggle in player controls
status: Done
assignee: []
created_date: '2026-01-14 01:02'
updated_date: '2026-01-14 04:30'
labels:
  - frontend
  - ui
  - player-controls
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Remove the queue button from the bottom player bar and replace it with a heart/favorite button. The button should:

1. Display an empty heart outline when the current track is not favorited
2. Display a filled heart when the current track is favorited
3. Toggle favorite status on click - add to or remove from liked songs
4. Persist favorite status to the backend database
5. Update the "Liked Songs" library view when tracks are favorited/unfavorited

The heart button should be positioned to the left of the shuffle button in the player controls bar.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Heart button replaces queue button in player controls
- [x] #2 Empty heart shown for non-favorited tracks
- [x] #3 Filled heart shown for favorited tracks
- [x] #4 Click toggles favorite status
- [x] #5 Liked Songs view updates when favorites change
- [x] #6 Favorite status persists across app restarts
<!-- AC:END -->
