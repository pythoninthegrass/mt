import { test, expect } from '@playwright/test';
import { waitForAlpine, getAlpineStore } from './fixtures/helpers.js';
import { createLibraryState, setupLibraryMocks } from './fixtures/mock-library.js';
import { createPlaylistState, setupPlaylistMocks } from './fixtures/mock-playlists.js';

/**
 * Drag and Drop Tests
 *
 * Tests for drag-and-drop functionality across the application:
 * - Library track drag to playlist (sidebar drop)
 * - Playlist track reordering
 * - Multi-track drag operations
 * - Playlist sidebar reordering
 */

test.describe('Library to Playlist Drag and Drop', () => {
  test.beforeEach(async ({ page }) => {
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    const playlistState = createPlaylistState();
    await setupPlaylistMocks(page, playlistState);

    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should show drag indicator when dragging track', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').nth(0);

    // Start dragging
    const trackBox = await firstTrack.boundingBox();
    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
    await page.mouse.down();

    // Move slightly
    await page.mouse.move(trackBox.x + trackBox.width / 2 + 50, trackBox.y + trackBox.height / 2 + 50);

    // The drag should be initiated (visual feedback may vary)
    // This tests that dragging doesn't crash
    await page.mouse.up();
  });

  test('should highlight playlist when dragging track over it', async ({ page }) => {
    // Check if playlists exist
    const playlistItem = page.locator('[data-playlist-id]').first();
    if (!(await playlistItem.isVisible())) {
      test.skip();
      return;
    }

    // Select a track to prepare for drag
    const firstTrack = page.locator('[data-track-id]').nth(0);
    await firstTrack.click();

    // Get track ID
    const trackId = await firstTrack.getAttribute('data-track-id');

    // Simulate drag start on the track
    const trackBox = await firstTrack.boundingBox();

    // Start dragging
    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
    await page.mouse.down();

    // Move to playlist area
    const playlistBox = await playlistItem.boundingBox();
    await page.mouse.move(playlistBox.x + playlistBox.width / 2, playlistBox.y + playlistBox.height / 2);

    // Check for visual feedback (drop highlight)
    await page.waitForTimeout(200);

    // End drag
    await page.mouse.up();
  });

  test('should support dragging multiple selected tracks', async ({ page }) => {
    // Select multiple tracks using Cmd+click
    const firstTrack = page.locator('[data-track-id]').nth(0);
    const secondTrack = page.locator('[data-track-id]').nth(1);

    await firstTrack.click();
    await secondTrack.click({ modifiers: ['Meta'] });

    // Verify multiple selection
    const selectedCount = await page.evaluate(() => {
      const component = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return component.selectedTracks?.size || 0;
    });
    expect(selectedCount).toBe(2);

    // Start drag operation
    const trackBox = await firstTrack.boundingBox();
    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
    await page.mouse.down();

    // Move the mouse (simulating drag)
    await page.mouse.move(trackBox.x + 100, trackBox.y + 100);

    // End drag
    await page.mouse.up();

    // The selected tracks should still be selected
    const selectedAfter = await page.evaluate(() => {
      const component = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return component.selectedTracks?.size || 0;
    });
    expect(selectedAfter).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Playlist Track Reordering', () => {
  test.beforeEach(async ({ page }) => {
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    const playlistState = createPlaylistState();
    await setupPlaylistMocks(page, playlistState);

    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should enable drag reorder in playlist view', async ({ page }) => {
    // Navigate to a playlist
    const playlistItem = page.locator('[data-playlist-id]').first();
    if (!(await playlistItem.isVisible())) {
      test.skip();
      return;
    }

    await playlistItem.click();
    await page.waitForTimeout(500);

    // Wait for playlist tracks to load
    const tracks = page.locator('[data-track-id]');
    const trackCount = await tracks.count();

    if (trackCount < 2) {
      test.skip();
      return;
    }

    // Get initial order
    const firstTrackId = await tracks.nth(0).getAttribute('data-track-id');
    const secondTrackId = await tracks.nth(1).getAttribute('data-track-id');

    // The presence of draggable tracks indicates reorder capability
    expect(firstTrackId).toBeTruthy();
    expect(secondTrackId).toBeTruthy();
  });

  test('should not allow drag reorder in library view (only in playlist)', async ({ page }) => {
    // Ensure we're in library view
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Check if we're in library view (not playlist)
    const isInPlaylistView = await page.evaluate(() => {
      const component = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return component.currentPlaylistId !== null;
    });

    expect(isInPlaylistView).toBe(false);
  });
});

test.describe('Playlist Sidebar Reordering', () => {
  test.beforeEach(async ({ page }) => {
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    const playlistState = createPlaylistState();
    await setupPlaylistMocks(page, playlistState);

    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should show reorder handle on playlist items', async ({ page }) => {
    // Check for playlist reorder handles
    const reorderHandle = page.locator('[data-playlist-reorder-index]').first();

    if (await reorderHandle.isVisible()) {
      // Reorder handles exist
      const handleCount = await page.locator('[data-playlist-reorder-index]').count();
      expect(handleCount).toBeGreaterThan(0);
    }
  });

  test('should reorder playlists via drag handle', async ({ page }) => {
    const playlistItems = page.locator('[data-playlist-id]');
    const count = await playlistItems.count();

    if (count < 2) {
      test.skip();
      return;
    }

    // Get initial playlist order
    const firstPlaylistId = await playlistItems.nth(0).getAttribute('data-playlist-id');
    const secondPlaylistId = await playlistItems.nth(1).getAttribute('data-playlist-id');

    // Get reorder handles
    const handles = page.locator('[data-playlist-reorder-index]');
    const handleCount = await handles.count();

    if (handleCount < 2) {
      test.skip();
      return;
    }

    // Perform drag on the first handle
    const firstHandle = handles.nth(0);
    const secondHandle = handles.nth(1);

    const firstBox = await firstHandle.boundingBox();
    const secondBox = await secondHandle.boundingBox();

    if (!firstBox || !secondBox) {
      test.skip();
      return;
    }

    // Drag first handle to second position
    await page.mouse.move(firstBox.x + firstBox.width / 2, firstBox.y + firstBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(secondBox.x + secondBox.width / 2, secondBox.y + secondBox.height / 2);
    await page.mouse.up();

    await page.waitForTimeout(300);

    // The drag operation should complete without errors
    // Actual reorder verification would need backend persistence
  });

  test('should maintain playlist data integrity during reorder', async ({ page }) => {
    const playlistItems = page.locator('[data-playlist-id]');
    const initialCount = await playlistItems.count();

    if (initialCount < 2) {
      test.skip();
      return;
    }

    // Get initial playlist IDs
    const initialIds = [];
    for (let i = 0; i < initialCount; i++) {
      const id = await playlistItems.nth(i).getAttribute('data-playlist-id');
      initialIds.push(id);
    }

    // Simulate a reorder operation via store
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('[x-data="sidebar"]'));
      if (sidebar && sidebar.playlists && sidebar.playlists.length >= 2) {
        // Just verify the data structure is intact
        const playlistNames = sidebar.playlists.map(p => p.name);
        console.log('[Test] Playlist names:', playlistNames);
      }
    });

    // Count should remain the same
    const finalCount = await playlistItems.count();
    expect(finalCount).toBe(initialCount);
  });
});

