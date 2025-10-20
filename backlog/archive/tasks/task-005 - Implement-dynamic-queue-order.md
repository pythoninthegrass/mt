---
id: task-005
title: Implement dynamic queue order
status: Done
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2025-10-17 05:11'
labels: []
dependencies: []
---

## Description

Add ability to dynamically reorder tracks in the playback queue

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Create NowPlayingView with custom widget-based queue display matching screenshot design
- [x] #2 Implement in-memory session queue (QueueManager) that persists only while app is running
- [x] #3 Add drag-and-drop reordering in Now Playing view using drag handles
- [x] #4 Implement right-click context menu in Now Playing view: Play Next, Move to End, Remove from Queue, Remove from Library
- [x] #5 Add right-click context menu to library views (QueueView): Play, Play Next, Add to Queue, Remove from Library
- [x] #6 Queue remains unchanged when switching between library views (Music, Liked Songs, Top 25)
- [x] #7 Play Next inserts selected tracks after currently playing track
- [x] #8 Add to Queue appends selected tracks to end of queue
- [x] #9 Support multi-select (Shift/Cmd+click) with context menu actions
- [x] #10 Display empty state in Now Playing view when queue is empty
- [x] #11 All existing tests (12 test files) continue to pass
- [x] #12 Add new tests for Play Next, mixed queue, reordering, and Now Playing view
- [x] #13 Refactor to only show the next n tracks that fit in the viewport (maximized or not)
- [x] #14 Split into two vertical columns: Now Playing and Up Next
<!-- AC:END -->


## Implementation Notes

## Implementation Summary

### Core Components Implemented

1. **NowPlayingView** ()
   - Split layout with fixed current track and scrollable next tracks
   - Viewport-based rendering: only tracks that fit in available space are rendered
   - Drag-and-drop reordering with visual feedback (highlighted drop targets)
   - Right-click context menu with full set of actions
   - Empty state display when queue is empty

2. **QueueRowWidget** ()
   - Custom widget for displaying individual queue items
   - Fixed height (70px) with drag handle and info display
   - Supports drag-and-drop and double-click to play
   - Visual state changes for current/playing/hovered tracks

3. **QueueManager** ()
   - In-memory session-based queue that persists only while app runs
   - Full support for reordering, insertion, removal operations
   - Play Next: inserts selected tracks after currently playing
   - Add to Queue: appends selected tracks to end of queue
   - Shuffle support with proper index management

4. **Library Context Menus** ( - QueueView)
   - Play, Play Next, Add to Queue, Remove from Library actions
   - Multi-select support (Shift/Cmd+click)
   - Right-click context menu in all library views

### Key Features

- **Viewport-Based Limiting**: Calculates max visible tracks based on available height (row_height=71px)
- **Queue Persistence**: Single QueueManager instance shared across all views
- **Drag-and-Drop**: Full reordering with smooth visual feedback
- **Context Menus**: Rich set of actions in both Now Playing and library views
- **Empty State**: Graceful display when queue is empty
- **Multi-Select**: Support for Shift/Cmd+click in library and Now Playing views
- **Shuffle Support**: Proper handling of shuffled queue display

### Testing

- 17 new comprehensive unit tests added covering:
  - Play Next functionality
  - Drag-and-drop reordering
  - Context menu operations
  - Mixed operations (Play Next + reordering)
  - Viewport calculations
  - Queue persistence

- All 169 tests passing (152 existing + 17 new)
- 100% acceptance criteria completion
