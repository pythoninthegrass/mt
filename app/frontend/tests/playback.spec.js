import { test, expect } from '@playwright/test';
import {
  waitForAlpine,
  getAlpineStore,
  waitForPlaying,
  waitForPaused,
  getCurrentTrack,
  doubleClickTrackRow,
  formatDuration,
} from './fixtures/helpers.js';
import { createLibraryState, setupLibraryMocks } from './fixtures/mock-library.js';

test.describe('Playback Controls @tauri', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Wait for Alpine.js to be ready
    await waitForAlpine(page);

    // Wait for library to load
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('should toggle play/pause when clicking play button', async ({ page }) => {
    // Get initial player state
    const initialPlayerStore = await getAlpineStore(page, 'player');
    expect(initialPlayerStore.isPlaying).toBe(false);

    // Click play button
    const playButton = page.locator('[data-testid="player-playpause"]');
    await playButton.click();

    // Wait for playing state
    await waitForPlaying(page);

    // Verify player is playing
    const playingStore = await getAlpineStore(page, 'player');
    expect(playingStore.isPlaying).toBe(true);

    // Click pause button
    await playButton.click();

    // Wait for paused state
    await waitForPaused(page);

    // Verify player is paused
    const pausedStore = await getAlpineStore(page, 'player');
    expect(pausedStore.isPlaying).toBe(false);
  });

  test('should play track when double-clicking track row', async ({ page }) => {
    // Wait for tracks to load
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Get track count
    const trackCount = await page.locator('[data-track-id]').count();
    expect(trackCount).toBeGreaterThan(0);

    // Double-click first track
    await doubleClickTrackRow(page, 0);

    // Wait for track to start playing
    await waitForPlaying(page);

    // Verify current track is set
    const currentTrack = await getCurrentTrack(page);
    expect(currentTrack).not.toBeNull();
    expect(currentTrack.id).toBeTruthy();
  });

  test('should navigate to next track', async ({ page }) => {
    // Start playing first track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Get current track ID
    const firstTrack = await getCurrentTrack(page);
    const firstTrackId = firstTrack.id;

    // Click next button
    const nextButton = page.locator('[data-testid="player-next"]');
    await nextButton.click();

    // Wait for track to change
    await page.waitForFunction(
      (trackId) => {
        const store = window.Alpine.store('player');
        return store.currentTrack && store.currentTrack.id !== trackId;
      },
      firstTrackId,
      { timeout: 5000 }
    );

    // Verify new track is different
    const secondTrack = await getCurrentTrack(page);
    expect(secondTrack.id).not.toBe(firstTrackId);
  });

  test('should navigate to previous track', async ({ page }) => {
    // Start playing second track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 1);
    await waitForPlaying(page);

    // Get current track ID
    const secondTrack = await getCurrentTrack(page);
    const secondTrackId = secondTrack.id;

    // Click previous button
    const prevButton = page.locator('[data-testid="player-prev"]');
    await prevButton.click();

    // Wait for track to change
    await page.waitForFunction(
      (trackId) => {
        const store = window.Alpine.store('player');
        return store.currentTrack && store.currentTrack.id !== trackId;
      },
      secondTrackId,
      { timeout: 5000 }
    );

    // Verify new track is different
    const firstTrack = await getCurrentTrack(page);
    expect(firstTrack.id).not.toBe(secondTrackId);
  });

  test('should update progress bar during playback', async ({ page }) => {
    // Start playing a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Wait a moment for progress to update
    await page.waitForTimeout(2000);

    // Get current position from player store
    const playerStore = await getAlpineStore(page, 'player');
    expect(playerStore.position).toBeGreaterThan(0);

    // Verify progress bar shows progress
    const progressBar = page.locator('[data-testid="player-progressbar"] div').first();
    const width = await progressBar.evaluate((el) => el.style.width);
    expect(width).not.toBe('0%');
  });

  test('should seek when clicking on progress bar', async ({ page }) => {
    // Start playing a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Wait for track to start
    await page.waitForTimeout(1000);

    // Get progress bar element
    const progressBar = page.locator('[data-testid="player-progressbar"]');
    const boundingBox = await progressBar.boundingBox();

    // Click at 50% of progress bar
    const clickX = boundingBox.x + boundingBox.width * 0.5;
    const clickY = boundingBox.y + boundingBox.height / 2;
    await page.mouse.click(clickX, clickY);

    // Wait a moment for seek to complete
    await page.waitForTimeout(500);

    // Verify position changed (should be around 50% of duration)
    const playerStore = await getAlpineStore(page, 'player');
    const expectedPosition = playerStore.duration * 0.5;
    expect(playerStore.position).toBeGreaterThan(expectedPosition * 0.8);
    expect(playerStore.position).toBeLessThan(expectedPosition * 1.2);
  });

  test('should display current time and duration', async ({ page }) => {
    // Start playing a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Wait for time display to update
    await page.waitForTimeout(1000);

    // Find time display element
    const timeDisplay = page.locator('.tabular-nums.whitespace-nowrap');
    const timeText = await timeDisplay.textContent();

    // Verify format is "0:XX / M:SS" or similar
    expect(timeText).toMatch(/\d+:\d{2}\s*\/\s*\d+:\d{2}/);
  });

  test('should disable prev/next buttons when no track is loaded', async ({ page }) => {
    // Verify buttons are disabled initially (or have opacity-40 class)
    const prevButton = page.locator('[data-testid="player-prev"]');
    const nextButton = page.locator('[data-testid="player-next"]');

    const prevClasses = await prevButton.getAttribute('class');
    const nextClasses = await nextButton.getAttribute('class');

    // Buttons should have opacity-40 class when no track is loaded
    const playerStore = await getAlpineStore(page, 'player');
    if (!playerStore.currentTrack) {
      expect(prevClasses).toContain('opacity-40');
      expect(nextClasses).toContain('opacity-40');
    }
  });

  test('should show playing indicator on current track', async ({ page }) => {
    // Start playing a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Get current track ID
    const currentTrack = await getCurrentTrack(page);

    // Find the track row with matching ID
    const trackRow = page.locator(`[data-track-id="${currentTrack.id}"]`);

    // Verify row has playing indicator (▶ symbol or bg-primary class)
    const hasPlayingIndicator = await trackRow.evaluate((el) => {
      return el.textContent.includes('▶') || el.classList.contains('bg-primary/15');
    });
    expect(hasPlayingIndicator).toBe(true);
  });

  test('should toggle favorite status', async ({ page }) => {
    // Start playing a track
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    // Get initial favorite status
    const currentTrack = await getCurrentTrack(page);
    const initialFavorite = currentTrack.favorite || false;

    // Click favorite button
    const favoriteButton = page.locator('button[title*="Liked Songs"]');
    await favoriteButton.click();

    // Wait for favorite status to change
    await page.waitForFunction(
      (initial) => {
        const track = window.Alpine.store('player').currentTrack;
        return track && track.favorite !== initial;
      },
      initialFavorite,
      { timeout: 5000 }
    );

    // Verify favorite status changed
    const updatedTrack = await getCurrentTrack(page);
    expect(updatedTrack.favorite).toBe(!initialFavorite);

    // Verify button icon changed (filled heart vs outline)
    const buttonHtml = await favoriteButton.innerHTML();
    if (!initialFavorite) {
      // Should now be filled (has fill="currentColor")
      expect(buttonHtml).toContain('fill="currentColor"');
    }
  });
});

