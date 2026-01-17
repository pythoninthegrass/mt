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
    
    // Coverage (optional, can enable later)
    // coverage: {
    //   provider: 'v8',
    //   include: ['js/**/*.js'],
    // },
    
    // Globals (describe, it, expect) available without imports
    globals: true,
  },
});
