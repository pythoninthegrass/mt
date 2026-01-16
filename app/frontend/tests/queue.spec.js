import { test, expect } from '@playwright/test';
import {
  waitForAlpine,
  getAlpineStore,
  getQueueItems,
  waitForPlaying,
  doubleClickTrackRow,
  callAlpineStoreMethod,
} from './fixtures/helpers.js';

test.describe('Queue Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('should add track to queue when playing', async ({ page }) => {
    // Get initial queue length
    const initialQueueItems = await getQueueItems(page);
    const initialLength = initialQueueItems.length;

    // Play a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Verify queue has items
    const updatedQueueItems = await getQueueItems(page);
    expect(updatedQueueItems.length).toBeGreaterThan(initialLength);
  });

  test('should remove track from queue', async ({ page }) => {
    // Add tracks to queue by playing
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Switch to Now Playing view to see queue
    await page.click('button:has-text("Now Playing")').catch(() => {
      // If button doesn't exist with text, try clicking the player area
      page.click('[x-data="nowPlayingView"]').catch(() => {});
    });

    // Wait for queue to be visible
    await page.waitForSelector('.queue-item', { state: 'visible', timeout: 5000 }).catch(() => {
      // Queue might not be visible in current view, switch to queue view
    });

    // Get initial queue length
    const initialQueueItems = await getQueueItems(page);
    const initialLength = initialQueueItems.length;

    if (initialLength > 1) {
      // Click remove button on first queue item (not currently playing)
      const removeButtons = page.locator('.queue-item button[title="Remove from queue"]');
      const count = await removeButtons.count();
      if (count > 1) {
        await removeButtons.nth(1).click();

        // Wait for queue to update
        await page.waitForFunction(
          (length) => {
            return window.Alpine.store('queue').items.length < length;
          },
          initialLength,
          { timeout: 5000 }
        );

        // Verify queue length decreased
        const updatedQueueItems = await getQueueItems(page);
        expect(updatedQueueItems.length).toBe(initialLength - 1);
      }
    }
  });

  test('should clear queue', async ({ page }) => {
    // Add tracks to queue
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Call clear on queue store
    await callAlpineStoreMethod(page, 'queue', 'clear');

    // Wait for queue to clear
    await page.waitForFunction(() => {
      return window.Alpine.store('queue').items.length === 0;
    }, null, { timeout: 5000 });

    // Verify queue is empty
    const queueItems = await getQueueItems(page);
    expect(queueItems.length).toBe(0);
  });

  test('should navigate through queue with next/prev buttons', async ({ page }) => {
    // Add multiple tracks to queue by selecting and playing
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Select multiple tracks (Shift+click)
    await page.locator('[data-track-id]').nth(0).click();
    await page.keyboard.down('Shift');
    await page.locator('[data-track-id]').nth(2).click();
    await page.keyboard.up('Shift');

    // Double-click to play first track
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Get queue state
    let queueStore = await getAlpineStore(page, 'queue');
    const initialIndex = queueStore.currentIndex;

    // Click next button
    await page.click('[data-testid="player-next"]');

    // Wait for queue index to change
    await page.waitForFunction(
      (index) => {
        return window.Alpine.store('queue').currentIndex !== index;
      },
      initialIndex,
      { timeout: 5000 }
    );

    // Verify index increased
    queueStore = await getAlpineStore(page, 'queue');
    expect(queueStore.currentIndex).toBe(initialIndex + 1);

    // Click previous button
    await page.click('[data-testid="player-prev"]');

    // Wait for queue index to change back
    await page.waitForFunction(
      (index) => {
        return window.Alpine.store('queue').currentIndex === index;
      },
      initialIndex,
      { timeout: 5000 }
    );

    // Verify index decreased
    queueStore = await getAlpineStore(page, 'queue');
    expect(queueStore.currentIndex).toBe(initialIndex);
  });
});