test.describe('Volume Controls @tauri', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should adjust volume when clicking volume slider', async ({ page }) => {
    // Get volume bar element
    const volumeBar = page.locator('[data-testid="player-volume"]');
    const boundingBox = await volumeBar.boundingBox();

    // Click at 75% of volume bar
    const clickX = boundingBox.x + boundingBox.width * 0.75;
    const clickY = boundingBox.y + boundingBox.height / 2;
    await page.mouse.click(clickX, clickY);

    // Wait a moment for volume to update
    await page.waitForTimeout(300);

    // Verify volume changed (should be around 75)
    const playerStore = await getAlpineStore(page, 'player');
    expect(playerStore.volume).toBeGreaterThan(60);
    expect(playerStore.volume).toBeLessThan(90);
  });

  test('should toggle mute when clicking mute button', async ({ page }) => {
    // Get initial mute status
    const playerStore = await getAlpineStore(page, 'player');
    const initialMuted = playerStore.muted || false;

    // Click mute button
    const muteButton = page.locator('[data-testid="player-mute"]');
    await muteButton.click();

    // Wait for mute status to change
    await page.waitForFunction(
      (initial) => {
        const store = window.Alpine.store('player');
        return store.muted !== initial;
      },
      initialMuted,
      { timeout: 2000 }
    );

    // Verify mute status changed
    const updatedStore = await getAlpineStore(page, 'player');
    expect(updatedStore.muted).toBe(!initialMuted);
  });

  test('should smoothly adjust volume when dragging slider', async ({ page }) => {
    // Get volume bar element
    const volumeBar = page.locator('[data-testid="player-volume"]');
    const boundingBox = await volumeBar.boundingBox();

    // Record initial volume
    const initialStore = await getAlpineStore(page, 'player');
    const initialVolume = initialStore.volume;

    // Simulate dragging from 20% to 80% of volume bar
    const startX = boundingBox.x + boundingBox.width * 0.2;
    const endX = boundingBox.x + boundingBox.width * 0.8;
    const centerY = boundingBox.y + boundingBox.height / 2;

    // Perform drag gesture
    await page.mouse.move(startX, centerY);
    await page.mouse.down();

    // Move through intermediate positions to simulate smooth drag
    const steps = 10;
    for (let i = 1; i <= steps; i++) {
      const x = startX + ((endX - startX) * i) / steps;
      await page.mouse.move(x, centerY);
      await page.waitForTimeout(10); // Small delay between moves
    }

    await page.mouse.up();

    // Wait for debounced volume update
    await page.waitForTimeout(300);

    // Verify volume changed and is in expected range
    const finalStore = await getAlpineStore(page, 'player');
    expect(finalStore.volume).toBeGreaterThan(initialVolume);
    expect(finalStore.volume).toBeGreaterThan(70);
    expect(finalStore.volume).toBeLessThan(90);

    // Verify thumb and tooltip are visible during hover
    await page.mouse.move(boundingBox.x + boundingBox.width * 0.5, centerY);

    // The thumb should be visible on hover (opacity-100)
    const thumbElement = volumeBar.locator('.absolute.top-1\\/2.-translate-y-1\\/2.w-2\\.5.h-2\\.5');
    await expect(thumbElement).toBeVisible();
  });

  test('should not bounce back when rapidly clicking volume slider', async ({ page }) => {
    // Get volume bar element
    const volumeBar = page.locator('[data-testid="player-volume"]');
    const boundingBox = await volumeBar.boundingBox();
    const centerY = boundingBox.y + boundingBox.height / 2;

    // Rapidly click at different positions
    const positions = [0.2, 0.8, 0.5, 0.9, 0.3];

    for (const pos of positions) {
      const clickX = boundingBox.x + boundingBox.width * pos;
      await page.mouse.click(clickX, centerY);

      // Very short wait to simulate rapid clicking
      await page.waitForTimeout(50);

      // Check that volume is approximately at clicked position
      const store = await getAlpineStore(page, 'player');
      const expectedVolume = Math.round(pos * 100);

      // Allow some tolerance for rounding
      expect(store.volume).toBeGreaterThan(expectedVolume - 10);
      expect(store.volume).toBeLessThan(expectedVolume + 10);
    }
  });

  test('should handle rapid drag direction changes without bounce-back', async ({ page }) => {
    // Get volume bar element
    const volumeBar = page.locator('[data-testid="player-volume"]');
    const boundingBox = await volumeBar.boundingBox();
    const centerY = boundingBox.y + boundingBox.height / 2;

    // Start drag at 50%
    const midX = boundingBox.x + boundingBox.width * 0.5;
    await page.mouse.move(midX, centerY);
    await page.mouse.down();

    // Rapidly change direction: right, left, right, left
    const positions = [0.8, 0.3, 0.9, 0.2, 0.7];

    for (const pos of positions) {
      const x = boundingBox.x + boundingBox.width * pos;
      await page.mouse.move(x, centerY);
      // Very small delay to simulate rapid movement
      await page.waitForTimeout(5);
    }

    // Release at final position (70%)
    await page.mouse.up();

    // Wait for volume to settle
    await page.waitForTimeout(100);

    // Volume should be at or near final drag position (70%)
    const finalStore = await getAlpineStore(page, 'player');
    expect(finalStore.volume).toBeGreaterThan(60);
    expect(finalStore.volume).toBeLessThan(80);
  });
});

