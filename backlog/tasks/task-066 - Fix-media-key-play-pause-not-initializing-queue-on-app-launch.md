---
id: task-066
title: Fix media key play/pause not initializing queue on app launch
status: In Progress
assignee: []
created_date: '2025-10-22 03:07'
updated_date: '2025-10-22 03:08'
labels: []
dependencies: []
priority: high
ordinal: 500
---

## Description

When the app is first launched and the media key play/pause is pressed without first double-clicking a track in the library, it doesn't properly queue the entire music library. This also appears to break shuffle functionality. The expected behavior is that pressing play/pause should initialize the queue with the library content similar to how double-clicking a track does.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Pressing media key play/pause after app launch should queue the library
- [ ] #2 Shuffle should work correctly when playback is initiated via media key
- [ ] #3 Behavior should match the queue initialization that occurs when double-clicking a library track
- [ ] #4 Previous/next navigation should work correctly after media key play/pause
<!-- AC:END -->
