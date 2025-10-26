---
id: task-070
title: 'Phase 3: Split core/db.py with facade pattern'
status: Done
assignee: []
created_date: '2025-10-25 22:15'
updated_date: '2025-10-25 22:38'
labels: []
dependencies: []
---

## Description

Refactor core/db.py (921 LOC) into core/db/ directory using facade pattern. Split MusicDatabase class into logical domain modules (~450 LOC each).

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Create core/db/ directory with facade pattern
- [x] #2 Split preferences methods to db/preferences.py
- [x] #3 Split library operations to db/library.py
- [x] #4 Split queue operations to db/queue.py
- [x] #5 Split favorites/views to db/favorites.py
- [x] #6 Create facade in db/__init__.py with MusicDatabase class
- [x] #7 All tests pass (467+ tests)
- [x] #8 No file exceeds 500 LOC
<!-- AC:END -->

## Implementation Notes

Phase 3 complete. Split core/db.py (921 LOC) into 5 focused modules:
- preferences.py (68 LOC): User settings, preferences, UI state
- queue.py (27 LOC): Playback queue operations
- favorites.py (111 LOC): Favorites and special views
- library.py (166 LOC): Music library, tracks, metadata
- __init__.py (119 LOC): Facade providing backwards-compatible interface

All modules under 500 LOC. All 467 tests pass (386 unit/property, 81 E2E). No import changes needed due to facade pattern.
