import { test, expect } from '@playwright/test';
import { waitForAlpine } from './fixtures/helpers.js';

test.describe('Library Settings UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);

    await page.click('[data-testid="sidebar-settings"]');
    await page.waitForSelector('[data-testid="settings-nav-library"]', { state: 'visible' });
  });

  test('should display Library nav item in settings sidebar', async ({ page }) => {
    const libraryNav = page.locator('[data-testid="settings-nav-library"]');
    await expect(libraryNav).toBeVisible();
    await expect(libraryNav).toHaveText('Library');
  });

  test('should navigate to Library section when clicked', async ({ page }) => {
    await page.click('[data-testid="settings-nav-library"]');
    const librarySection = page.locator('[data-testid="settings-section-library"]');
    await expect(librarySection).toBeVisible();
  });

  test('should display Reconciliation Scan subsection', async ({ page }) => {
    await page.click('[data-testid="settings-nav-library"]');

    const librarySection = page.locator('[data-testid="settings-section-library"]');
    await expect(librarySection).toBeVisible();

    const scanTitle = librarySection.locator('text=Reconciliation Scan');
    await expect(scanTitle).toBeVisible();

    const scanDescription = librarySection.locator('text=Update file fingerprints');
    await expect(scanDescription).toBeVisible();
  });

  test('should display Run Scan button', async ({ page }) => {
    await page.click('[data-testid="settings-nav-library"]');

    const scanButton = page.locator('[data-testid="settings-reconcile-scan"]');
    await expect(scanButton).toBeVisible();
    await expect(scanButton).toHaveText('Run Scan');
  });
});

test.describe('Library Settings with Mocked Tauri', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.__TAURI__ = {
        core: {
          invoke: async (cmd) => {
            if (cmd === 'library_reconcile_scan') {
              return {
                backfilled: 5,
                duplicates_merged: 2,
                errors: 0,
              };
            }
            if (cmd === 'app_get_info') {
              return { version: 'test', build: 'test', platform: 'test' };
            }
            if (cmd === 'watched_folders_list') {
              return [];
            }
            if (cmd === 'lastfm_get_settings') {
              return { enabled: false, authenticated: false, scrobble_threshold: 90 };
            }
            return null;
          },
        },
        dialog: {
          confirm: async () => true,
        },
      };
    });

    await page.goto('/');
    await waitForAlpine(page);

    await page.click('[data-testid="sidebar-settings"]');
    await page.click('[data-testid="settings-nav-library"]');
    await page.waitForSelector('[data-testid="settings-section-library"]', { state: 'visible' });
  });

  test('should run reconcile scan and display results', async ({ page }) => {
    const scanButton = page.locator('[data-testid="settings-reconcile-scan"]');
    await scanButton.click();

    await page.waitForSelector('text=Last scan results:', { state: 'visible' });

    const resultsSection = page.locator('[data-testid="settings-section-library"]');
    await expect(resultsSection.locator('text=Backfilled')).toBeVisible();
    await expect(resultsSection.locator('text=Duplicates Merged')).toBeVisible();
    await expect(resultsSection.locator('text=Errors')).toBeVisible();
  });

  test('should disable button while scanning', async ({ page }) => {
    await page.addInitScript(() => {
      const originalInvoke = window.__TAURI__.core.invoke;
      window.__TAURI__.core.invoke = async (cmd, args) => {
        if (cmd === 'library_reconcile_scan') {
          await new Promise((resolve) => setTimeout(resolve, 500));
          return { backfilled: 0, duplicates_merged: 0, errors: 0 };
        }
        return originalInvoke(cmd, args);
      };
    });

    await page.reload();
    await waitForAlpine(page);
    await page.click('[data-testid="sidebar-settings"]');
    await page.click('[data-testid="settings-nav-library"]');

    const scanButton = page.locator('[data-testid="settings-reconcile-scan"]');
    await scanButton.click();

    await expect(scanButton).toBeDisabled();
  });
});
