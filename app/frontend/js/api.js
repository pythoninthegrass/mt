/**
 * Backend API Client
 *
 * Hybrid client that uses:
 * - Tauri commands for library operations (Rust backend)
 * - HTTP requests for operations still on Python FastAPI sidecar
 */

let API_BASE = 'http://127.0.0.1:8765/api';

export function setApiBase(url) {
  API_BASE = url;
}

// Get Tauri invoke function if available
const invoke = window.__TAURI__?.core?.invoke;

/**
 * Make an API request with error handling
 * @param {string} endpoint - API endpoint (e.g., '/library/tracks')
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }

    // Handle empty responses
    const text = await response.text();
    return text ? JSON.parse(text) : null;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network error or other fetch failure
    throw new ApiError(0, `Network error: ${error.message}`);
  }
}

/**
 * Custom API error class
 */
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * API client object with all endpoints
 */
export const api = {
  /**
   * Health check
   * @returns {Promise<{status: string}>}
   */
  async health() {
    return request('/health');
  },

  // ============================================
  // Library endpoints
  // ============================================

  library: {
    /**
     * Get all tracks in library (uses Tauri command)
     * @param {object} params - Query parameters
     * @param {string} [params.search] - Search query
     * @param {string} [params.sort] - Sort field
     * @param {string} [params.order] - Sort order ('asc' or 'desc')
     * @param {number} [params.limit] - Max results
     * @param {number} [params.offset] - Offset for pagination
     * @returns {Promise<{tracks: Array, total: number, limit: number, offset: number}>}
     */
    async getTracks(params = {}) {
      if (invoke) {
        try {
          return await invoke('library_get_all', {
            search: params.search || null,
            artist: params.artist || null,
            album: params.album || null,
            sortBy: params.sort || null,
            sortOrder: params.order || null,
            limit: params.limit || null,
            offset: params.offset || null,
          });
        } catch (error) {
          console.error('[api.library.getTracks] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      // Fallback to HTTP
      const query = new URLSearchParams();
      if (params.search) query.set('search', params.search);
      if (params.sort) query.set('sort_by', params.sort);
      if (params.order) query.set('sort_order', params.order);
      if (params.limit) query.set('limit', params.limit.toString());
      if (params.offset) query.set('offset', params.offset.toString());
      const queryString = query.toString();
      return request(`/library${queryString ? `?${queryString}` : ''}`);
    },

    /**
     * Get a single track by ID (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<object|null>} Track object or null
     */
    async getTrack(id) {
      if (invoke) {
        try {
          return await invoke('library_get_track', { trackId: id });
        } catch (error) {
          console.error('[api.library.getTrack] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}`);
    },

    /**
     * Scan paths for music files and add to library (uses Tauri command)
     * @param {string[]} paths - File or directory paths to scan
     * @param {boolean} [recursive=true] - Scan subdirectories
     * @returns {Promise<{added_count: number, modified_count: number, unchanged_count: number, deleted_count: number, error_count: number}>}
     */
    async scan(paths, recursive = true) {
      if (invoke) {
        try {
          const result = await invoke('scan_paths_to_library', { paths, recursive });
          // Map response to expected format
          return {
            added: result.added_count || 0,
            skipped: result.unchanged_count || 0,
            errors: result.error_count || 0,
            tracks: [],  // The new API doesn't return tracks
          };
        } catch (error) {
          console.error('[api.library.scan] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request('/library/scan', {
        method: 'POST',
        body: JSON.stringify({ paths, recursive }),
      });
    },

    /**
     * Get library statistics (uses Tauri command)
     * @returns {Promise<{total_tracks: number, total_duration: number, total_size: number, total_artists: number, total_albums: number}>}
     */
    async getStats() {
      if (invoke) {
        try {
          return await invoke('library_get_stats');
        } catch (error) {
          console.error('[api.library.getStats] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request('/library/stats');
    },

    /**
     * Delete a track from library (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<boolean>} True if deleted
     */
    async deleteTrack(id) {
      if (invoke) {
        try {
          return await invoke('library_delete_track', { trackId: id });
        } catch (error) {
          console.error('[api.library.deleteTrack] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
    },

    /**
     * Update play count for a track (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async updatePlayCount(id) {
      if (invoke) {
        try {
          return await invoke('library_update_play_count', { trackId: id });
        } catch (error) {
          console.error('[api.library.updatePlayCount] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}/play-count`, {
        method: 'PUT',
      });
    },

    /**
     * Rescan a track's metadata from its file (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async rescanTrack(id) {
      if (invoke) {
        try {
          return await invoke('library_rescan_track', { trackId: id });
        } catch (error) {
          console.error('[api.library.rescanTrack] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}/rescan`, {
        method: 'PUT',
      });
    },

    /**
     * Get album artwork for a track (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<{data: string, mime_type: string, source: string}|null>}
     */
    async getArtwork(id) {
      if (invoke) {
        try {
          return await invoke('library_get_artwork', { trackId: id });
        } catch (error) {
          // Not found is returned as null, not an error
          if (error.toString().includes('not found')) {
            return null;
          }
          console.error('[api.library.getArtwork] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      try {
        return await request(`/library/${encodeURIComponent(id)}/artwork`);
      } catch (error) {
        if (error.status === 404) {
          return null;
        }
        throw error;
      }
    },

    /**
     * Get artwork as data URL for use in img src (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<string|null>} Data URL or null
     */
    async getArtworkUrl(id) {
      if (invoke) {
        try {
          return await invoke('library_get_artwork_url', { trackId: id });
        } catch (error) {
          if (error.toString().includes('not found')) {
            return null;
          }
          console.error('[api.library.getArtworkUrl] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      // HTTP fallback - get artwork and convert to data URL
      const artwork = await this.getArtwork(id);
      if (artwork && artwork.data) {
        return `data:${artwork.mime_type};base64,${artwork.data}`;
      }
      return null;
    },

    /**
     * Get all tracks marked as missing (uses Tauri command)
     * @returns {Promise<{tracks: Array, total: number}>}
     */
    async getMissing() {
      if (invoke) {
        try {
          return await invoke('library_get_missing');
        } catch (error) {
          console.error('[api.library.getMissing] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request('/library/missing');
    },

    /**
     * Locate a missing track by providing a new file path (uses Tauri command)
     * @param {number} id - Track ID
     * @param {string} newPath - New file path
     * @returns {Promise<object>} Updated track object
     */
    async locate(id, newPath) {
      if (invoke) {
        try {
          return await invoke('library_locate_track', { trackId: id, newPath });
        } catch (error) {
          console.error('[api.library.locate] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}/locate`, {
        method: 'POST',
        body: JSON.stringify({ new_path: newPath }),
      });
    },

    /**
     * Check if a track's file exists and update its missing status (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<object>} Updated track object with current missing status
     */
    async checkStatus(id) {
      if (invoke) {
        try {
          return await invoke('library_check_status', { trackId: id });
        } catch (error) {
          console.error('[api.library.checkStatus] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}/check-status`, {
        method: 'POST',
      });
    },

    /**
     * Mark a track as missing (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async markMissing(id) {
      if (invoke) {
        try {
          return await invoke('library_mark_missing', { trackId: id });
        } catch (error) {
          console.error('[api.library.markMissing] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}/mark-missing`, {
        method: 'POST',
      });
    },

    /**
     * Mark a track as present (not missing) (uses Tauri command)
     * @param {number} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async markPresent(id) {
      if (invoke) {
        try {
          return await invoke('library_mark_present', { trackId: id });
        } catch (error) {
          console.error('[api.library.markPresent] Tauri error:', error);
          throw new ApiError(500, error.toString());
        }
      }
      return request(`/library/${encodeURIComponent(id)}/mark-present`, {
        method: 'POST',
      });
    },
  },

  // ============================================
  // Queue endpoints
  // ============================================

  queue: {
    /**
     * Get current queue
     * @returns {Promise<Array>} Array of queued track objects
     */
    async get() {
      return request('/queue');
    },

    /**
     * Add track(s) to queue by track IDs
     * @param {number|number[]} trackIds - Track ID(s) to add
     * @param {number} [position] - Position to insert at (end if omitted)
     * @returns {Promise<{added: number, queue_length: number}>}
     */
    async add(trackIds, position) {
      const ids = Array.isArray(trackIds) ? trackIds : [trackIds];
      return request('/queue/add', {
        method: 'POST',
        body: JSON.stringify({ track_ids: ids, position }),
      });
    },

    /**
     * Remove track from queue
     * @param {number} position - Position in queue to remove
     * @returns {Promise<{queue: Array}>}
     */
    async remove(position) {
      return request(`/queue/${position}`, {
        method: 'DELETE',
      });
    },

    /**
     * Clear the entire queue
     * @returns {Promise<void>}
     */
    async clear() {
      return request('/queue/clear', {
        method: 'POST',
      });
    },

    /**
     * Move track within queue (reorder)
     * @param {number} from - Current position
     * @param {number} to - New position
     * @returns {Promise<{success: boolean, queue_length: number}>}
     */
    async move(from, to) {
      return request('/queue/reorder', {
        method: 'POST',
        body: JSON.stringify({ from_position: from, to_position: to }),
      });
    },

    async shuffle(keepCurrent = true) {
      return request('/queue/shuffle', {
        method: 'POST',
        body: JSON.stringify({ keep_current: keepCurrent }),
      });
    },

    async save(state) {
      console.debug('Queue save (local only):', state);
    },
  },

  // ============================================
  // Favorites endpoints
  // ============================================

  favorites: {
    async get(params = {}) {
      const query = new URLSearchParams();
      if (params.limit) query.set('limit', params.limit.toString());
      if (params.offset) query.set('offset', params.offset.toString());
      const queryString = query.toString();
      return request(`/favorites${queryString ? `?${queryString}` : ''}`);
    },

    async check(trackId) {
      return request(`/favorites/${encodeURIComponent(trackId)}`);
    },

    async add(trackId) {
      return request(`/favorites/${encodeURIComponent(trackId)}`, {
        method: 'POST',
      });
    },

    async remove(trackId) {
      return request(`/favorites/${encodeURIComponent(trackId)}`, {
        method: 'DELETE',
      });
    },

    async getTop25() {
      return request('/favorites/top25');
    },

    async getRecentlyPlayed(params = {}) {
      const query = new URLSearchParams();
      if (params.days) query.set('days', params.days.toString());
      if (params.limit) query.set('limit', params.limit.toString());
      const queryString = query.toString();
      return request(`/favorites/recently-played${queryString ? `?${queryString}` : ''}`);
    },

    async getRecentlyAdded(params = {}) {
      const query = new URLSearchParams();
      if (params.days) query.set('days', params.days.toString());
      if (params.limit) query.set('limit', params.limit.toString());
      const queryString = query.toString();
      return request(`/favorites/recently-added${queryString ? `?${queryString}` : ''}`);
    },
  },

  // ============================================
  // Playback endpoints (if sidecar handles playback state)
  // ============================================

  playback: {
    /**
     * Get current playback state
     * @returns {Promise<{playing: boolean, position: number, track: object|null}>}
     */
    async getState() {
      return request('/playback/state');
    },

    /**
     * Update playback position (for sync)
     * @param {number} position - Position in seconds
     * @returns {Promise<void>}
     */
    async updatePosition(position) {
      return request('/playback/position', {
        method: 'POST',
        body: JSON.stringify({ position }),
      });
    },
  },

  // ============================================
  // Preferences endpoints
  // ============================================

  preferences: {
    /**
     * Get all preferences
     * @returns {Promise<object>}
     */
    async get() {
      return request('/preferences');
    },

    /**
     * Update preferences
     * @param {object} prefs - Preferences to update
     * @returns {Promise<object>}
     */
    async update(prefs) {
      return request('/preferences', {
        method: 'PATCH',
        body: JSON.stringify(prefs),
      });
    },

    /**
     * Get a specific preference
     * @param {string} key - Preference key
     * @returns {Promise<any>}
     */
    async getValue(key) {
      return request(`/preferences/${encodeURIComponent(key)}`);
    },

    /**
     * Set a specific preference
     * @param {string} key - Preference key
     * @param {any} value - Preference value
     * @returns {Promise<void>}
     */
    async setValue(key, value) {
      return request(`/preferences/${encodeURIComponent(key)}`, {
        method: 'PUT',
        body: JSON.stringify({ value }),
      });
    },
  },

  playlists: {
    async getAll() {
      const response = await request('/playlists');
      return Array.isArray(response) ? response : (response.playlists || []);
    },

    async generateName(base = 'New playlist') {
      const query = new URLSearchParams({ base });
      return request(`/playlists/generate-name?${query}`);
    },

    async create(name) {
      return request('/playlists', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
    },

    async get(playlistId) {
      return request(`/playlists/${playlistId}`);
    },

    async rename(playlistId, name) {
      return request(`/playlists/${playlistId}`, {
        method: 'PUT',
        body: JSON.stringify({ name }),
      });
    },

    async delete(playlistId) {
      return request(`/playlists/${playlistId}`, {
        method: 'DELETE',
      });
    },

    async addTracks(playlistId, trackIds) {
      return request(`/playlists/${playlistId}/tracks`, {
        method: 'POST',
        body: JSON.stringify({ track_ids: trackIds }),
      });
    },

    async removeTrack(playlistId, position) {
      return request(`/playlists/${playlistId}/tracks/${position}`, {
        method: 'DELETE',
      });
    },

    async reorder(playlistId, fromPosition, toPosition) {
      return request(`/playlists/${playlistId}/tracks/reorder`, {
        method: 'POST',
        body: JSON.stringify({ from_position: fromPosition, to_position: toPosition }),
      });
    },

    async reorderPlaylists(fromPosition, toPosition) {
      return request('/playlists/reorder', {
        method: 'POST',
        body: JSON.stringify({ from_position: fromPosition, to_position: toPosition }),
      });
    },
  },

  // ============================================
  // Last.fm endpoints
  // ============================================

  lastfm: {
    /**
     * Get Last.fm settings
     * @returns {Promise<{enabled: boolean, username: string|null, authenticated: boolean, scrobble_threshold: number}>}
     */
    async getSettings() {
      return request('/lastfm/settings');
    },

    /**
     * Update Last.fm settings
     * @param {object} settings - Settings to update
     * @param {boolean} [settings.enabled] - Enable/disable scrobbling
     * @param {number} [settings.scrobble_threshold] - Scrobble threshold percentage (25-100)
     * @returns {Promise<{updated: string[]}>}
     */
    async updateSettings(settings) {
      return request('/lastfm/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      });
    },

    /**
     * Get Last.fm authentication URL
     * @returns {Promise<{auth_url: string}>}
     */
    async getAuthUrl() {
      return request('/lastfm/auth-url');
    },

    /**
     * Complete Last.fm authentication
     * @param {string} token - Authentication token from callback
     * @returns {Promise<{status: string, username: string, message: string}>}
     */
    async completeAuth(token) {
      const query = new URLSearchParams({ token });
      return request(`/lastfm/auth-callback?${query}`);
    },

    /**
     * Scrobble a track
     * @param {object} scrobbleData - Track scrobble data
     * @param {string} scrobbleData.artist - Artist name
     * @param {string} scrobbleData.track - Track title
     * @param {string} [scrobbleData.album] - Album name
     * @param {number} scrobbleData.timestamp - Unix timestamp when track finished
     * @param {number} scrobbleData.duration - Track duration in seconds
     * @param {number} scrobbleData.played_time - Time played in seconds
     * @returns {Promise<object>}
     */
    async scrobble(scrobbleData) {
      return request('/lastfm/scrobble', {
        method: 'POST',
        body: JSON.stringify(scrobbleData),
      });
    },

    /**
     * Update 'Now Playing' status on Last.fm
     * @param {object} nowPlayingData - Now playing track data
     * @param {string} nowPlayingData.artist - Artist name
     * @param {string} nowPlayingData.track - Track title
     * @param {string} [nowPlayingData.album] - Album name
     * @param {number} [nowPlayingData.duration] - Track duration in seconds
     * @returns {Promise<object>}
     */
    async updateNowPlaying(nowPlayingData) {
      return request('/lastfm/now-playing', {
        method: 'POST',
        body: JSON.stringify(nowPlayingData),
      });
    },

    /**
     * Import user's loved tracks from Last.fm
     * @returns {Promise<{status: string, total_loved_tracks: number, imported_count: number, message: string}>}
     */
    async importLovedTracks() {
      return request('/lastfm/import-loved-tracks', {
        method: 'POST',
      });
    },

    /**
     * Disconnect from Last.fm
     * @returns {Promise<{status: string, message: string}>}
     */
    async disconnect() {
      return request('/lastfm/disconnect', {
        method: 'DELETE',
      });
    },

    /**
     * Get scrobble queue status
     * @returns {Promise<{queued_scrobbles: number}>}
     */
    async getQueueStatus() {
      return request('/lastfm/queue/status');
    },

    /**
     * Manually retry queued scrobbles
     * @returns {Promise<{status: string, remaining_queued: number}>}
     */
    async retryQueuedScrobbles() {
      return request('/lastfm/queue/retry', {
        method: 'POST',
      });
    },
  },

  watchedFolders: {
    async list() {
      return request('/watched-folders');
    },

    async get(id) {
      return request(`/watched-folders/${id}`);
    },

    async add(path, mode = 'continuous', cadenceMinutes = 10, enabled = true) {
      return request('/watched-folders', {
        method: 'POST',
        body: JSON.stringify({
          path,
          mode,
          cadence_minutes: cadenceMinutes,
          enabled,
        }),
      });
    },

    async update(id, updates) {
      return request(`/watched-folders/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
    },

    async remove(id) {
      return request(`/watched-folders/${id}`, {
        method: 'DELETE',
      });
    },

    async rescan(id) {
      return request(`/watched-folders/${id}/rescan`, {
        method: 'POST',
      });
    },
  },
};

export default api;
