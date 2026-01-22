/**
 * Tauri Event System for real-time updates
 *
 * This module centralizes all Tauri event subscriptions, replacing the WebSocket
 * connection from the Python backend. Events are emitted from the Rust backend
 * using app.emit() and received here using window.__TAURI__.event.listen().
 *
 * Event naming convention: `domain:action` (e.g., `library:updated`)
 */

const { listen } = window.__TAURI__?.event ?? { listen: async () => () => {} };

// Store unlisten functions for cleanup
const listeners = [];

/**
 * Event names matching Rust backend events
 */
export const Events = {
  // Library events
  LIBRARY_UPDATED: 'library:updated',
  SCAN_PROGRESS: 'library:scan-progress',
  SCAN_COMPLETE: 'library:scan-complete',

  // Queue events
  QUEUE_UPDATED: 'queue:updated',

  // Favorites events
  FAVORITES_UPDATED: 'favorites:updated',

  // Playlist events
  PLAYLISTS_UPDATED: 'playlists:updated',

  // Settings events
  SETTINGS_UPDATED: 'settings:updated',
};

/**
 * Subscribe to a Tauri event
 * @param {string} event - Event name
 * @param {Function} callback - Callback function receiving event payload
 * @returns {Promise<Function>} Unlisten function
 */
export async function subscribe(event, callback) {
  const unlisten = await listen(event, (e) => {
    console.debug(`[events] ${event}:`, e.payload);
    callback(e.payload);
  });
  listeners.push(unlisten);
  return unlisten;
}

/**
 * Initialize all event listeners
 * Call this during app startup to set up event handlers
 * @param {object} Alpine - Alpine.js instance
 */
export async function initEventListeners(Alpine) {
  console.log('[events] Initializing Tauri event listeners...');

  // Library updated event
  await subscribe(Events.LIBRARY_UPDATED, (payload) => {
    const { action, track_ids } = payload;
    const library = Alpine.store('library');

    console.log(`[events] Library ${action}:`, track_ids.length ? `${track_ids.length} tracks` : 'bulk update');

    // Refresh library data based on action
    if (action === 'added' || action === 'modified' || action === 'deleted') {
      // If no track_ids, it's a bulk operation - full refresh
      // If track_ids present, could do targeted update in the future
      library.fetchTracks();
    }
  });

  // Scan progress event
  await subscribe(Events.SCAN_PROGRESS, (payload) => {
    const { job_id, status, scanned, found, errors, current_path } = payload;
    const library = Alpine.store('library');

    // Update scan progress in library store
    if (library.setScanProgress) {
      library.setScanProgress({
        jobId: job_id,
        status,
        scanned,
        found,
        errors,
        currentPath: current_path,
      });
    }
  });

  // Scan complete event
  await subscribe(Events.SCAN_COMPLETE, (payload) => {
    const { job_id, added, skipped, errors, duration_ms } = payload;
    const library = Alpine.store('library');

    console.log(`[events] Scan complete: ${added} added, ${skipped} skipped, ${errors} errors (${duration_ms}ms)`);

    // Clear scan progress and refresh library
    if (library.clearScanProgress) {
      library.clearScanProgress();
    }
    library.fetchTracks();
  });

  // Queue updated event - DISABLED
  // The frontend manages queue state locally and the backend events were causing
  // race conditions with playback. The queue store already syncs changes to the
  // backend via API calls, so we don't need to react to backend events.
  // If external queue changes are needed in the future (e.g., multi-device sync),
  // this will need careful synchronization to avoid interfering with playback.

  // Favorites updated event
  await subscribe(Events.FAVORITES_UPDATED, (payload) => {
    const { action, track_id } = payload;
    const library = Alpine.store('library');
    const player = Alpine.store('player');

    console.log(`[events] Favorites ${action}: track ${track_id}`);

    // Refresh library if showing liked songs
    if (library.refreshIfLikedSongs) {
      library.refreshIfLikedSongs();
    }

    // Update player favorite status if currently playing this track
    if (player.currentTrack?.id === track_id) {
      player.isFavorite = action === 'added';
    }
  });

  // Playlists updated event
  await subscribe(Events.PLAYLISTS_UPDATED, (payload) => {
    const { action, playlist_id, track_ids } = payload;
    const library = Alpine.store('library');

    console.log(`[events] Playlists ${action}: playlist ${playlist_id}`);

    // Refresh playlists
    if (library.loadPlaylists) {
      library.loadPlaylists();
    }

    // If showing this playlist, refresh its tracks
    if (library.activePlaylistId === playlist_id && library.loadPlaylistTracks) {
      library.loadPlaylistTracks(playlist_id);
    }
  });

  // Settings updated event
  await subscribe(Events.SETTINGS_UPDATED, (payload) => {
    const { key, value, previous_value } = payload;

    console.log(`[events] Settings ${key}:`, value, previous_value ? `(was: ${previous_value})` : '');

    // Handle specific settings changes
    // This could trigger UI updates or refresh relevant stores
    // For now, we just log the change
  });

  console.log('[events] Tauri event listeners initialized');
}

/**
 * Cleanup all event listeners
 * Call this when the app is closing
 */
export function cleanupEventListeners() {
  console.log('[events] Cleaning up event listeners...');
  listeners.forEach((unlisten) => unlisten());
  listeners.length = 0;
}

export default {
  Events,
  subscribe,
  initEventListeners,
  cleanupEventListeners,
};