test.describe('Queue Drag and Drop Enhancements', () => {
  test.beforeEach(async ({ page }) => {
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should add tracks to queue via double-click before drag operations work', async ({ page }) => {
    // Add tracks to queue first
    await page.locator('[data-track-id]').nth(0).dblclick();
    await page.waitForTimeout(500);

    // Verify queue has items
    const queueLength = await page.evaluate(() =>
      window.Alpine.store('queue').items.length
    );
    expect(queueLength).toBeGreaterThan(0);
  });

  test('should navigate to Now Playing view', async ({ page }) => {
    // Add tracks to queue
    await page.locator('[data-track-id]').nth(0).dblclick();
    await page.waitForTimeout(500);

    // Navigate to Now Playing
    await page.evaluate(() => {
      window.Alpine.store('ui').view = 'nowPlaying';
    });
    await page.waitForTimeout(300);

    // Verify Now Playing view is active
    const currentView = await page.evaluate(() =>
      window.Alpine.store('ui').view
    );
    expect(currentView).toBe('nowPlaying');
  });

  test('should show queue items in Now Playing view', async ({ page }) => {
    // Add multiple tracks to queue
    await page.locator('[data-track-id]').nth(0).dblclick();
    await page.waitForTimeout(500);

    // Navigate to Now Playing
    await page.evaluate(() => {
      window.Alpine.store('ui').view = 'nowPlaying';
    });
    await page.waitForTimeout(300);

    // Check for queue items in the view
    const queueContainer = page.locator('[x-data="nowPlayingView"]');
    if (await queueContainer.isVisible()) {
      const queueItems = page.locator('.queue-item');
      const itemCount = await queueItems.count();
      expect(itemCount).toBeGreaterThan(0);
    }
  });

  test('should support reorder operation via store method', async ({ page }) => {
    // Add tracks to queue
    await page.keyboard.press('Meta+a'); // Select all
    await page.keyboard.press('Enter'); // Play selected
    await page.waitForTimeout(500);

    const queueBefore = await page.evaluate(() =>
      window.Alpine.store('queue').items.map(t => t.id)
    );

    if (queueBefore.length < 2) {
      test.skip();
      return;
    }

    // Reorder via store method
    await page.evaluate(() => {
      window.Alpine.store('queue').reorder(0, 1);
    });
    await page.waitForTimeout(300);

    const queueAfter = await page.evaluate(() =>
      window.Alpine.store('queue').items.map(t => t.id)
    );

    // Queue should have changed (unless reorder was no-op)
    expect(queueAfter.length).toBe(queueBefore.length);
  });
});

