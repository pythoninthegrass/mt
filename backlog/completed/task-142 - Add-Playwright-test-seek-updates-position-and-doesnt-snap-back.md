---
id: task-142
title: 'Add Playwright test: seek updates position and doesn''t snap back'
status: Done
assignee: []
created_date: '2026-01-16 04:04'
updated_date: '2026-01-24 22:28'
labels:
  - testing
  - playwright
  - playback
  - parity
dependencies:
  - task-139
priority: medium
ordinal: 64382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Purpose
Prevent regressions where seek appears to work but state reverts shortly after. Engine-agnostic contract test.

## Test location
`app/frontend/tests/playback.spec.js`

## Test logic
```javascript
test('seek should move position and remain stable', async ({ page }) => {
  // Arrange
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);
  await page.waitForFunction(() => window.Alpine.store('player').duration > 5);

  const duration = await page.evaluate(() => window.Alpine.store('player').duration);
  const targetFraction = 0.25;
  const expected = duration * targetFraction;
  const tolerance = Math.max(2.0, duration * 0.05);

  // Act: click progress bar at 25%
  const bar = page.locator('[data-testid="player-progressbar"]');
  const box = await bar.boundingBox();
  await page.mouse.click(box.x + box.width * targetFraction, box.y + box.height / 2);

  // Assert: position moved
  await page.waitForTimeout(300);
  const posA = await page.evaluate(() => window.Alpine.store('player').position);
  expect(Math.abs(posA - expected)).toBeLessThanOrEqual(tolerance);

  // Assert: doesn't snap back
  await page.waitForTimeout(400);
  const posB = await page.evaluate(() => window.Alpine.store('player').position);
  expect(Math.abs(posB - expected)).toBeLessThanOrEqual(tolerance);
});
```

## Acceptance Criteria
<!-- AC:BEGIN -->
- Test added to playback.spec.js
- Test passes consistently
- Uses data-testid selectors
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 Test added to playback.spec.js
- [ ] #2 Test passes consistently
- [ ] #3 Uses data-testid selectors
- [ ] #4 Tolerance accounts for varying track durations
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added test 'seek should move position and remain stable (task-142)' to playback.spec.js
<!-- SECTION:NOTES:END -->
