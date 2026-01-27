---
id: task-218
title: Fix library.store.test.js _stripIgnoredPrefix property test failure
status: Done
assignee: []
created_date: '2026-01-27 22:08'
updated_date: '2026-01-27 22:10'
labels:
  - bug
  - frontend
  - tests
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Property-based test in `__tests__/library.store.test.js` is failing:

**Test:** "result length is <= original length" (seed=-2031172996)
**Counterexample:** `[" ", []]` (single space string, empty prefix array)

```
AssertionError: expected 1 to be less than or equal to 0
```

The `_stripIgnoredPrefix` function appears to have an edge case where a whitespace-only string with no prefixes returns a result longer than expected (trimmed length vs original length issue).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All tests in library.store.test.js pass
- [x] #2 Edge case with whitespace-only input is handled correctly
- [x] #3 Test remains deterministic with the same seed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Root Cause

The test file's `_stripIgnoredPrefix` implementation had a bug in its early return path. When `ignoreWords` is empty or null, it returned `value || ''` without trimming, but the actual `library.js` implementation at line 265 returns `String(value || '').trim()`.

## Counterexample Analysis
- Input: `value = " "` (single space), `ignoreWords = []`
- Bug: Test returned `" "` (length 1)
- Expected: `"".trim() = ""` (length 0)
- Assertion `1 <= 0` failed

## Fix
Changed test file line 41 from:
```javascript
return value || '';
```
to:
```javascript
return String(value || '').trim();
```

This aligns the test's mock implementation with the actual library.js implementation.
<!-- SECTION:NOTES:END -->
