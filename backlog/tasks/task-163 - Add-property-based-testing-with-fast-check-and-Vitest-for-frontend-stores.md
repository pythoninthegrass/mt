---
id: task-163
title: Add property-based testing with fast-check and Vitest for frontend stores
status: Done
assignee: []
created_date: '2026-01-17 09:08'
updated_date: '2026-01-24 22:28'
labels:
  - testing
  - frontend
  - fast-check
  - vitest
dependencies: []
priority: medium
ordinal: 58382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Introduce property-based testing (PBT) for frontend store logic using `dubzzz/fast-check` with Vitest as the test runner. PBT will catch edge cases and invariant violations in stateful logic (queue, player, library stores) that are difficult to cover with traditional example-based tests.

**Why PBT for stores?**
- Stores are high-leverage (bugs affect lots of UI) and deterministic
- Traditional tests cover anticipated edge cases; PBT explores weird combinations automatically
- Sequences of operations (add → reorder → remove → shuffle → playNext) reveal bugs single-step tests miss
- fast-check shrinks failures to minimal counterexamples for easy debugging

**Scope**: Frontend store logic only (no DOM/component testing). Target invariants like index bounds, permutation preservation, and projection consistency.

**Note on reproducibility**: The queue store uses `Math.random()` directly for shuffle. PBT tests should assert seed-independent properties (e.g., permutation preserved, current track stays first). Full shuffle reproducibility would require injecting an RNG, which is out of scope for this task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Vitest is configured in `app/frontend` with a working `npm test` (or `task npm:test`) command
- [x] #2 `fast-check` and `@fast-check/vitest` are installed as dev dependencies
- [x] #3 At least 3 property-based tests exist for queue store invariants (index bounds, permutation preservation under shuffle/unshuffle, operation sequences)
- [x] #4 Test failures include fast-check's `seed` and `path` for reproducible replay
- [x] #5 CI-compatible: tests run in headless mode and fail the build on property violations
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

**Files created:**
- `app/frontend/vitest.config.js` - Vitest configuration for property tests
- `app/frontend/__tests__/queue.store.test.js` - 10 property-based tests for queue store

**Files modified:**
- `app/frontend/package.json` - Added `test` and `test:watch` scripts, installed vitest/fast-check
- `taskfiles/npm.yml` - Added `npm:test` and `npm:test:watch` tasks
- `app/frontend/js/stores/queue.js` - **Bug fix discovered by PBT**: `toggleShuffle()` set `currentIndex = 0` on empty queue

**Property tests implemented (3 categories, 10 tests):**
1. Index Bounds Invariants (4 tests)
   - currentIndex is -1 when queue is empty
   - currentIndex stays within bounds after playIndex
   - currentIndex adjusts correctly after remove
   - currentIndex adjusts correctly after reorder

2. Permutation Preservation (4 tests)
   - shuffle preserves all track IDs (no duplicates, no losses)
   - unshuffle restores original track set
   - current track stays at index 0 after shuffle
   - current track is preserved after unshuffle

3. Operation Sequence Invariants (2 tests)
   - invariants hold after arbitrary operation sequences
   - currentTrack getter is consistent with currentIndex

**Bug found and fixed:**
fast-check discovered that `toggleShuffle()` when disabling shuffle on an empty queue would set `currentIndex = 0` instead of `-1`. The counterexample was: start with 1 track → toggleShuffle (enable) → clear → toggleShuffle (disable). Fixed by checking `items.length > 0` before defaulting to 0.

**Commands:**
- `npm test` or `task npm:test` - Run property tests
- `npm run test:watch` or `task npm:test:watch` - Watch mode
<!-- SECTION:NOTES:END -->
