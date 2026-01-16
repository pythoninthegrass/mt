---
id: task-144
title: 'Add Playwright test: double-click populates queue with entire library'
status: Done
assignee: []
created_date: '2026-01-16 04:04'
updated_date: '2026-01-16 04:18'
labels:
  - testing
  - playwright
  - queue
  - parity
  - foundation
dependencies:
  - task-140
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Purpose
Lock in the core queue construction contract: double-clicking a track in the library should populate the queue with the **entire library** (not filtered view).

## Test location
`app/frontend/tests/queue.spec.js`

## Test logic
```javascript
test('double-click should populate queue with entire library', async ({ page }) => {
  // Arrange: apply a search filter to reduce visible tracks
  await page.waitForSelector('[data-track-id]', { state: 'visible' });
  
  const searchInput = page.locator('input[placeholder="Search"]');
  await searchInput.fill('specific');
  await page.waitForTimeout(500);

  // Get counts
  const totalLibraryCount = await page.evaluate(() => 
    window.Alpine.store('library').tracks.length
  );
  const filteredCount = await page.evaluate(() => 
    window.Alpine.store('library').filteredTracks.length
  );
  
  // Sanity check: filter actually reduced visible tracks
  expect(filteredCount).toBeLessThan(totalLibraryCount);

  // Act: double-click first visible track
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);

  // Assert: queue contains ENTIRE library, not just filtered
  const queueLength = await page.evaluate(() => 
    window.Alpine.store('queue').items.length
  );
  expect(queueLength).toBe(totalLibraryCount);
});
```

## Depends on
- Task 140 (fix handleDoubleClick to use library.tracks)

## Acceptance Criteria
<!-- AC:BEGIN -->
- Test added to queue.spec.js
- Test verifies queue length equals total library, not filtered
- Test passes after task-140 implementation
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 Test added to queue.spec.js
- [ ] #2 Test verifies queue = entire library
- [ ] #3 Test passes after task-140 is complete
- [ ] #4 Test fails if filtered behavior is restored (regression guard)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added test 'double-click should populate queue with entire library (task-144)' to queue.spec.js
<!-- SECTION:NOTES:END -->
