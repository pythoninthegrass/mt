---
id: task-121
title: Auto-scroll and highlight currently playing track in library view
status: Done
assignee: []
created_date: '2026-01-14 01:36'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - ui
  - library-view
  - playback
dependencies: []
priority: medium
ordinal: 80382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When a track starts playing, the library view should automatically scroll to show that track and highlight it visually. Currently, the only indication of the playing track is a small play icon (▶) next to the title. This task adds:

1. **Auto-scroll**: When playback moves to a new track (via next/previous, queue advancement, or direct selection), scroll the library view to ensure the playing track is visible
2. **Visual highlight**: Apply a distinct background highlight to the currently playing track row (in addition to the existing ▶ icon)
3. **Smooth scrolling**: Use smooth scroll behavior for a polished feel
4. **Edge cases**: Handle cases where the playing track is not in the current filtered view (e.g., search results don't include it)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Library view auto-scrolls to currently playing track when playback changes
- [x] #2 Playing track row has distinct visual highlight (background color)
- [x] #3 Scroll behavior is smooth, not jarring
- [x] #4 Works with next/previous navigation
- [x] #5 Works when track advances automatically from queue
- [x] #6 Handles filtered views gracefully (no scroll if track not visible in filter)
<!-- AC:END -->
