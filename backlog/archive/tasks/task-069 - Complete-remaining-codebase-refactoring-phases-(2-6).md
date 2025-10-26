---
id: task-069
title: Complete remaining codebase refactoring phases (2-6)
status: Done
assignee:
  - '@lance'
created_date: '2025-10-25 20:08'
updated_date: '2025-10-25 22:19'
labels: []
dependencies: []
---

## Description

Continue the modular refactoring effort to break up large files (>500 LOC) into focused, maintainable modules. Phase 1 (core/player.py) is complete with all 467 tests passing.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Phase 2: Split core/gui.py (1511 LOC) into core/gui/ directory with ~250 LOC per module
- [ ] #2 Phase 3: Split core/db.py (921 LOC) into core/db/ directory with ~450 LOC facade pattern
- [ ] #3 Phase 4: Refactor core/now_playing.py (832 LOC) into focused modules (~450 LOC)
- [ ] #4 Phase 5: Refactor core/controls.py (711 LOC) into focused modules (~450 LOC)
- [ ] #5 Phase 6: Split api/api.py (710 LOC) into api/ directory modules (~450 LOC)
- [ ] #6 All 467+ tests pass after each phase completion
- [ ] #7 No file exceeds 500 LOC (business logic target)
<!-- AC:END -->

## Implementation Notes

Phase 2 complete. Split core/gui.py (1511 LOC) into 6 modules: player_controls (306), progress_status (270), library_search (247), queue_view (709), music_player (23), __init__ (27). NOTE: queue_view.py exceeds 500 LOC target and should be refactored further in a future iteration. All 386 tests passing.

Phase 2 COMPLETE ✓

Split core/gui.py (1511 LOC) into 6 modules:
- player_controls.py (306 LOC)
- progress_status.py (270 LOC)
- library_search.py (247 LOC)
- queue_view.py (709 LOC) ⚠️ exceeds 500 LOC target
- music_player.py (23 LOC)
- __init__.py (27 LOC)

All 386 unit/property tests passing. Original file backed up as core/gui.py.backup.

NOTE: queue_view.py needs further splitting to meet 500 LOC target.
Phases 3-6 split into separate tasks.

Phase 2 COMPLETE ✓

Split core/gui.py (1511 LOC) into 6 modules:
- player_controls.py (306 LOC)
- progress_status.py (270 LOC)
- library_search.py (247 LOC)
- queue_view.py (709 LOC) ⚠️ exceeds 500 LOC target
- music_player.py (23 LOC)
- __init__.py (27 LOC)

Fixed import issues and missing PlayerControls reference in progress_status.py.
All 467 tests passing (5 skipped), including all 80 E2E tests.
Original file backed up as core/gui.py.backup.

NOTE: queue_view.py needs further splitting to meet 500 LOC target.
Phases 3-6 split into separate tasks (070-073).