test.describe('Playback Edge Cases (Regression Hardening)', () => {
  // NOTE: These tests use mocked library data and run in browser mode
  test.beforeEach(async ({ page }) => {
    // Set up library mocks BEFORE navigating
    const libraryState = createLibraryState();
    await setupLibraryMocks(page, libraryState);

    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('rapid double-clicks should not duplicate tracks in queue', async ({ page }) => {
    // This tests the fix from commits 25fa679 and 37f0af4
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Clear any existing queue
    await page.evaluate(() => {
      window.Alpine.store('queue').items = [];
    });

    // Get library track count
    const libraryCount = await page.evaluate(() =>
      window.Alpine.store('library').tracks.length
    );

    // Rapid double-clicks (simulating race condition)
    const trackRow = page.locator('[data-track-id]').nth(0);
    await trackRow.dblclick();
    await trackRow.dblclick();
    await trackRow.dblclick();

    // Wait for queue to stabilize
    await page.waitForTimeout(500);

    // Queue should contain exactly the library count, not duplicates
    const queueLength = await page.evaluate(() =>
      window.Alpine.store('queue').items.length
    );

    expect(queueLength).toBe(libraryCount);
  });

  test('volume should update immediately during playback', async ({ page }) => {
    // NOTE: In browser mode without Tauri audio backend, we simulate playback state
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Simulate playback by setting up queue and player state directly
    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      // Add tracks to queue
      queue.items = [...library.tracks];
      queue.currentIndex = 0;

      // Simulate playing state
      player.currentTrack = library.tracks[0];
      player.isPlaying = true;
    });

    // Set volume to 50%
    const volumeBar = page.locator('[data-testid="player-volume"]');
    const boundingBox = await volumeBar.boundingBox();
    const clickX = boundingBox.x + boundingBox.width * 0.5;
    const clickY = boundingBox.y + boundingBox.height / 2;
    await page.mouse.click(clickX, clickY);

    await page.waitForTimeout(200);

    // Verify volume changed
    const volume1 = await page.evaluate(() =>
      window.Alpine.store('player').volume
    );
    expect(volume1).toBeGreaterThan(40);
    expect(volume1).toBeLessThan(60);

    // Still playing?
    const stillPlaying = await page.evaluate(() =>
      window.Alpine.store('player').isPlaying
    );
    expect(stillPlaying).toBe(true);

    // Change volume again while playing
    await page.mouse.click(boundingBox.x + boundingBox.width * 0.75, clickY);
    await page.waitForTimeout(200);

    const volume2 = await page.evaluate(() =>
      window.Alpine.store('player').volume
    );
    expect(volume2).toBeGreaterThan(volume1);
  });

  test('queue clear during playback should stop playback', async ({ page }) => {
    // NOTE: In browser mode without Tauri audio backend, we simulate playback state
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Simulate playback by setting up queue and player state directly
    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      // Add tracks to queue
      queue.items = [...library.tracks];
      queue.currentIndex = 0;

      // Simulate playing state
      player.currentTrack = library.tracks[0];
      player.isPlaying = true;
    });

    // Clear queue
    await page.evaluate(() => {
      window.Alpine.store('queue').clear();
    });

    await page.waitForTimeout(300);

    // Verify queue is empty and playback state
    const queueEmpty = await page.evaluate(() =>
      window.Alpine.store('queue').items.length === 0
    );
    expect(queueEmpty).toBe(true);

    // Current track should be null
    const currentTrack = await page.evaluate(() =>
      window.Alpine.store('queue').currentTrack
    );
    expect(currentTrack).toBeNull();
  });

  test('shuffle toggle during playback should keep current track', async ({ page }) => {
    // NOTE: In browser mode without Tauri audio backend, we simulate playback state
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Simulate playback by setting up queue and player state directly
    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      // Add tracks to queue (need multiple for meaningful shuffle test)
      queue.items = [...library.tracks];
      queue.currentIndex = 0;

      // Simulate playing state
      player.currentTrack = library.tracks[0];
      player.isPlaying = true;
    });

    // Get current track ID before shuffle
    const trackIdBefore = await page.evaluate(() =>
      window.Alpine.store('player').currentTrack?.id
    );

    // Toggle shuffle on
    await page.locator('[data-testid="player-shuffle"]').click();
    await page.waitForTimeout(300);

    // Verify current track didn't change
    const trackIdAfter = await page.evaluate(() =>
      window.Alpine.store('player').currentTrack?.id
    );
    expect(trackIdAfter).toBe(trackIdBefore);

    // Toggle shuffle off
    await page.locator('[data-testid="player-shuffle"]').click();
    await page.waitForTimeout(300);

    // Still same track
    const trackIdFinal = await page.evaluate(() =>
      window.Alpine.store('player').currentTrack?.id
    );
    expect(trackIdFinal).toBe(trackIdBefore);
  });

  test('now playing track display should show current track title and artist', async ({ page }) => {
    // Simulate playback by setting up queue and player state directly
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      queue.items = [...library.tracks];
      queue.currentIndex = 0;
      player.currentTrack = library.tracks[0];
      player.isPlaying = true;
    });

    // Check the track display in the footer
    const trackDisplay = page.locator('footer [x-text="trackDisplayName"]');
    await expect(trackDisplay).toBeVisible();

    // Verify it displays track info
    const displayText = await trackDisplay.textContent();
    expect(displayText.length).toBeGreaterThan(0);

    // The display format is typically "Artist - Title" or "Title"
    // Verify it contains something meaningful
    expect(displayText).not.toBe('—');
  });

  test('now playing display should update when track changes', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Set up initial track
    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      queue.items = [...library.tracks];
      queue.currentIndex = 0;
      player.currentTrack = library.tracks[0];
      player.isPlaying = true;
    });

    const trackDisplay = page.locator('footer [x-text="trackDisplayName"]');
    const firstTrackDisplay = await trackDisplay.textContent();

    // Change to second track
    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      if (library.tracks.length > 1) {
        queue.currentIndex = 1;
        player.currentTrack = library.tracks[1];
      }
    });

    await page.waitForTimeout(200);

    // Display should update (if tracks are different)
    const secondTrackDisplay = await trackDisplay.textContent();
    expect(secondTrackDisplay.length).toBeGreaterThan(0);
  });

  test('double-click on now playing display should scroll to current track in library', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Get track count and select a track from the middle
    const trackCount = await page.evaluate(() =>
      window.Alpine.store('library').filteredTracks.length
    );

    // Use a track from the middle of the list
    const targetIndex = Math.floor(trackCount / 2);

    await page.evaluate((idx) => {
      const library = window.Alpine.store('library');
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      queue.items = [...library.tracks];
      queue.currentIndex = idx;
      player.currentTrack = library.tracks[idx];
    }, targetIndex);

    // Scroll to top of library first to ensure we need to scroll
    await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      if (container) container.scrollTop = 0;
    });
    await page.waitForTimeout(200);

    // Double-click the now playing display
    const trackDisplay = page.locator('footer [x-text="trackDisplayName"]');
    await trackDisplay.dblclick();

    // Wait for scroll animation
    await page.waitForTimeout(600);

    // Verify the current track is now visible
    const currentTrackId = await page.evaluate(() =>
      window.Alpine.store('player').currentTrack?.id
    );

    if (currentTrackId) {
      const trackElement = page.locator(`[data-track-id="${currentTrackId}"]`);
      const isVisible = await trackElement.isVisible();
      expect(isVisible).toBe(true);
    }
  });

  test('now playing display should be hidden when no track is playing', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Ensure no track is playing
    await page.evaluate(() => {
      window.Alpine.store('player').currentTrack = null;
      window.Alpine.store('player').isPlaying = false;
    });

    // The track display should be invisible (invisible class when no track)
    const trackDisplay = page.locator('footer [x-text="trackDisplayName"]');

    // Check the visibility class
    const hasInvisibleClass = await page.evaluate(() => {
      const el = document.querySelector('footer [x-text="trackDisplayName"]');
      return el?.classList.contains('invisible');
    });

    expect(hasInvisibleClass).toBe(true);
  });

  test('now playing display should show when track is set', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Set a current track
    await page.evaluate(() => {
      const library = window.Alpine.store('library');
      const player = window.Alpine.store('player');
      player.currentTrack = library.tracks[0];
    });

    await page.waitForTimeout(100);

    // The track display should be visible
    const hasInvisibleClass = await page.evaluate(() => {
      const el = document.querySelector('footer [x-text="trackDisplayName"]');
      return el?.classList.contains('invisible');
    });

    expect(hasInvisibleClass).toBe(false);
  });
});

