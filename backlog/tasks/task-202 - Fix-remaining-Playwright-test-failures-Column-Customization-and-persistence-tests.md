---
id: task-202
title: >-
  Fix remaining Playwright test failures (Column Customization and persistence
  tests)
status: To Do
assignee: []
created_date: '2026-01-25 07:36'
labels:
  - testing
  - playwright
  - technical-debt
dependencies:
  - task-199
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem

After implementing API mocking infrastructure (task-199), 10 tests still fail for reasons unrelated to mocking:

### Column Customization Tests (8 failures)

These tests depend on specific track string lengths for column width auto-fit calculations:

- `should auto-fit column to content width and adjust neighbor`
- `should increase column width on auto-fit for Artist column`
- `should increase column width on auto-fit for Album column`
- `auto-fit Artist should persist width (no flash-and-revert)`
- `auto-fit Album should persist width (no flash-and-revert)`
- `should persist column settings to localStorage`
- `should restore column settings on page reload`
- `should persist column order to localStorage`

**Root cause:** Mock track titles/artists/albums are shorter than expected by tests, causing auto-fit width calculations to differ.

### Sorting Persistence Tests (2 failures)

- `should NOT strip prefixes when ignore words is disabled`
- `should persist ignore words settings across page reload`

**Root cause:** Timing issues with localStorage state persistence across page reloads.

## Proposed Solutions

### For Column Customization:
1. **Option A:** Adjust mock data to include longer strings matching expected widths
2. **Option B:** Modify tests to be more flexible about exact width values
3. **Option C:** Use specific mock tracks with known string lengths for these tests

### For Persistence Tests:
1. Investigate localStorage timing during page reload
2. Add explicit waits or verification steps
3. Consider using Playwright's `storageState` for persistence testing

## Files to Investigate

- `app/frontend/tests/library.spec.js` (lines 576-1360)
- `app/frontend/tests/sorting-ignore-words.spec.js` (lines 191, 264)
- `app/frontend/tests/fixtures/mock-library.js` (mock data generation)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 8 Column Customization tests pass
- [ ] #2 Both sorting persistence tests pass
- [ ] #3 No regressions in other tests
- [ ] #4 Mock data adjustments documented if made
<!-- AC:END -->
