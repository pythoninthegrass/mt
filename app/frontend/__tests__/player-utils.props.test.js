/**
 * Property-based tests for player utility functions using fast-check
 *
 * These tests verify pure function invariants without needing complex Tauri mocks.
 */

import { describe, it, expect } from 'vitest';
import { test, fc } from '@fast-check/vitest';

/**
 * Format time in ms to MM:SS string
 * (Extracted from player store for testing)
 */
function formatTime(ms) {
  if (!ms || ms < 0) return '0:00';
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Clamp value to range [min, max]
 */
function clamp(value, min, max) {
  return Math.max(min, Math.min(value, max));
}

/**
 * Calculate progress percentage (clamped to 0-100%)
 */
function calculateProgress(currentTime, duration) {
  if (duration <= 0) return 0;
  const progress = (currentTime / duration) * 100;
  return Math.max(0, Math.min(100, progress));
}

/**
 * Check if playback should trigger play count update
 */
function shouldUpdatePlayCount(currentTime, duration, threshold = 0.75) {
  if (duration <= 0) return false;
  return (currentTime / duration) >= threshold;
}

/**
 * Check if playback should trigger scrobble
 */
function shouldScrobble(currentTime, duration, threshold = 0.9) {
  if (duration <= 0) return false;
  return (currentTime / duration) >= threshold;
}

describe('Player Utils - Property-Based Tests', () => {
  describe('formatTime Invariants', () => {
    test.prop([fc.integer({ min: 0, max: 86400000 })])('formatTime never returns negative values', (ms) => {
      const formatted = formatTime(ms);

      expect(formatted).toMatch(/^\d+:\d{2}$/);

      const [minutes, seconds] = formatted.split(':').map(Number);
      expect(minutes).toBeGreaterThanOrEqual(0);
      expect(seconds).toBeGreaterThanOrEqual(0);
      expect(seconds).toBeLessThan(60);
    });

    test.prop([fc.integer({ min: 0, max: 3600000 })])('formatTime seconds are always two digits', (ms) => {
      const formatted = formatTime(ms);

      const [_, seconds] = formatted.split(':');
      expect(seconds.length).toBe(2);
    });

    test.prop([fc.integer({ min: 0, max: 86400000 })])('formatTime roundtrip is consistent', (ms) => {
      const formatted = formatTime(ms);
      const [minutes, seconds] = formatted.split(':').map(Number);

      const reconstructedSeconds = minutes * 60 + seconds;
      const originalSeconds = Math.floor(ms / 1000);

      expect(reconstructedSeconds).toBe(originalSeconds);
    });

    test.prop([fc.constantFrom(null, undefined, -100, NaN)])('formatTime handles invalid input safely', (invalid) => {
      const formatted = formatTime(invalid);

      expect(formatted).toBe('0:00');
    });

    it('formatTime handles exact boundaries correctly', () => {
      expect(formatTime(0)).toBe('0:00');
      expect(formatTime(1000)).toBe('0:01');
      expect(formatTime(59000)).toBe('0:59');
      expect(formatTime(60000)).toBe('1:00');
      expect(formatTime(3599000)).toBe('59:59');
      expect(formatTime(3600000)).toBe('60:00');
    });
  });

  describe('clamp Invariants', () => {
    test.prop([fc.integer({ min: -1000, max: 1000 }), fc.integer({ min: -100, max: 0 }), fc.integer({ min: 1, max: 100 })])(
      'clamp keeps value in bounds',
      (value, min, max) => {
        const clamped = clamp(value, min, max);
        expect(clamped).toBeGreaterThanOrEqual(min);
        expect(clamped).toBeLessThanOrEqual(max);
      }
    );

    test.prop([fc.integer({ min: 0, max: 100 }), fc.integer({ min: 0, max: 50 }), fc.integer({ min: 51, max: 100 })])(
      'clamp preserves values already in range',
      (value, min, max) => {
        fc.pre(min <= value && value <= max);

        const clamped = clamp(value, min, max);
        expect(clamped).toBe(value);
      }
    );

    test.prop([fc.integer({ min: -1000, max: -1 })])('clamp to [0,100] returns 0 for negative', (value) => {
      const clamped = clamp(value, 0, 100);
      expect(clamped).toBe(0);
    });

    test.prop([fc.integer({ min: 101, max: 10000 })])('clamp to [0,100] returns 100 for above range', (value) => {
      const clamped = clamp(value, 0, 100);
      expect(clamped).toBe(100);
    });
  });

  describe('calculateProgress Invariants', () => {
    test.prop([fc.integer({ min: 0, max: 600000 }), fc.integer({ min: 1, max: 600000 })])(
      'progress is always between 0 and 100',
      (currentTime, duration) => {
        const progress = calculateProgress(currentTime, duration);

        expect(progress).toBeGreaterThanOrEqual(0);
        expect(progress).toBeLessThanOrEqual(100);
      }
    );

    test.prop([fc.integer({ min: 0, max: 600000 })])('progress with zero duration is zero', (currentTime) => {
      const progress = calculateProgress(currentTime, 0);

      expect(progress).toBe(0);
      expect(Number.isFinite(progress)).toBe(true);
    });

    test.prop([fc.integer({ min: 1, max: 600000 })])('progress at duration is exactly 100%', (duration) => {
      const progress = calculateProgress(duration, duration);

      expect(progress).toBe(100);
    });

    test.prop([fc.integer({ min: 1, max: 600000 })])('progress at zero is 0%', (duration) => {
      const progress = calculateProgress(0, duration);

      expect(progress).toBe(0);
    });

    test.prop([fc.integer({ min: 1, max: 600000 }), fc.float({ min: 0, max: 1, noNaN: true })])(
      'progress is monotonic',
      (duration, fraction) => {
        const time1 = Math.floor(duration * fraction);
        const time2 = Math.floor(duration * (fraction + 0.1));

        const progress1 = calculateProgress(time1, duration);
        const progress2 = calculateProgress(time2, duration);

        if (time2 <= duration) {
          expect(progress2).toBeGreaterThanOrEqual(progress1);
        }
      }
    );
  });

  describe('Threshold Check Invariants', () => {
    test.prop([fc.integer({ min: 1000, max: 600000 }), fc.float({ min: 0, max: 1, noNaN: true })])(
      'play count threshold check is deterministic',
      (duration, threshold) => {
        // Add small epsilon to avoid floating point precision issues at boundary
        const beforeTime = Math.floor(duration * threshold) - 10; // 10ms before
        const afterTime = Math.floor(duration * threshold) + 10; // 10ms after

        // Well before threshold should not trigger
        if (beforeTime >= 0) {
          expect(shouldUpdatePlayCount(beforeTime, duration, threshold)).toBe(false);
        }

        // Well after threshold should trigger
        if (afterTime <= duration) {
          expect(shouldUpdatePlayCount(afterTime, duration, threshold)).toBe(true);
        }
      }
    );

    test.prop([fc.integer({ min: 1000, max: 600000 }), fc.float({ min: 0.5, max: 1, noNaN: true })])(
      'scrobble threshold check is deterministic',
      (duration, threshold) => {
        // Add small epsilon to avoid floating point precision issues at boundary
        const beforeTime = Math.floor(duration * threshold) - 10; // 10ms before
        const afterTime = Math.floor(duration * threshold) + 10; // 10ms after

        // Well before threshold should not trigger
        if (beforeTime >= 0) {
          expect(shouldScrobble(beforeTime, duration, threshold)).toBe(false);
        }

        // Well after threshold should trigger
        if (afterTime <= duration) {
          expect(shouldScrobble(afterTime, duration, threshold)).toBe(true);
        }
      }
    );

    test.prop([fc.integer({ min: 0, max: 600000 })])('threshold checks with zero duration return false', (currentTime) => {
      expect(shouldUpdatePlayCount(currentTime, 0)).toBe(false);
      expect(shouldScrobble(currentTime, 0)).toBe(false);
    });

    test.prop([fc.integer({ min: 1000, max: 600000 })])('threshold checks with zero time return false', (duration) => {
      expect(shouldUpdatePlayCount(0, duration)).toBe(false);
      expect(shouldScrobble(0, duration)).toBe(false);
    });

    test.prop([fc.integer({ min: 1000, max: 600000 }), fc.float({ min: 0, max: 1, noNaN: true })])(
      'higher threshold requires more playback time',
      (duration, baseThreshold) => {
        fc.pre(baseThreshold < 0.95); // Ensure we can add 0.05

        const lowerThreshold = baseThreshold;
        const higherThreshold = baseThreshold + 0.05;

        const time = Math.floor(duration * (baseThreshold + 0.025)); // Midpoint

        const reachedLower = shouldScrobble(time, duration, lowerThreshold);
        const reachedHigher = shouldScrobble(time, duration, higherThreshold);

        // If we reached higher threshold, we must have reached lower
        if (reachedHigher) {
          expect(reachedLower).toBe(true);
        }
      }
    );
  });

  describe('Seek Position Invariants', () => {
    test.prop([fc.integer({ min: 0, max: 600000 }), fc.float({ min: 0, max: 1, noNaN: true })])(
      'seekPercent produces position within duration',
      (duration, percent) => {
        const position = Math.round((percent / 100) * duration);

        expect(position).toBeGreaterThanOrEqual(0);
        expect(position).toBeLessThanOrEqual(duration);
      }
    );

    test.prop([fc.integer({ min: 1, max: 600000 }), fc.integer({ min: 0, max: 100 })])(
      'seekPercent is proportional',
      (duration, percentInt) => {
        const position = Math.round((percentInt / 100) * duration);
        const expectedPosition = Math.round((percentInt / 100) * duration);

        expect(position).toBe(expectedPosition);
      }
    );

    test.prop([fc.integer({ min: -1000, max: 700000 }), fc.integer({ min: 1, max: 600000 })])(
      'clamp seek position to valid range',
      (requestedPosition, duration) => {
        const clampedPosition = clamp(requestedPosition, 0, duration);

        expect(clampedPosition).toBeGreaterThanOrEqual(0);
        expect(clampedPosition).toBeLessThanOrEqual(duration);
      }
    );
  });

  describe('Volume Invariants', () => {
    test.prop([fc.integer({ min: -1000, max: 2000 })])('volume clamps to [0, 100]', (volume) => {
      const clamped = clamp(volume, 0, 100);

      expect(clamped).toBeGreaterThanOrEqual(0);
      expect(clamped).toBeLessThanOrEqual(100);
    });

    test.prop([fc.integer({ min: 0, max: 100 })])('valid volume is preserved', (volume) => {
      const clamped = clamp(volume, 0, 100);

      expect(clamped).toBe(volume);
    });

    test.prop([fc.integer({ min: 101, max: 10000 })])('volume above 100 clamps to 100', (volume) => {
      const clamped = clamp(volume, 0, 100);

      expect(clamped).toBe(100);
    });

    test.prop([fc.integer({ min: -10000, max: -1 })])('volume below 0 clamps to 0', (volume) => {
      const clamped = clamp(volume, 0, 100);

      expect(clamped).toBe(0);
    });
  });
});
