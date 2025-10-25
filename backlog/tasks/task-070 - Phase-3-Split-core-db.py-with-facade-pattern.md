---
id: task-070
title: 'Phase 3: Split core/db.py with facade pattern'
status: To Do
assignee: []
created_date: '2025-10-25 22:15'
labels: []
dependencies: []
---

## Description

Refactor core/db.py (921 LOC) into core/db/ directory using facade pattern. Split MusicDatabase class into logical domain modules (~450 LOC each).

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create core/db/ directory with facade pattern
- [ ] #2 Split preferences methods to db/preferences.py
- [ ] #3 Split library operations to db/library.py
- [ ] #4 Split queue operations to db/queue.py
- [ ] #5 Split favorites/views to db/favorites.py
- [ ] #6 Create facade in db/__init__.py with MusicDatabase class
- [ ] #7 All tests pass (467+ tests)
- [ ] #8 No file exceeds 500 LOC
<!-- AC:END -->
