/**
 * Setup file for player property tests
 * This must run BEFORE player.js is imported
 */

import { vi, beforeAll } from 'vitest';

// Setup window mock BEFORE any imports
beforeAll(() => {
  const invokeReturns = {
    audio_get_status: { volume: 1.0 },
    audio_load: { duration_ms: 180000 },
  };

  global.window = {
    __TAURI__: {
      core: {
        invoke: vi.fn((cmd, args) => {
          if (cmd === 'audio_seek') return Promise.resolve();
          if (cmd === 'audio_set_volume') return Promise.resolve();
          if (cmd === 'audio_stop') return Promise.resolve();
          if (cmd === 'audio_play') return Promise.resolve();
          if (cmd === 'audio_pause') return Promise.resolve();
          return Promise.resolve(invokeReturns[cmd] || {});
        })
      },
      event: {
        listen: vi.fn((event, callback) => {
          return Promise.resolve(() => {});
        })
      }
    }
  };
});

// Mock API
vi.mock('../js/api.js', () => ({
  api: {
    favorites: {
      check: vi.fn().mockResolvedValue({ is_favorite: false }),
      add: vi.fn().mockResolvedValue({}),
      remove: vi.fn().mockResolvedValue({}),
    },
    library: {
      getArtwork: vi.fn().mockResolvedValue(null),
      updatePlayCount: vi.fn().mockResolvedValue({}),
    },
    lastfm: {
      getSettings: vi.fn().mockResolvedValue({ enabled: false, authenticated: false, scrobble_threshold: 90 }),
      updateNowPlaying: vi.fn().mockResolvedValue({ status: 'disabled' }),
      scrobble: vi.fn().mockResolvedValue({ status: 'disabled' }),
    }
  }
}));