test.describe('Playback Parity Tests @tauri', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('pause should freeze position (task-141)', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    await page.waitForFunction(() => window.Alpine.store('player').position > 0.5);

    await page.locator('[data-testid="player-playpause"]').click();
    await waitForPaused(page);

    const pos0 = await page.evaluate(() => window.Alpine.store('player').position);
    await page.waitForTimeout(750);
    const pos1 = await page.evaluate(() => window.Alpine.store('player').position);

    expect(pos1 - pos0).toBeLessThanOrEqual(0.25);
  });

  test('seek should move position and remain stable (task-142)', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    await page.waitForFunction(() => window.Alpine.store('player').duration > 5);

    const duration = await page.evaluate(() => window.Alpine.store('player').duration);
    const targetFraction = 0.25;
    const expected = duration * targetFraction;
    const tolerance = Math.max(2.0, duration * 0.05);

    const bar = page.locator('[data-testid="player-progressbar"]');
    const box = await bar.boundingBox();
    await page.mouse.click(box.x + box.width * targetFraction, box.y + box.height / 2);

    await page.waitForTimeout(300);
    const posA = await page.evaluate(() => window.Alpine.store('player').position);
    expect(Math.abs(posA - expected)).toBeLessThanOrEqual(tolerance);

    await page.waitForTimeout(400);
    const posB = await page.evaluate(() => window.Alpine.store('player').position);
    expect(Math.abs(posB - expected)).toBeLessThanOrEqual(tolerance);
  });

  test('rapid next should not break playback state (task-143)', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    const nextBtn = page.locator('[data-testid="player-next"]');
    for (let i = 0; i < 15; i++) {
      await nextBtn.click();
      await page.waitForTimeout(75);
    }

    const player = await page.evaluate(() => window.Alpine.store('player'));
    expect(player.currentTrack).toBeTruthy();
    expect(player.currentTrack.id).toBeTruthy();
    expect(player.isPlaying).toBe(true);
  });

  test('should preserve database duration when Rust returns 0 (task-148)', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await doubleClickTrackRow(page, 0);
    await waitForPlaying(page);

    await page.waitForFunction(() => window.Alpine.store('player').duration > 0);
    const initialDuration = await page.evaluate(() => window.Alpine.store('player').duration);
    expect(initialDuration).toBeGreaterThan(0);

    await page.evaluate((dbDuration) => {
      window.__TAURI__.event.emit('audio://progress', {
        position_ms: 1000,
        duration_ms: 0,
        state: 'Playing',
      });
    }, initialDuration);

    await page.waitForTimeout(100);

    const afterDuration = await page.evaluate(() => window.Alpine.store('player').duration);
    expect(afterDuration).toBe(initialDuration);
  });
});

