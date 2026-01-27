---
id: task-222
title: 'E2E: Shuffle-only full cycle with no repeats'
status: In Progress
assignee: []
created_date: '2026-01-27 23:36'
updated_date: '2026-01-27 23:49'
labels:
  - e2e
  - playback
  - queue
  - P0
dependencies:
  - task-213
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Validate that shuffle mode plays all tracks exactly once before any repeat. User expectation: when shuffle is enabled (loop off), every track plays once in random order with no duplicates until the queue is exhausted.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Enable shuffle mode with loop OFF
- [ ] #2 Play through entire queue programmatically (simulate track-end events)
- [ ] #3 Assert each track ID appears exactly once in play history
- [ ] #4 Assert no track repeats before queue exhaustion
- [ ] #5 Test with library of 10+ tracks
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Test Location
Add to `app/frontend/tests/queue.spec.js` in a new describe block: `'Shuffle Full Cycle Tests @tauri'`

### Test Scenario

```javascript
test('shuffle mode should play all tracks exactly once before any repeat', async ({ page }) => {
  // 1. Setup: Load library with 10+ tracks
  await page.waitForSelector('[data-track-id]', { state: 'visible' });
  
  // 2. Start playback to populate queue
  await doubleClickTrackRow(page, 0);
  await waitForPlaying(page);
  
  // 3. Enable shuffle, disable loop
  await page.evaluate(() => {
    window.Alpine.store('queue').shuffle = true;
    window.Alpine.store('queue').loop = 'none';
  });
  
  // 4. Get queue length
  const queueLength = await page.evaluate(() => 
    window.Alpine.store('queue').items.length
  );
  
  // 5. Play through entire queue, recording played track IDs
  const playedIds = new Set();
  
  for (let i = 0; i < queueLength; i++) {
    const currentId = await page.evaluate(() => 
      window.Alpine.store('queue').currentTrack?.id
    );
    
    // Assert: No duplicate plays
    expect(playedIds.has(currentId)).toBe(false);
    playedIds.add(currentId);
    
    // Simulate track end (skip to next)
    if (i < queueLength - 1) {
      await page.evaluate(() => {
        window.__TAURI__.event.emit('audio://track-ended', {});
      });
      await page.waitForTimeout(100);
    }
  }
  
  // 6. Assert: All tracks played exactly once
  expect(playedIds.size).toBe(queueLength);
});
```

### Key Implementation Details
- Use `window.__TAURI__.event.emit('audio://track-ended', {})` to simulate track completion
- Track played IDs using a Set to detect duplicates efficiently
- Loop = 'none' ensures playback stops after last track (no wrap-around)
- Need to wait briefly after each track-ended event for queue state to update

### Selectors/APIs
- `window.Alpine.store('queue').currentTrack?.id` - Get current track ID
- `window.Alpine.store('queue').items.length` - Get queue size
- `window.Alpine.store('queue').shuffle = true` - Enable shuffle
- `window.__TAURI__.event.emit('audio://track-ended', {})` - Trigger auto-advance
<!-- SECTION:PLAN:END -->
