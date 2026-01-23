---
id: task-195
title: Fix 6 failing E2E tests in library.spec.js and sidebar.spec.js
status: To Do
assignee: []
created_date: '2026-01-23 05:20'
labels:
  - testing
  - e2e
  - playwright
  - bug
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
There are 6 pre-existing failing E2E tests related to playlist drag reordering and metadata editor navigation. These tests fail consistently and need investigation and fixes.

**Failing Tests:**

1. `library.spec.js:1770` - Playlist Feature Parity - Library Browser (task-150) › AC#6: drag reorder in playlist view shows drag handle and sets state
2. `library.spec.js:2156` - Metadata Editor Navigation (task-166) › should show track position indicator with correct format
3. `library.spec.js:2181` - Metadata Editor Navigation (task-166) › should navigate to next track with ArrowRight key
4. `library.spec.js:2313` - Metadata Editor Navigation (task-166) › should navigate using arrow buttons
5. `library.spec.js:2375` - Metadata Editor Navigation (task-166) › arrow keys should work even when input is focused
6. `sidebar.spec.js:644` - Playlist Feature Parity (task-150) › dragging playlist should show opacity change

**Common Failure Pattern:**

The sidebar.spec.js test expects `opacity-50` class during drag but the element has different classes:
```
Expected substring: "opacity-50"
Received string: "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-all duration-150 select-none hover:bg-muted/70 text-foreground/80 bg-card shadow-lg z-10 relative"
```

**Investigation Needed:**
- Check if drag state is being properly set in the sidebar component
- Verify the opacity class is conditionally applied based on drag state
- Review if the metadata editor navigation implementation matches test expectations
- Check if tests need updating vs implementation needs fixing
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 6 failing tests pass
- [ ] #2 No regressions in other tests
- [ ] #3 Root cause documented in implementation notes
<!-- AC:END -->
