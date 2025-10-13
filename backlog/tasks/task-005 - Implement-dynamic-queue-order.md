---
id: task-005
title: Implement dynamic queue order
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2025-10-13 05:08'
labels: []
dependencies: []
---

## Description

Add ability to dynamically reorder tracks in the playback queue

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create NowPlayingView with custom widget-based queue display matching screenshot design
- [ ] #2 Implement in-memory session queue (QueueManager) that persists only while app is running
- [ ] #3 Add drag-and-drop reordering in Now Playing view using drag handles
- [ ] #4 Implement right-click context menu in Now Playing view: Play Next, Move to End, Remove from Queue, Remove from Library
- [ ] #5 Add right-click context menu to library views (QueueView): Play, Play Next, Add to Queue, Remove from Library
- [ ] #6 Queue remains unchanged when switching between library views (Music, Liked Songs, Top 25)
- [ ] #7 Play Next inserts selected tracks after currently playing track
- [ ] #8 Add to Queue appends selected tracks to end of queue
- [ ] #9 Support multi-select (Shift/Cmd+click) with context menu actions
- [ ] #10 Display empty state in Now Playing view when queue is empty
- [ ] #11 All existing tests (12 test files) continue to pass
- [ ] #12 Add new tests for Play Next, mixed queue, reordering, and Now Playing view
- [ ] #13 Refactor to only show the next n tracks that fit in the viewport (maximized or not)
- [ ] #14 Split into two vertical columns: Now Playing and Up Next
<!-- AC:END -->


## Implementation Notes

Implementation plan revised based on commit 95ad5c2c analysis:
- Session-based in-memory queue (no database persistence)
- Separate NowPlayingView with custom widgets for queue visualization
- Keep existing QueueView (Treeview) for library browsing
- Context menu in both views: Play Next, Add to Queue, Remove from Library
- Drag-and-drop reordering in Now Playing view with drag handles only
- Queue persists only during app session, cleared on close
- View switching does not affect queue
- Users can mix tracks from different sources (Music, Liked Songs, Top 25)
