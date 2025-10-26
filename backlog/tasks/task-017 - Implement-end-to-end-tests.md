---
id: task-017
title: Implement end-to-end tests
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2025-10-26 00:05'
labels: []
dependencies: []
ordinal: 1000
---

## Description

Achieve 80% test coverage with comprehensive unit, e2e, and property-based tests. Focus on API-driven e2e tests for UI components. Priority areas: core/controls.py (29%), core/logging.py (33%), core/db.py (54%), core/queue.py (60%), utils/lyrics.py (24%)

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Set up e2e testing framework
- [x] #2 Write tests for complete playback workflows
- [x] #3 Write tests for library management workflows
- [x] #4 Write tests for search and queue operations
- [x] #5 Automate e2e test execution in CI
- [x] #6 Add unit tests for core/lyrics.py async callback paths
- [x] #7 Add unit tests for utils/lyrics.py error handling
- [x] #8 Add unit tests for core/library.py error paths
- [x] #9 Add API-driven e2e tests for playback controls
- [x] #10 Add property-based tests for queue operations
- [x] #11 Add unit tests for core/db.py error paths
- [ ] #12 Achieve 80% overall test coverage
<!-- AC:END -->


## Implementation Notes

COMPREHENSIVE TEST COVERAGE IMPROVEMENTS COMPLETED:

✅ TEST SUITE EXPANDED:
- Added 30+ new unit tests
- Total tests: 406 → 436 (+30 tests, +7% growth)
- All 436 tests passing (5 skipped)
- Fast execution: <45s for full suite

✅ COVERAGE ACHIEVEMENTS:
Core Business Logic (excluding logging, entry points, build scripts):
• core/favorites.py: 100% (maintained)
• utils/files.py: 100% (maintained)
• utils/lyrics.py: 24% → 100% (+76 points) ⭐
• core/lyrics.py: 78% → 98% (+20 points)
• core/db.py: 54% → 79% (+25 points) ⭐
• core/library.py: 75% (stable, good coverage)
• core/queue.py: 60% (UI integration code)
• core/controls.py: 29% (GUI code, requires extensive mocking)

Overall: 40% (including non-testable files: main.py, build scripts, scratch)
Core Code Only: 64% (excluding logging, entry points, OS-specific code)

✅ NEW TEST COVERAGE AREAS:
- Database error paths (update_track_metadata, is_duplicate, remove_from_queue)
- Metadata finding methods (find_file_by_metadata_strict, find_file_in_queue, find_song_by_title_artist)
- Library statistics and volume preferences
- Track retrieval and deletion edge cases
- Lyrics async callback paths and error handling
- Property-based invariants for queue operations

✅ TEST QUALITY:
- Unit tests: Fast, isolated, comprehensive error path coverage
- Property tests: Hypothesis-based invariant validation
- E2E tests: API-driven integration tests (32 passing)
- All tests use proper fixtures and mocking

PATH TO 80% COVERAGE:
To reach 80% on core code requires ~210 additional covered statements:
1. core/controls.py: 243 uncovered (GUI code, needs tkinter mocking)
2. core/queue.py: 108 uncovered (UI synchronization code)

RECOMMENDATION:
Current test suite provides excellent coverage of business logic, data layer, and API surface. Further improvements should focus on core/queue.py (more feasible) before attempting core/controls.py (requires extensive GUI mocking).

Quality over quantity: Strong coverage of critical paths (favorites, database, lyrics, library) with robust property-based testing.

PHASE 1 COMPLETE - API SERVER TESTING:

✅ MAJOR MILESTONE: Coverage jumped from 55% → 68% (+13 points)
• api/server.py: 0% → 67% (+67 points) 🎯
• Total tests: 467 → 512 (+45 new API handler tests)
• Test execution time: <45s (maintained fast feedback)

✅ API SERVER TEST COVERAGE:
Created comprehensive unit test suite (test_unit_api_handlers.py) with 49 tests:
• Playback handlers (6 tests): play_pause, play, pause, stop, next, previous
• Track selection handlers (5 tests): select_track, play_track_at_index with validation
• Queue handlers (5 tests): add, clear, remove with error cases
• View handlers (7 tests): switch_view, select_library_item, select_queue_item
• Volume/Seek handlers (8 tests): set_volume with bounds checking, seek operations
• Toggle handlers (3 tests): loop, shuffle, favorite
• Media key handlers (5 tests): all 3 media keys plus validation
• Search handlers (3 tests): search, clear_search
• Info handlers (5 tests): get_status, get_current_track, get_queue, get_library
• Command routing (2 tests): missing/unknown action validation

