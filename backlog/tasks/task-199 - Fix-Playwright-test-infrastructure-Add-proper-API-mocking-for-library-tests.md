---
id: task-199
title: Fix Playwright test infrastructure - Add proper API mocking for library tests
status: In Progress
assignee: []
created_date: '2026-01-25 01:17'
updated_date: '2026-01-25 04:52'
labels:
  - testing
  - playwright
  - infrastructure
  - technical-debt
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix 118 failing Playwright library tests by implementing proper API mocking infrastructure.

## Problem

Playwright tests run in browser-only mode (Vite dev server at `http://localhost:5173`) without Tauri backend. The `api.js` client falls back to HTTP requests (`http://127.0.0.1:8765/api/library`), but no backend is running at that address during tests.

**Current failures:**
- 118 tests timeout waiting for `[data-track-id]` elements
- All library-dependent tests fail: library.spec.js, missing-tracks.spec.js, sorting-ignore-words.spec.js
- 170 non-library tests pass correctly

## Root Cause

Tests rely on `api.library.getTracks()` returning data, but:
1. `window.__TAURI__` is undefined in browser tests
2. HTTP fallback tries to reach `http://127.0.0.1:8765` (no backend running)
3. No mock data or fixtures provided for tests

## Proposed Solution

Implement one of these approaches:

### Option 1: Mock API Responses (Recommended)
Add test fixtures and intercept API calls:
```javascript
// tests/fixtures/library-fixtures.js
export const mockTracks = [
  { id: 1, title: 'Track 1', artist: 'Artist 1', album: 'Album 1', ... },
  { id: 2, title: 'Track 2', artist: 'Artist 2', album: 'Album 2', ... },
  // ...
];

// In test setup
await page.route('**/api/library*', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({ tracks: mockTracks, total: mockTracks.length })
  });
});
```

### Option 2: Mock Tauri Commands
Inject mock `window.__TAURI__` before Alpine.js loads:
```javascript
await page.addInitScript(() => {
  window.__TAURI__ = {
    core: {
      invoke: async (cmd, args) => {
        if (cmd === 'library_get_all') {
          return { tracks: [...], total: 300 };
        }
        // ...
      }
    }
  };
});
```

### Option 3: Real Backend for Tests
Start Python backend or Tauri app during test runs (slower but more accurate).

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 118 failing library tests pass
- [ ] #2 Mock data includes representative tracks with all required fields
- [ ] #3 Tests remain fast (no real backend if Option 1/2 chosen)
- [ ] #4 Mocking approach is documented for future test additions
- [ ] #5 CI/CD pipeline updated if needed
<!-- SECTION:DESCRIPTION:END -->
<!-- AC:END -->