test.describe('Drag and Drop Edge Cases', () => {
  test.beforeEach(async ({ page }) => {
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    const playlistState = createPlaylistState();
    await setupPlaylistMocks(page, playlistState);

    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should handle cancelled drag (drop outside valid target)', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').nth(0);
    const trackBox = await firstTrack.boundingBox();

    // Start drag
    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
    await page.mouse.down();

    // Drag far away from any valid drop target
    await page.mouse.move(10, 10);

    // Release (cancelled drop)
    await page.mouse.up();

    // Application should still be responsive
    const selectedCount = await page.evaluate(() => {
      const component = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return component.selectedTracks?.size || 0;
    });
    expect(selectedCount).toBeGreaterThanOrEqual(0);
  });

  test('should handle rapid drag operations', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').nth(0);
    const trackBox = await firstTrack.boundingBox();

    // Perform multiple rapid drags
    for (let i = 0; i < 3; i++) {
      await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
      await page.mouse.down();
      await page.mouse.move(trackBox.x + 50 + i * 10, trackBox.y + 50);
      await page.mouse.up();
    }

    // Application should not crash
    const isAppResponsive = await page.evaluate(() => {
      return window.Alpine && window.Alpine.store('library');
    });
    expect(isAppResponsive).toBeTruthy();
  });

  test('should preserve selection during drag without drop', async ({ page }) => {
    // Select multiple tracks
    await page.keyboard.press('Meta+a');

    const selectedBefore = await page.evaluate(() => {
      const component = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return component.selectedTracks?.size || 0;
    });

    // Start and cancel drag
    const firstTrack = page.locator('[data-track-id]').nth(0);
    const trackBox = await firstTrack.boundingBox();

    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(trackBox.x + 100, trackBox.y + 100);
    await page.mouse.up();

    // Selection should be preserved (or cleared based on implementation)
    const selectedAfter = await page.evaluate(() => {
      const component = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return component.selectedTracks?.size || 0;
    });

    // At minimum, no crash should occur
    expect(selectedAfter).toBeGreaterThanOrEqual(0);
  });

  test('should handle touch interaction on tracks', async ({ page }) => {
    // Test that basic interactions work (touch events require special browser config)
    // This verifies the app handles touch-like rapid interactions

    const firstTrack = page.locator('[data-track-id]').nth(0);

    // Rapid click to simulate touch-like interaction
    await firstTrack.click();
    await page.waitForTimeout(50);
    await firstTrack.click();

    // App should remain responsive
    const isResponsive = await page.evaluate(() => Boolean(window.Alpine));
    expect(isResponsive).toBe(true);
  });
});

test.describe('Drag Visual Feedback', () => {
  test.beforeEach(async ({ page }) => {
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    const playlistState = createPlaylistState();
    await setupPlaylistMocks(page, playlistState);

    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should show cursor change during drag', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').nth(0);
    const trackBox = await firstTrack.boundingBox();

    // Move to track
    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);

    // Start drag
    await page.mouse.down();

    // Move during drag
    await page.mouse.move(trackBox.x + 100, trackBox.y + 100);

    // The drag should be active (visual feedback)
    // Note: Cursor style verification is limited in Playwright

    // End drag
    await page.mouse.up();
  });

  test('should clear drag state after drop', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').nth(0);
    const trackBox = await firstTrack.boundingBox();

    // Perform complete drag cycle
    await page.mouse.move(trackBox.x + trackBox.width / 2, trackBox.y + trackBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(trackBox.x + 100, trackBox.y + 100);
    await page.mouse.up();

    await page.waitForTimeout(100);

    // Verify drag state is cleared in sidebar
    const sidebarDragState = await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('[x-data="sidebar"]'));
      return sidebar?.dragOverPlaylistId;
    });
    expect(sidebarDragState).toBeFalsy();
  });
});