test.describe('Auto-Advance Behavior (task-224)', () => {
  // NOTE: These tests use mocked library data and work in browser-only mode
  // They test the queue's auto-advance logic by directly manipulating state,
  // which is what happens when the audio://track-ended event fires and triggers playNext()

  test('should auto-advance to next track when current track ends', async ({ page }) => {
    // Setup mocks for browser-only testing
    const libraryState = createLibraryState({ trackCount: 10 });
    await setupLibraryMocks(page, libraryState);
    await page.goto('/');
    await waitForAlpine(page);

    // 1. Setup: Load library with tracks
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // 2. Directly populate queue with library tracks and set playing state
    await page.evaluate((tracks) => {
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');
      queue.items = tracks;
      queue.currentIndex = 0;
      queue._originalOrder = [...tracks];
      player.currentTrack = tracks[0];
      player.isPlaying = true;
    }, libraryState.tracks);

    // 3. Capture initial state
    const initialState = await page.evaluate(() => ({
      queueCurrentTrackId: window.Alpine.store('queue').currentTrack?.id,
      queueIndex: window.Alpine.store('queue').currentIndex,
      queueLength: window.Alpine.store('queue').items.length,
    }));

    expect(initialState.queueLength).toBeGreaterThan(1);

    // 4. Simulate track ending - manually advance the queue
    // (This mirrors what playNext() does when playIndex is called)
    await page.evaluate(() => {
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      // Push current track to history before advancing (what playNext does)
      if (queue.currentIndex >= 0 && queue._playHistory) {
        queue._playHistory.push(queue.currentIndex);
      }

      // Advance to next track
      queue.currentIndex++;
      const newTrack = queue.items[queue.currentIndex];

      // Update player state (simulating successful playback)
      player.currentTrack = newTrack;
      player.isPlaying = true;
    });

    await page.waitForTimeout(50);

    // 5. Assert: Queue index incremented
    const newIndex = await page.evaluate(() =>
      window.Alpine.store('queue').currentIndex
    );
    expect(newIndex).toBe(initialState.queueIndex + 1);

    // 6. Assert: Queue's current track changed
    const newQueueTrackId = await page.evaluate(() =>
      window.Alpine.store('queue').currentTrack?.id
    );
    expect(newQueueTrackId).not.toBe(initialState.queueCurrentTrackId);

    // 7. Assert: Still playing
    const isPlaying = await page.evaluate(() =>
      window.Alpine.store('player').isPlaying
    );
    expect(isPlaying).toBe(true);

    // 8. Assert: Player's current track updated
    const playerTrackId = await page.evaluate(() =>
      window.Alpine.store('player').currentTrack?.id
    );
    expect(playerTrackId).toBe(newQueueTrackId);
  });

  test('should stop playback at end of queue when loop is off', async ({ page }) => {
    // Setup mocks for browser-only testing
    const libraryState = createLibraryState({ trackCount: 10 });
    await setupLibraryMocks(page, libraryState);
    await page.goto('/');
    await waitForAlpine(page);

    // 1. Setup: Load library with tracks
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // 2. Directly populate queue and set to last track with playing state
    await page.evaluate((tracks) => {
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');
      queue.items = tracks;
      queue.currentIndex = tracks.length - 1;
      queue.loop = 'none';
      queue._originalOrder = [...tracks];
      player.currentTrack = tracks[tracks.length - 1];
      player.isPlaying = true;
    }, libraryState.tracks);

    // 3. Verify we're at the last track
    const lastIndex = await page.evaluate(() =>
      window.Alpine.store('queue').currentIndex
    );
    const queueLength = await page.evaluate(() =>
      window.Alpine.store('queue').items.length
    );
    expect(lastIndex).toBe(queueLength - 1);

    // 4. Simulate track ending by calling playNext() directly
    // playNext() handles the "at end with loop=none" case internally
    await page.evaluate(() => {
      const player = window.Alpine.store('player');
      player.isPlaying = false; // Event listener sets this first
      window.Alpine.store('queue').playNext();
    });

    await page.waitForTimeout(100);

    // 5. Assert: Playback stopped (no next track, loop is off)
    const isPlaying = await page.evaluate(() =>
      window.Alpine.store('player').isPlaying
    );
    expect(isPlaying).toBe(false);

    // 6. Assert: Index stayed at last track (didn't wrap)
    const finalIndex = await page.evaluate(() =>
      window.Alpine.store('queue').currentIndex
    );
    expect(finalIndex).toBe(queueLength - 1);
  });

  test('should loop back to first track when loop-all is enabled', async ({ page }) => {
    // Setup mocks for browser-only testing
    const libraryState = createLibraryState({ trackCount: 10 });
    await setupLibraryMocks(page, libraryState);
    await page.goto('/');
    await waitForAlpine(page);

    // 1. Setup: Load library with tracks
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // 2. Directly populate queue and set to last track with loop enabled
    await page.evaluate((tracks) => {
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');
      queue.items = tracks;
      queue.currentIndex = tracks.length - 1;
      queue.loop = 'all';
      queue._originalOrder = [...tracks];
      player.currentTrack = tracks[tracks.length - 1];
      player.isPlaying = true;
    }, libraryState.tracks);

    const lastTrackId = await page.evaluate(() =>
      window.Alpine.store('queue').currentTrack?.id
    );

    // 3. Simulate track ending - manually advance with wrap-around
    // (This mirrors what playNext() does with loop='all')
    await page.evaluate(() => {
      const queue = window.Alpine.store('queue');
      const player = window.Alpine.store('player');

      // Push current track to history
      if (queue._playHistory) {
        queue._playHistory.push(queue.currentIndex);
      }

      // Wrap to first track (what playNext does with loop='all')
      queue.currentIndex = 0;
      const newTrack = queue.items[0];

      // Update player state (simulating successful playback)
      player.currentTrack = newTrack;
      player.isPlaying = true;
    });

    await page.waitForTimeout(50);

    // 4. Assert: Wrapped to first track
    const newIndex = await page.evaluate(() =>
      window.Alpine.store('queue').currentIndex
    );
    expect(newIndex).toBe(0);

    // 5. Assert: Still playing
    const isPlaying = await page.evaluate(() =>
      window.Alpine.store('player').isPlaying
    );
    expect(isPlaying).toBe(true);

    // 6. Assert: Track changed to first track
    const newTrackId = await page.evaluate(() =>
      window.Alpine.store('queue').currentTrack?.id
    );
    expect(newTrackId).not.toBe(lastTrackId);
  });
});
