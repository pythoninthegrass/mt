import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for mt Tauri application E2E testing
 *
 * This configuration is designed for testing the Tauri + Alpine.js frontend
 * during the hybrid architecture phase (Python PEX sidecar backend).
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory (relative to app/frontend where this config lives)
  testDir: './tests',

  // Test file patterns
  testMatch: '**/*.spec.js',

  // Maximum time one test can run for
  timeout: 60000,

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: '../../playwright-report' }],
    ['list'],
    // Add JUnit reporter for CI
    ...(process.env.CI ? [['junit', { outputFile: '../../test-results/junit.xml' }]] : [])
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL for testing (Vite dev server)
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:5173',

    // Collect trace on failure (useful for debugging)
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Default viewport for desktop testing (minimum recommended size)
    viewport: { width: 1624, height: 1057 },

    // Emulate browser timezone
    timezoneId: 'America/Chicago',

    // Default timeout for actions (click, fill, etc.)
    actionTimeout: 10000,

    // Default timeout for navigation
    navigationTimeout: 30000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1624, height: 1057 }
      },
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1624, height: 1057 }
      },
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1624, height: 1057 }
      },
    },
  ],

  // Run dev server before starting tests
  // Note: When running from Taskfile, we're already in app/frontend
  webServer: process.env.PLAYWRIGHT_SKIP_WEBSERVER ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    stdout: 'ignore',
    stderr: 'pipe',
  },

  // Global setup/teardown
  // globalSetup: './tests/e2e/global-setup.js',
  // globalTeardown: './tests/e2e/global-teardown.js',
});