test.describe('Shuffle and Loop Modes', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('should toggle shuffle mode', async ({ page }) => {
    // Get initial shuffle state
    const initialQueueStore = await getAlpineStore(page, 'queue');
    const initialShuffle = initialQueueStore.shuffle;

    // Click shuffle button
    const shuffleButton = page.locator('[data-testid="player-shuffle"]');
    await shuffleButton.click();

    // Wait for shuffle state to change
    await page.waitForFunction(
      (initial) => {
        return window.Alpine.store('queue').shuffle !== initial;
      },
      initialShuffle,
      { timeout: 5000 }
    );

    // Verify shuffle state changed
    const updatedQueueStore = await getAlpineStore(page, 'queue');
    expect(updatedQueueStore.shuffle).toBe(!initialShuffle);

    // Verify button visual state (should have text-primary class when active)
    const buttonClasses = await shuffleButton.getAttribute('class');
    if (!initialShuffle) {
      expect(buttonClasses).toContain('text-primary');
    } else {
      expect(buttonClasses).not.toContain('text-primary');
    }
  });

  test('should cycle through loop modes', async ({ page }) => {
    // Get initial loop mode
    const initialQueueStore = await getAlpineStore(page, 'queue');
    const initialLoopMode = initialQueueStore.loop;

    // Click loop button
    const loopButton = page.locator('[data-testid="player-loop"]');
    await loopButton.click();

    // Wait for loop mode to change
    await page.waitForFunction(
      (initial) => {
        return window.Alpine.store('queue').loop !== initial;
      },
      initialLoopMode,
      { timeout: 5000 }
    );

    // Verify loop mode changed
    const updatedQueueStore = await getAlpineStore(page, 'queue');
    expect(updatedQueueStore.loop).not.toBe(initialLoopMode);

    // Loop modes should cycle: off -> all -> one -> off
    const validModes = ['off', 'all', 'one'];
    expect(validModes).toContain(updatedQueueStore.loop);
  });

  test('should show loop one icon when loop mode is "one"', async ({ page }) => {
    // Set loop mode to "one"
    await page.evaluate(() => {
      window.Alpine.store('queue').loop = 'one';
    });

    // Wait a moment for UI to update
    await page.waitForTimeout(300);

    // Verify loop button shows "1" indicator
    const loopButton = page.locator('[data-testid="player-loop"]');
    const buttonHtml = await loopButton.innerHTML();
    expect(buttonHtml).toContain('1');
  });

  test('should repeat track when loop mode is "one"', async ({ page }) => {
    // Play a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Set loop mode to "one"
    await page.evaluate(() => {
      window.Alpine.store('queue').loop = 'one';
    });

    // Get current track ID
    const playerStore = await getAlpineStore(page, 'player');
    const trackId = playerStore.currentTrack.id;

    // Simulate track ending by seeking to near end
    await page.evaluate(() => {
      const store = window.Alpine.store('player');
      store.position = store.duration - 1;
    });

    // Wait for track to end and restart
    await page.waitForTimeout(2000);

    // Verify same track is still playing
    const updatedPlayerStore = await getAlpineStore(page, 'player');
    expect(updatedPlayerStore.currentTrack.id).toBe(trackId);
  });
});

