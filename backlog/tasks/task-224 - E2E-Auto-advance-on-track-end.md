---
id: task-224
title: 'E2E: Auto-advance on track end'
status: In Progress
assignee: []
created_date: '2026-01-27 23:36'
updated_date: '2026-01-27 23:49'
labels:
  - e2e
  - playback
  - P0
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Validate that playback automatically advances to the next track when current track finishes. User expectation: no manual intervention needed for continuous playback.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Start playback of a track
- [ ] #2 Simulate or wait for track completion event (audio://progress with position >= duration)
- [ ] #3 Assert currentTrack changes to next track in queue
- [ ] #4 Assert isPlaying remains true
- [ ] #5 Assert queue currentIndex increments
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Test Location
Add to `app/frontend/tests/playback.spec.js` in describe block: `'Playback Parity Tests @tauri'`

### Test Scenario

```javascript
test('should auto-advance to next track when current track ends', async ({ page }) => {
  // 1. Setup: Ensure multiple tracks in queue
  await page.waitForSelector('[data-track-id]', { state: 'visible' });
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);
  
  // 2. Capture initial state
  const initialTrackId = await page.evaluate(() => 
    window.Alpine.store('player').currentTrack?.id
  );
  const initialIndex = await page.evaluate(() => 
    window.Alpine.store('queue').currentIndex
  );
  
  // 3. Verify queue has more tracks
  const queueLength = await page.evaluate(() => 
    window.Alpine.store('queue').items.length
  );
  expect(queueLength).toBeGreaterThan(1);
  
  // 4. Simulate track ending via Tauri event
  await page.evaluate(() => {
    window.__TAURI__.event.emit('audio://track-ended', {});
  });
  
  // 5. Wait for auto-advance
  await page.waitForFunction(
    (prevId) => {
      const current = window.Alpine.store('player').currentTrack;
      return current && current.id !== prevId;
    },
    initialTrackId,
    { timeout: 5000 }
  );
  
  // 6. Assert: Track changed
  const newTrackId = await page.evaluate(() => 
    window.Alpine.store('player').currentTrack?.id
  );
  expect(newTrackId).not.toBe(initialTrackId);
  
  // 7. Assert: Still playing
  const isPlaying = await page.evaluate(() => 
    window.Alpine.store('player').isPlaying
  );
  expect(isPlaying).toBe(true);
  
  // 8. Assert: Queue index incremented
  const newIndex = await page.evaluate(() => 
    window.Alpine.store('queue').currentIndex
  );
  expect(newIndex).toBe(initialIndex + 1);
});

test('should stop playback at end of queue when loop is off', async ({ page }) => {
  await page.waitForSelector('[data-track-id]', { state: 'visible' });
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);
  
  // Disable loop
  await page.evaluate(() => {
    window.Alpine.store('queue').loop = 'none';
  });
  
  // Jump to last track
  const lastIndex = await page.evaluate(() => {
    const queue = window.Alpine.store('queue');
    queue.currentIndex = queue.items.length - 1;
    return queue.currentIndex;
  });
  
  // Simulate track end
  await page.evaluate(() => {
    window.__TAURI__.event.emit('audio://track-ended', {});
  });
  
  await page.waitForTimeout(200);
  
  // Assert: Playback stopped
  const isPlaying = await page.evaluate(() => 
    window.Alpine.store('player').isPlaying
  );
  expect(isPlaying).toBe(false);
});
```

### Key Implementation Details
- `audio://track-ended` event triggers `playNext()` in player store
- Player store line 43-46 shows the listener that calls `queue.playNext()`
- Test both happy path (advance) and edge case (stop at end)

### Event Mechanism
```javascript
// From player.js line 43-46:
this._trackEndedListener = await listen('audio://track-ended', () => {
  this.isPlaying = false;
  Alpine.store('queue').playNext();
});
```
<!-- SECTION:PLAN:END -->
