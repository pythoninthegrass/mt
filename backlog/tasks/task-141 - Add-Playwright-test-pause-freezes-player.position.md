---
id: task-141
title: 'Add Playwright test: pause freezes player.position'
status: To Do
assignee: []
created_date: '2026-01-16 04:04'
labels:
  - testing
  - playwright
  - playback
  - parity
dependencies:
  - task-139
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Purpose
Prevent regressions where UI shows "paused" but position continues advancing. This is a generalized interface contract test (engine-agnostic).

## Test location
`app/frontend/tests/playback.spec.js`

## Test logic
```javascript
test('pause should freeze position', async ({ page }) => {
  // Arrange: start playback
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);
  await page.waitForFunction(() => window.Alpine.store('player').position > 0.5);

  // Act: pause
  await page.locator('[data-testid="player-playpause"]').click();
  await waitForPaused(page);

  // Assert: position does not advance
  const pos0 = await page.evaluate(() => window.Alpine.store('player').position);
  await page.waitForTimeout(750);
  const pos1 = await page.evaluate(() => window.Alpine.store('player').position);

  expect(pos1 - pos0).toBeLessThanOrEqual(0.25);
});
```

## Tolerance
- 0.25 seconds is tight but usually safe
- If flaky, can loosen to 0.5 seconds

## Acceptance Criteria
<!-- AC:BEGIN -->
- Test added to playback.spec.js
- Test passes consistently
- Uses data-testid selectors (depends on task-138)
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 Test added to playback.spec.js
- [ ] #2 Test passes consistently across browsers
- [ ] #3 Uses data-testid selectors
- [ ] #4 Tolerance is appropriate (0.25-0.5s)
<!-- AC:END -->
