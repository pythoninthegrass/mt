---
id: task-119
title: 'Improve progress bar: add track info display and fix seeking'
status: Done
assignee: []
created_date: '2026-01-13 23:53'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - ui
  - player-controls
  - tauri-migration
dependencies: []
priority: medium
ordinal: 81382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The progress bar in the player controls needs improvements:

## Issues

### 1. Missing track info display
- No "Artist - Track Title" shown above the progress bar
- User has no visual indication of what's currently playing in the controls area

### 2. Progress slider visibility
- The scrubber/ball only appears on hover
- Should always be visible when a track is loaded
- Makes it hard to see current position at a glance

### 3. Seeking doesn't work
- Clicking/dragging on the progress bar doesn't actually change track position
- The visual updates but audio position doesn't change

## Implementation

### Track info display
- Add "Artist - Track Title" text above the progress bar
- Truncate with ellipsis if too long
- Show placeholder when no track loaded

### Progress slider
- Make the scrubber ball always visible when a track is playing
- Keep hover effect for slightly larger size on interaction

### Fix seeking
- Verify seek handler calls player.seek() with correct millisecond value
- Check if Tauri audio_seek command is being invoked properly
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Artist - Track Title displayed above progress bar when track is playing
- [x] #2 Progress scrubber ball is always visible when track is loaded
- [x] #3 Clicking on progress bar seeks to that position
- [x] #4 Dragging scrubber seeks in real-time
- [x] #5 Time display updates correctly during seek
<!-- AC:END -->
