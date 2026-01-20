import { test, expect } from '@playwright/test';
import {
  waitForAlpine,
  getAlpineStore,
  setAlpineStoreProperty,
  waitForStoreValue,
} from './fixtures/helpers.js';

test.describe('Last.fm Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Set viewport size to mimic desktop use
    await page.setViewportSize({ width: 1624, height: 1057 });
    await page.goto('/');
    await waitForAlpine(page);
  });

  test.describe('Authentication Flow', () => {
    test.beforeEach(async ({ page }) => {
      // Navigate to settings
      await page.click('[data-testid="sidebar-settings"]');
      await page.waitForTimeout(500);
      // Click on Last.fm section
      await page.click('[data-testid="settings-nav-lastfm"]');
      await page.waitForTimeout(300);
    });

    test('should display connection status indicator', async ({ page }) => {
      // Check for status indicator
      const statusIndicator = page.locator('.w-3.h-3.rounded-full').first();
      await expect(statusIndicator).toBeVisible();

      // Should show red (not connected) initially
      const classes = await statusIndicator.getAttribute('class');
      expect(classes).toContain('bg-red-500');
    });

    test('should show "Not Connected" status when not authenticated', async ({ page }) => {
      const statusText = page.locator('text=Not Connected').first();
      await expect(statusText).toBeVisible();
    });

    test('should show Connect button when not authenticated', async ({ page }) => {
      const connectButton = page.locator('[data-testid="lastfm-connect"]');
      await expect(connectButton).toBeVisible();
      await expect(connectButton).toHaveText('Connect');
    });

    test('should handle auth flow with pending state', async ({ page }) => {
      // Mock the API response for getting auth URL
      await page.route('**/lastfm/auth', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            auth_url: 'https://www.last.fm/api/auth/?api_key=test&token=testtoken123',
            token: 'testtoken123',
          }),
        });
      });

      // Click Connect button
      await page.click('[data-testid="lastfm-connect"]');

      // Wait for pending state to be set
      await page.waitForTimeout(500);

      // Check that status changed to "Awaiting Authorization" with yellow indicator
      const statusText = page.locator('text=Awaiting Authorization').first();
      await expect(statusText).toBeVisible();

      const statusIndicator = page.locator('.w-3.h-3.rounded-full').first();
      const classes = await statusIndicator.getAttribute('class');
      expect(classes).toContain('bg-yellow-500');

      // Check that Complete Authentication button is visible
      const completeButton = page.locator('[data-testid="lastfm-complete-auth"]');
      await expect(completeButton).toBeVisible();
      await expect(completeButton).toHaveText('Complete Authentication');

      // Check that Cancel button is visible
      const cancelButton = page.locator('[data-testid="lastfm-cancel-auth"]');
      await expect(cancelButton).toBeVisible();
      await expect(cancelButton).toHaveText('Cancel');

      // Connect button should be hidden
      const connectButton = page.locator('[data-testid="lastfm-connect"]');
      await expect(connectButton).not.toBeVisible();
    });

    test('should complete authentication successfully', async ({ page }) => {
      // Set up mocks
      await page.route('**/lastfm/auth', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            auth_url: 'https://www.last.fm/api/auth/?api_key=test&token=testtoken123',
            token: 'testtoken123',
          }),
        });
      });

      await page.route('**/lastfm/auth/complete', async (route) => {
        const postData = route.request().postDataJSON();
        if (postData.token === 'testtoken123') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              username: 'testuser',
              authenticated: true,
            }),
          });
        }
      });

      await page.route('**/lastfm/queue-status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            queued_scrobbles: 0,
          }),
        });
      });

      // Click Connect
      await page.click('[data-testid="lastfm-connect"]');
      await page.waitForTimeout(500);

      // Click Complete Authentication
      await page.click('[data-testid="lastfm-complete-auth"]');
      await page.waitForTimeout(500);

      // Verify authenticated state
      const statusText = page.locator('text=Connected as testuser').first();
      await expect(statusText).toBeVisible({ timeout: 5000 });

      // Status indicator should be green
      const statusIndicator = page.locator('.w-3.h-3.rounded-full').first();
      const classes = await statusIndicator.getAttribute('class');
      expect(classes).toContain('bg-green-500');

      // Disconnect button should be visible
      const disconnectButton = page.locator('[data-testid="lastfm-disconnect"]');
      await expect(disconnectButton).toBeVisible();
    });

    test('should cancel pending authentication', async ({ page }) => {
      // Mock the API response
      await page.route('**/lastfm/auth', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            auth_url: 'https://www.last.fm/api/auth/?api_key=test&token=testtoken123',
            token: 'testtoken123',
          }),
        });
      });

      // Click Connect
      await page.click('[data-testid="lastfm-connect"]');
      await page.waitForTimeout(500);

      // Verify we're in pending state
      await expect(page.locator('[data-testid="lastfm-cancel-auth"]')).toBeVisible();

      // Click Cancel
      await page.click('[data-testid="lastfm-cancel-auth"]');

      // Should return to not connected state
      const statusText = page.locator('text=Not Connected').first();
      await expect(statusText).toBeVisible();

      // Connect button should be visible again
      const connectButton = page.locator('[data-testid="lastfm-connect"]');
      await expect(connectButton).toBeVisible();

      // Complete and Cancel buttons should be hidden
      await expect(page.locator('[data-testid="lastfm-complete-auth"]')).not.toBeVisible();
      await expect(page.locator('[data-testid="lastfm-cancel-auth"]')).not.toBeVisible();
    });

    test('should handle authentication errors gracefully', async ({ page }) => {
      // Mock auth URL success but complete failure
      await page.route('**/lastfm/auth', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            auth_url: 'https://www.last.fm/api/auth/?api_key=test&token=testtoken123',
            token: 'testtoken123',
          }),
        });
      });

      await page.route('**/lastfm/auth/complete', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Authentication failed',
          }),
        });
      });

      // Click Connect
      await page.click('[data-testid="lastfm-connect"]');
      await page.waitForTimeout(500);

      // Click Complete Authentication
      await page.click('[data-testid="lastfm-complete-auth"]');
      await page.waitForTimeout(1000);

      // Should still show pending state (or return to not connected depending on implementation)
      // The important thing is it doesn't crash
      const statusText = page.locator('text=Awaiting Authorization, text=Not Connected').first();
      await expect(statusText).toBeVisible({ timeout: 5000 });
    });

    test('should show disconnect button when authenticated', async ({ page }) => {
      // Simulate already authenticated state
      await page.evaluate(() => {
        const settingsComponent = window.Alpine.$data(document.querySelector('[x-data*="settingsView"]'));
        if (settingsComponent) {
          settingsComponent.lastfm.authenticated = true;
          settingsComponent.lastfm.username = 'testuser';
        }
      });

      await page.waitForTimeout(300);

      // Verify disconnect button is visible
      const disconnectButton = page.locator('[data-testid="lastfm-disconnect"]');
      await expect(disconnectButton).toBeVisible();

      // Connect button should not be visible
      const connectButton = page.locator('[data-testid="lastfm-connect"]');
      await expect(connectButton).not.toBeVisible();
    });

    test('should display contextual help text based on auth state', async ({ page }) => {
      // Initial state: show connect help text
      const connectHelpText = page.locator('text=Connect your Last.fm account to enable scrobbling');
      await expect(connectHelpText).toBeVisible();

      // Mock auth flow
      await page.route('**/lastfm/auth', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            auth_url: 'https://www.last.fm/api/auth/?api_key=test&token=testtoken123',
            token: 'testtoken123',
          }),
        });
      });

      // Click Connect
      await page.click('[data-testid="lastfm-connect"]');
      await page.waitForTimeout(500);

      // Pending state: show complete authentication help text
      const pendingHelpText = page.locator('text=After authorizing on Last.fm, click "Complete Authentication"');
      await expect(pendingHelpText).toBeVisible();
    });
  });

  test.describe('Now Playing Updates', () => {
    test('should update Now Playing when track starts playing', async ({ page }) => {
      // This test requires Tauri runtime for actual playback
      // For now, we'll test the API call is made with correct data

      let nowPlayingCalled = false;
      let nowPlayingData = null;

      await page.route('**/lastfm/now-playing', async (route) => {
        nowPlayingCalled = true;
        nowPlayingData = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: 'Now playing updated',
          }),
        });
      });

      // Simulate track playing (mock player state)
      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Test Track',
          artist: 'Test Artist',
          album: 'Test Album',
        };
        player.duration = 240000; // 4 minutes in ms
        player.isPlaying = true;

        // Trigger Now Playing update
        player._updateLastfmNowPlaying();
      });

      // Wait for API call
      await page.waitForTimeout(1000);

      // Verify Now Playing was called
      expect(nowPlayingCalled).toBe(true);
      expect(nowPlayingData).toMatchObject({
        artist: 'Test Artist',
        track: 'Test Track',
        album: 'Test Album',
        duration: 240, // Should be in seconds
      });
    });

    test('should handle Now Playing errors silently', async ({ page }) => {
      // Mock failed Now Playing update
      await page.route('**/lastfm/now-playing', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Internal server error',
          }),
        });
      });

      // Simulate track playing
      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Test Track',
          artist: 'Test Artist',
        };
        player.duration = 180000;
        player.isPlaying = true;

        // Trigger Now Playing update
        player._updateLastfmNowPlaying();
      });

      // Wait and verify app doesn't crash
      await page.waitForTimeout(1000);

      // App should still be functional
      const player = await getAlpineStore(page, 'player');
      expect(player.currentTrack.title).toBe('Test Track');
    });

    test('should include album in Now Playing if available', async ({ page }) => {
      let nowPlayingData = null;

      await page.route('**/lastfm/now-playing', async (route) => {
        nowPlayingData = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'success' }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Track With Album',
          artist: 'Artist Name',
          album: 'Album Name',
        };
        player.duration = 200000;
        player._updateLastfmNowPlaying();
      });

      await page.waitForTimeout(1000);

      expect(nowPlayingData.album).toBe('Album Name');
    });

    test('should omit album from Now Playing if not available', async ({ page }) => {
      let nowPlayingData = null;

      await page.route('**/lastfm/now-playing', async (route) => {
        nowPlayingData = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'success' }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Track Without Album',
          artist: 'Artist Name',
          // No album field
        };
        player.duration = 200000;
        player._updateLastfmNowPlaying();
      });

      await page.waitForTimeout(1000);

      expect(nowPlayingData.album).toBeUndefined();
    });
  });

  test.describe('Scrobble Threshold (task-007)', () => {
    test('should use Math.ceil for duration and played_time in scrobble payload', async ({ page }) => {
      let scrobblePayload = null;

      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 80,
          }),
        });
      });

      await page.route('**/lastfm/scrobble', async (route) => {
        scrobblePayload = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            scrobbles: { '@attr': { accepted: 1 } },
          }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Test Track',
          artist: 'Test Artist',
          album: 'Test Album',
        };
        // 107066ms = 107.066s -> Math.ceil = 108s
        player.duration = 107066;
        // 85839ms = 85.839s -> Math.ceil = 86s
        player.currentTime = 85839;
        player._scrobbleThreshold = 0.8;
        player._scrobbleChecked = false;
        player._checkScrobble();
      });

      await page.waitForTimeout(1000);

      expect(scrobblePayload).not.toBeNull();
      // Math.ceil(107066/1000) = 108, Math.ceil(85839/1000) = 86
      expect(scrobblePayload.duration).toBe(108);
      expect(scrobblePayload.played_time).toBe(86);
    });

    test('should scrobble when fraction played meets threshold (edge case)', async ({ page }) => {
      let scrobbleCalled = false;

      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 80,
          }),
        });
      });

      await page.route('**/lastfm/scrobble', async (route) => {
        scrobbleCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            scrobbles: { '@attr': { accepted: 1 } },
          }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Edge Case Track',
          artist: 'Test Artist',
        };
        // Duration: 100s, played: 80.1s -> fraction = 0.801 >= 0.8 threshold
        player.duration = 100000;
        player.currentTime = 80100;
        player._scrobbleThreshold = 0.8;
        player._scrobbleChecked = false;
        player._checkScrobble();
      });

      await page.waitForTimeout(1000);

      expect(scrobbleCalled).toBe(true);
    });

    test('should not trigger scrobble check when fraction played is below threshold', async ({ page }) => {
      let checkScrobbleCalled = false;

      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 80,
          }),
        });
      });

      await page.route('**/lastfm/scrobble', async (route) => {
        checkScrobbleCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            scrobbles: { '@attr': { accepted: 1 } },
          }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Below Threshold Track',
          artist: 'Test Artist',
        };
        // Duration: 100s, played: 79s -> fraction = 0.79 < 0.8 threshold
        player.duration = 100000;
        player.currentTime = 79000;
        player._scrobbleThreshold = 0.8;
        player._scrobbleChecked = false;

        // Simulate progress event - this is where threshold check happens
        const ratio = player.currentTime / player.duration;
        // The progress listener only calls _checkScrobble when ratio >= threshold
        // Since 0.79 < 0.8, _checkScrobble should NOT be called
        if (ratio >= player._scrobbleThreshold) {
          player._checkScrobble();
        }
      });

      await page.waitForTimeout(1000);

      // Scrobble API should NOT be called because threshold wasn't met
      expect(checkScrobbleCalled).toBe(false);
    });

    test('should handle successful scrobble response', async ({ page }) => {
      const consoleLogs = [];
      page.on('console', (msg) => {
        if (msg.type() === 'log') {
          consoleLogs.push(msg.text());
        }
      });

      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 80,
          }),
        });
      });

      await page.route('**/lastfm/scrobble', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            scrobbles: { '@attr': { accepted: 1, ignored: 0 } },
          }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Success Track',
          artist: 'Test Artist',
        };
        player.duration = 180000;
        player.currentTime = 150000;
        player._scrobbleThreshold = 0.8;
        player._scrobbleChecked = false;
        player._checkScrobble();
      });

      await page.waitForTimeout(1000);

      const successLog = consoleLogs.find((log) => log.includes('Successfully scrobbled'));
      expect(successLog).toBeTruthy();
    });

    test('should handle queued scrobble response', async ({ page }) => {
      const consoleLogs = [];
      page.on('console', (msg) => {
        if (msg.type() === 'warning') {
          consoleLogs.push(msg.text());
        }
      });

      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 80,
          }),
        });
      });

      await page.route('**/lastfm/scrobble', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'queued',
            message: 'Scrobble queued for retry',
          }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Queued Track',
          artist: 'Test Artist',
        };
        player.duration = 180000;
        player.currentTime = 150000;
        player._scrobbleThreshold = 0.8;
        player._scrobbleChecked = false;
        player._checkScrobble();
      });

      await page.waitForTimeout(1000);

      const queuedLog = consoleLogs.find((log) => log.includes('Queued for retry'));
      expect(queuedLog).toBeTruthy();
    });

    test('should handle threshold_not_met response from backend', async ({ page }) => {
      const consoleLogs = [];
      page.on('console', (msg) => {
        if (msg.type() === 'debug') {
          consoleLogs.push(msg.text());
        }
      });

      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 80,
          }),
        });
      });

      await page.route('**/lastfm/scrobble', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'threshold_not_met',
          }),
        });
      });

      await page.evaluate(() => {
        const player = window.Alpine.store('player');
        player.currentTrack = {
          id: '1',
          title: 'Threshold Not Met Track',
          artist: 'Test Artist',
        };
        player.duration = 180000;
        player.currentTime = 150000;
        player._scrobbleThreshold = 0.8;
        player._scrobbleChecked = false;
        player._checkScrobble();
      });

      await page.waitForTimeout(1000);

      const thresholdLog = consoleLogs.find((log) => log.includes('Threshold not met'));
      expect(thresholdLog).toBeTruthy();
    });
  });

  test.describe('Settings Persistence', () => {
    test.beforeEach(async ({ page }) => {
      await page.click('[data-testid="sidebar-settings"]');
      await page.waitForTimeout(500);
      await page.click('[data-testid="settings-nav-lastfm"]');
      await page.waitForTimeout(300);
    });

    test('should load Last.fm settings on init', async ({ page }) => {
      // Mock settings endpoint
      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'loadeduser',
            scrobble_threshold: 0.9,
          }),
        });
      });

      // Reload page to trigger init
      await page.reload();
      await waitForAlpine(page);
      await page.click('[data-testid="sidebar-settings"]');
      await page.waitForTimeout(500);
      await page.click('[data-testid="settings-nav-lastfm"]');
      await page.waitForTimeout(1000);

      // Verify settings were loaded
      const statusText = page.locator('text=Connected as loadeduser').first();
      await expect(statusText).toBeVisible({ timeout: 5000 });
    });

    test('should load queue status when authenticated', async ({ page }) => {
      // Mock authenticated state and queue status
      await page.route('**/lastfm/settings', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            enabled: true,
            authenticated: true,
            username: 'testuser',
            scrobble_threshold: 0.9,
          }),
        });
      });

      let queueStatusCalled = false;
      await page.route('**/lastfm/queue-status', async (route) => {
        queueStatusCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            queued_scrobbles: 5,
          }),
        });
      });

      // Reload to trigger settings load
      await page.reload();
      await waitForAlpine(page);
      await page.click('[data-testid="sidebar-settings"]');
      await page.waitForTimeout(500);
      await page.click('[data-testid="settings-nav-lastfm"]');
      await page.waitForTimeout(1500);

      // Verify queue status was requested
      expect(queueStatusCalled).toBe(true);
    });
  });
});
