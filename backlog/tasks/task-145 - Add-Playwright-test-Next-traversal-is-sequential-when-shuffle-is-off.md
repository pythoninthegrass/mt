---
id: task-145
title: 'Add Playwright test: Next traversal is sequential when shuffle is off'
status: Done
assignee: []
created_date: '2026-01-16 04:04'
updated_date: '2026-01-16 04:18'
labels:
  - testing
  - playwright
  - queue
  - parity
dependencies:
  - task-139
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Purpose
Lock in the sequential traversal contract when shuffle mode is disabled.

## Test location
`app/frontend/tests/queue.spec.js`

## Test logic
```javascript
test('next should advance sequentially when shuffle is off', async ({ page }) => {
  // Arrange: ensure shuffle is off
  await page.evaluate(() => {
    window.Alpine.store('queue').shuffle = false;
  });

  // Start playback at index 0
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);

  const initialIndex = await page.evaluate(() => 
    window.Alpine.store('queue').currentIndex
  );
  expect(initialIndex).toBe(0);

  // Act: click Next
  await page.locator('[data-testid="player-next"]').click();
  await page.waitForTimeout(300);

  // Assert: index advanced by 1
  const newIndex = await page.evaluate(() => 
    window.Alpine.store('queue').currentIndex
  );
  expect(newIndex).toBe(initialIndex + 1);
});
```

## Acceptance Criteria
<!-- AC:BEGIN -->
- Test added to queue.spec.js
- Test verifies sequential index advancement
- Uses data-testid selectors
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 Test added to queue.spec.js
- [ ] #2 Test verifies currentIndex increments by 1
- [ ] #3 Uses data-testid selectors
- [ ] #4 Shuffle is explicitly disabled in test
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added test 'next should advance sequentially when shuffle is off (task-145)' to queue.spec.js
<!-- SECTION:NOTES:END -->
