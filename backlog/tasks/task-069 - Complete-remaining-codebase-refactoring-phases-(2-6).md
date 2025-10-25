---
id: task-069
title: Complete remaining codebase refactoring phases (2-6)
status: To Do
assignee: []
created_date: '2025-10-25 20:08'
labels: []
dependencies: []
---

## Description

Continue the modular refactoring effort to break up large files (>500 LOC) into focused, maintainable modules. Phase 1 (core/player.py) is complete with all 467 tests passing.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Phase 2: Split core/gui.py (1511 LOC) into core/gui/ directory with ~250 LOC per module
- [ ] #2 Phase 3: Split core/db.py (921 LOC) into core/db/ directory with ~450 LOC facade pattern
- [ ] #3 Phase 4: Refactor core/now_playing.py (832 LOC) into focused modules (~450 LOC)
- [ ] #4 Phase 5: Refactor core/controls.py (711 LOC) into focused modules (~450 LOC)
- [ ] #5 Phase 6: Split api/api.py (710 LOC) into api/ directory modules (~450 LOC)
- [ ] #6 All 467+ tests pass after each phase completion
- [ ] #7 No file exceeds 500 LOC (business logic target)
<!-- AC:END -->
