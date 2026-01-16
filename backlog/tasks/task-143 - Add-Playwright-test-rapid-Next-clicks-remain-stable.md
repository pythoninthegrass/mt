---
id: task-143
title: 'Add Playwright test: rapid Next clicks remain stable'
status: To Do
assignee: []
created_date: '2026-01-16 04:04'
labels:
  - testing
  - playwright
  - playback
  - parity
  - stability
dependencies:
  - task-139
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Purpose
Prevent state wedging from repeated Next operations. UI-level replacement for the old Python concurrency tests.

## Test location
`app/frontend/tests/playback.spec.js`

## Test logic
```javascript
test('rapid next should not break playback state', async ({ page }) => {
  // Arrange
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);

  // Act: click Next 15 times rapidly
  const nextBtn = page.locator('[data-testid="player-next"]');
  for (let i = 0; i < 15; i++) {
    await nextBtn.click();
    await page.waitForTimeout(75);
  }

  // Assert: player state is coherent
  const player = await page.evaluate(() => window.Alpine.store('player'));
  expect(player.currentTrack).toBeTruthy();
  expect(player.currentTrack.id).toBeTruthy();
  expect(player.isPlaying).toBe(true);
});
```

## Notes
- 15 iterations is enough to catch race conditions without making tests slow
- 75ms delay between clicks simulates rapid but realistic user behavior

## Acceptance Criteria
<!-- AC:BEGIN -->
- Test added to playback.spec.js
- Test passes consistently
- Uses data-testid selectors
- No false positives from legitimate end-of-queue scenarios
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 Test added to playback.spec.js
- [ ] #2 Test passes consistently
- [ ] #3 Uses data-testid selectors
- [ ] #4 Handles edge cases gracefully
<!-- AC:END -->
