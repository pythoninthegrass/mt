/**
 * Shared utility functions for formatting time, data sizes, and other display values.
 *
 * Consolidates formatting logic used across player, player-controls, and metadata components.
 */

/**
 * Format milliseconds as M:SS
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted time (e.g., "3:45", "0:00")
 */
export function formatTime(ms) {
  if (!ms || ms < 0) return '0:00';
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Format seconds as M:SS (for duration values in seconds)
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted time (e.g., "3:45", "0:00")
 */
export function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '0:00';
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format bytes as human-readable size
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size (e.g., "4.2 MB", "1.5 GB")
 */
export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = (bytes / Math.pow(k, i)).toFixed(1);
  return `${size} ${units[i]}`;
}

/**
 * Format bitrate as kbps
 * @param {number} bitrate - Bitrate in bits per second
 * @returns {string} Formatted bitrate (e.g., "320 kbps")
 */
export function formatBitrate(bitrate) {
  if (!bitrate) return '—';
  return `${bitrate} kbps`;
}

/**
 * Format sample rate as Hz
 * @param {number} sampleRate - Sample rate in Hz
 * @returns {string} Formatted sample rate (e.g., "44100 Hz")
 */
export function formatSampleRate(sampleRate) {
  if (!sampleRate) return '—';
  return `${sampleRate} Hz`;
}
