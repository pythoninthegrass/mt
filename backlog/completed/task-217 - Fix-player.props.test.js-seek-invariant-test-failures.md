---
id: task-217
title: Fix player.props.test.js seek invariant test failures
status: Done
assignee: []
created_date: '2026-01-27 21:55'
updated_date: '2026-01-27 21:56'
labels:
  - bug
  - frontend
  - tests
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two property-based tests in `__tests__/player.props.test.js` are failing:

1. **"seek with zero duration is safe"** (line 211) - seed=593645856
2. **"seek with invalid values is safe"** (line 220) - seed=-1122206762

Both failures have the same root cause:
```
TypeError: You must provide a Promise to expect() when using .resolves, not 'undefined'.
```

The tests use `.resolves` but the function being tested doesn't return a Promise.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All tests in player.props.test.js pass
- [x] #2 seek invariant tests properly handle sync/async behavior
- [x] #3 Tests remain deterministic with the same seeds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Fix Applied

The `seek()` method in `player.js` doesn't return a Promise - it uses a debounced `setTimeout` internally. The two failing tests incorrectly used `.resolves.not.toThrow()` which expects a Promise.

**Changed in `player.props.test.js`:**
- Line 211: `await expect(store.seek(position)).resolves.not.toThrow()` → `store.seek(position)`
- Line 220: `await expect(store.seek(invalidValue)).resolves.not.toThrow()` → `store.seek(invalidValue)`

The tests still verify the same behavior - seeking with zero duration results in 0 progress, and seeking with invalid values (NaN, Infinity, -Infinity) is handled safely by clamping to valid range.
<!-- SECTION:NOTES:END -->
