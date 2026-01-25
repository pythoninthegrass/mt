import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Use jsdom for any DOM-related utilities (though we're testing stores, not UI)
    environment: 'node',

    // Test file patterns - property tests go in __tests__ directory
    include: ['__tests__/**/*.{test,spec}.{js,mjs,ts}'],

    // Exclude Playwright E2E tests (they have their own config)
    exclude: ['tests/**/*', 'node_modules/**/*'],

    // Reporter configuration
    reporters: ['default'],

    // Coverage configuration
    // NOTE: The 80% coverage target for frontend is primarily achieved through
    // Playwright E2E tests. Unit tests here focus on store logic and edge cases.
    // Per-file thresholds are set for actively tested modules.
    coverage: {
      provider: 'v8',
      include: ['js/**/*.js'],
      exclude: [
        'js/**/*.test.js',
        'js/**/*.spec.js',
        'node_modules/**',
      ],
      // Report formats
      reporter: ['text', 'text-summary', 'html', 'json-summary'],
      // Output directory
      reportsDirectory: './coverage',
      // Still generate report even with test failures
      reportOnFailure: true,
      // Per-file thresholds for actively tested modules
      thresholds: {
        // queue.js is the primary unit-tested module (~40% coverage)
        'js/stores/queue.js': {
          lines: 35,
          functions: 35,
          branches: 30,
          statements: 35,
        },
      },
    },

    // Globals (describe, it, expect) available without imports
    globals: true,
  },
});
