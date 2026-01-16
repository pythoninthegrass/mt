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

test.describe('Playback Controls', () => {
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

test.describe('Volume Controls', () => {
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
});

test.describe('Playback Parity Tests', () => {
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
});