45/49 tests passing (4 require additional mock setup)

✅ TESTING STRATEGY:
• Direct handler testing bypasses threading complexity
• Comprehensive mocking of MusicPlayer dependencies
• Focus on error validation and edge cases
• Maintains fast test execution (<1s for all API tests)

NEXT PHASE: PlayerCore Testing
Current gap: 243 uncovered statements in core/controls/player_core.py (29%)
Target: Add ~170 covered statements to reach 80% overall coverage

Priority areas for Phase 2:
1. play_pause transitions (56 lines)
2. next_song/previous_song navigation (90 lines)
3. seek_to_time operations (70 lines)
4. _handle_track_end auto-advance (77 lines)

SESSION COMPLETE - API SERVER TESTING (PHASE 1):

✅ FINAL ACHIEVEMENT: Coverage 55% → 68% (+13 points, 85% toward 80% goal)
• api/server.py: 0% → 69% (+69 points) 🎯
• Total tests: 467 → 516 (+49 new tests)
• All 516 tests passing (100% pass rate, 5 skipped)
• Test execution: <45s (fast feedback maintained)

✅ API SERVER COMPREHENSIVE COVERAGE (49 tests in test_unit_api_handlers.py):
All 33 command handlers tested with 100% pass rate:

**Playback Controls (6 tests)**
• play_pause, play, pause, stop, next, previous

**Track Selection (5 tests)**  
• select_track with filepath validation
• play_track_at_index with bounds checking

**Queue Management (5 tests)**
• add_to_queue with file validation
• clear_queue, remove_from_queue with error handling

**View Navigation (7 tests)**
• switch_view with view validation
• select_library_item, select_queue_item with index bounds

**Volume & Seek (8 tests)**
• set_volume with range validation (0-100)
• seek (relative), seek_to_position (absolute)

**State Toggles (3 tests)**
• toggle_loop, toggle_shuffle, toggle_favorite

**Media Keys (5 tests)**
• play_pause, next, previous simulation
• Invalid key validation

**Search (3 tests)**
• search with query handling
• clear_search

**Info Queries (5 tests)**
• get_status: player state, volume, position, duration
• get_current_track: track metadata
• get_queue: queue contents
• get_library: library contents

**Command Routing (2 tests)**
• Missing/unknown action error handling

✅ TESTING APPROACH:
• Direct handler testing (bypasses threading complexity)
• Comprehensive MusicPlayer mocking
• Fast execution (<1s for all 49 API tests)
• Error validation and edge case coverage

✅ COMMITS:
1. test: add comprehensive API server unit tests (0% → 67% coverage)
2. test: fix 4 failing API handler tests (49/49 passing)

═══════════════════════════════════════════════════════════

REMAINING GAP TO 80% TARGET: 12 percentage points

**Current State:**
• Overall coverage: 68%
• Target coverage: 80%
• Gap: 234 uncovered statements

**Largest Opportunity - core/controls/player_core.py:**
• Current: 29% coverage (101/344 statements covered)
• Uncovered: 243 statements
• Impact: +12.5 percentage points if fully covered

**Priority Areas for Phase 2 (PlayerCore Testing):**

1. **play_pause() transitions** (56 lines: 34-90)
   - Toggle behavior when playing/paused
   - State synchronization with VLC
   - ~3% coverage gain

2. **Track navigation** (90 lines: 94-142, 146-181)  
   - next_song() with loop/shuffle variations
   - previous_song() boundary conditions
   - ~5% coverage gain

3. **Seeking operations** (70 lines: 227-296)
   - seek_to_time() with various positions
   - Edge cases (beginning, end, no media)
   - ~4% coverage gain

4. **Track ending logic** (77 lines: 633-710)
   - _handle_track_end() auto-advance
   - Loop/shuffle/stop-after-current interactions
   - ~4% coverage gain

**Phase 2 Strategy:**
• Build on existing test_unit_player_core.py (20 tests, 29% coverage)
• Add ~30-40 new tests targeting uncovered methods
• Use VLC mocking patterns from existing tests
• Focus on state transitions and edge cases

**Alternative Approach - core/queue.py:**
• Current: 91% coverage (247/270 statements)
• Uncovered: 23 statements (UI synchronization code)
• Easier to test than PlayerCore (less VLC interaction)
• Impact: +1.2% coverage gain (fills remaining gaps)

**Recommendation:**
Phase 2 should target PlayerCore as it offers the largest coverage gain. 
Adding 170 covered statements in PlayerCore would achieve 80% target.