test.describe('Queue Reordering (Drag and Drop)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });

    // Add tracks to queue
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await page.locator('[data-track-id]').nth(0).click();
    await page.keyboard.down('Shift');
    await page.locator('[data-track-id]').nth(4).click();
    await page.keyboard.up('Shift');
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);
  });

  test('should show drag handles on queue items', async ({ page }) => {
    // Navigate to Now Playing view
    await page.click('[x-show="$store.ui.view === \'nowPlaying\'"]').catch(() => {
      // Try alternative method to show queue
      page.evaluate(() => {
        window.Alpine.store('ui').view = 'nowPlaying';
      });
    });

    // Wait for queue items to be visible
    await page.waitForSelector('.queue-item .drag-handle', { state: 'visible', timeout: 5000 });

    // Verify drag handles are present
    const dragHandles = page.locator('.drag-handle');
    const count = await dragHandles.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should reorder queue items via drag and drop', async ({ page }) => {
    // Navigate to Now Playing view
    await page.evaluate(() => {
      window.Alpine.store('ui').view = 'nowPlaying';
    });

    // Wait for queue items
    await page.waitForSelector('.queue-item', { state: 'visible', timeout: 5000 });

    // Get initial queue order
    const initialQueueItems = await getQueueItems(page);
    const initialLength = initialQueueItems.length;

    if (initialLength < 3) {
      // Skip test if not enough items
      test.skip();
      return;
    }

    // Get track IDs before reordering
    const firstTrackId = initialQueueItems[1].id;
    const secondTrackId = initialQueueItems[2].id;

    // Perform drag and drop (drag second item to first position)
    const queueItems = page.locator('.queue-item');
    const source = queueItems.nth(2);
    const target = queueItems.nth(1);

    // Get bounding boxes
    const sourceBox = await source.boundingBox();
    const targetBox = await target.boundingBox();

    if (sourceBox && targetBox) {
      // Simulate drag and drop
      await page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
      await page.mouse.down();
      await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2);
      await page.mouse.up();

      // Wait for reorder to complete
      await page.waitForTimeout(500);

      // Verify queue order changed
      const updatedQueueItems = await getQueueItems(page);
      expect(updatedQueueItems[1].id).not.toBe(firstTrackId);
    }
  });

  test('should maintain queue integrity after reordering', async ({ page }) => {
    // Navigate to Now Playing view
    await page.evaluate(() => {
      window.Alpine.store('ui').view = 'nowPlaying';
    });

    await page.waitForSelector('.queue-item', { state: 'visible', timeout: 5000 });

    // Get initial queue length
    const initialQueueItems = await getQueueItems(page);
    const initialLength = initialQueueItems.length;

    // Perform a reorder operation (using store method)
    if (initialLength >= 2) {
      await callAlpineStoreMethod(page, 'queue', 'move', 1, 0);

      // Wait for UI to update
      await page.waitForTimeout(500);

      // Verify queue length unchanged
      const updatedQueueItems = await getQueueItems(page);
      expect(updatedQueueItems.length).toBe(initialLength);
    }
  });
});

test.describe('Queue View Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should show empty state when queue is empty', async ({ page }) => {
    // Ensure queue is empty
    await page.evaluate(() => {
      window.Alpine.store('queue').items = [];
    });

    // Navigate to Now Playing view
    await page.evaluate(() => {
      window.Alpine.store('ui').view = 'nowPlaying';
    });

    // Wait for empty state to show
    await page.waitForSelector('text=Queue is empty', { state: 'visible', timeout: 5000 });

    // Verify empty state message
    const emptyState = page.locator('text=Queue is empty');
    await expect(emptyState).toBeVisible();
  });

  test('should highlight currently playing track in queue', async ({ page }) => {
    // Add tracks and start playing
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Navigate to Now Playing view
    await page.evaluate(() => {
      window.Alpine.store('ui').view = 'nowPlaying';
    });

    await page.waitForSelector('.queue-item', { state: 'visible', timeout: 5000 });

    // Get current queue index
    const queueStore = await getAlpineStore(page, 'queue');
    const currentIndex = queueStore.currentIndex;

    // Find the queue item at current index
    const currentQueueItem = page.locator('.queue-item').nth(currentIndex);

    // Verify it has active styling (bg-primary class or playing indicator)
    const classes = await currentQueueItem.getAttribute('class');
    const hasPlayingIndicator = await currentQueueItem.locator('svg').count() > 0;

    expect(classes?.includes('bg-primary') || hasPlayingIndicator).toBe(true);
  });
});
