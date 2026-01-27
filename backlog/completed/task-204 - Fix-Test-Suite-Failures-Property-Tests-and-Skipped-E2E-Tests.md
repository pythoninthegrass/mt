---
id: task-204
title: 'Fix Test Suite Failures: Property Tests and Skipped E2E Tests'
status: Done
assignee: []
created_date: '2026-01-25 21:11'
updated_date: '2026-01-25 21:43'
labels:
  - testing
  - property-tests
  - e2e
  - rust
  - vitest
dependencies:
  - task-203
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Summary
Fix all pre-existing test failures and skipped tests across the test suite to achieve 100% passing/running status.

## Context
While verifying task-203 (80% test coverage), found several pre-existing failures that need resolution:

### Current Test Status
**Total Test Count:** 906 tests
- **Rust Backend:** 320 tests (317 passed, 3 failed)
- **Vitest Unit:** 179 tests (176 passed, 3 failed + 1 file failed to load)
- **Playwright E2E:** 413 tests (409 passed, 4 skipped)

## Test Failures Breakdown

### 1. Rust Property Test Failures (3 tests)
**Location:** `src-tauri/src/db/queue/queue_props_test.rs`

All 3 failures are in property-based tests:
- `add_to_queue_preserves_count` - Queue count invariant violated
- `add_to_queue_preserves_tracks` - Track preservation invariant violated  
- `queue_operations_never_negative_positions` - Position invariant violated

**Root Cause:** These are property tests using proptest that verify queue operation invariants. They're failing intermittently, suggesting edge cases in queue state management.

### 2. Vitest Property Test Failures (4 tests)
**Location:** `app/frontend/__tests__/queue.props.test.js` and `player.props.test.js`

**Queue Property Tests (3 failures):**
- `toggle shuffle twice returns to original order` 
  - Error: `api.queue.setShuffle is not a function`
- `setLoop updates mode correctly`
  - Error: `api.queue.setLoop is not a function`
- `cycleLoop progresses through modes in order`
  - Error: `api.queue.setLoop is not a function`

**Root Cause:** Mock API setup incomplete - `api.queue.setShuffle` and `api.queue.setLoop` need to be mocked in test environment.

**Player Property Tests (entire file failed):**
- All tests in `player.props.test.js` failed to load
  - Error: `ReferenceError: window is not defined` at `js/stores/player.js:4:20`
  - Line: `const { invoke } = window.__TAURI__?.core ?? { invoke: async () => console.warn(...) };`

**Root Cause:** Player store imports fail in Node.js test environment because `window` is undefined. Need jsdom environment or better mocking.

### 3. Playwright Skipped Tests (4 tests)
**Location:** `app/frontend/tests/drag-and-drop.spec.js`

All skipped tests are drag-and-drop related:
- Line 126: `Playlist Track Reordering › should enable drag reorder in playlist view`
- Line 238: `Playlist Sidebar Reordering › should maintain playlist data integrity during reorder`
- Line 192: `Playlist Sidebar Reordering › should reorder playlists via drag handle`
- Line 46: `Library to Playlist Drag and Drop › should highlight playlist when dragging track over it`

**Root Cause:** Tests likely marked as `.skip()` due to flakiness or incomplete implementation. Need to investigate why they were skipped.

## Implementation Strategy

### Phase 1: Vitest Mocking (Easiest)
1. Add proper API mocks to queue.props.test.js test setup
2. Configure jsdom environment for player.props.test.js OR add window mocking
3. Verify all 179 Vitest tests pass

### Phase 2: Playwright Skipped Tests
1. Review drag-and-drop.spec.js at lines 46, 126, 192, 238
2. Identify why tests were skipped (check git history/comments)
3. Fix underlying issues (likely timing/selectors)
4. Remove `.skip()` and verify tests pass

### Phase 3: Rust Property Tests (Hardest)
1. Enable verbose proptest output to capture failing examples
2. Add shrinking hints to isolate minimal failing cases
3. Fix queue state management bugs revealed by property tests
4. Consider adjusting property test strategies if invariants are too strict

## Priority Rationale
- **High Priority:** These are known, documented failures that reduce confidence in the test suite
- **Impact:** Blocks achieving true 100% passing test status
- **Risk:** Low - all failures are pre-existing and isolated to specific test types
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 320 Rust backend tests pass (0 failures)
- [x] #2 All 179 Vitest unit tests pass (0 failures, all files load)
- [x] #3 All 413 Playwright E2E tests pass (0 skipped)
- [x] #4 Document any false-positive property test invariants that were adjusted
- [x] #5 Update CLAUDE.md with new passing test counts
<!-- AC:END -->
