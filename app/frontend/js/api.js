/**
 * Backend API Client
 *
 * HTTP client for communicating with the Python FastAPI sidecar.
 * The sidecar runs on localhost:5556 and provides REST endpoints
 * for library, queue, and playback operations.
 */

let API_BASE = 'http://127.0.0.1:8765/api';

export function setApiBase(url) {
  API_BASE = url;
}

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
     * Get all tracks in library
     * @param {object} params - Query parameters
     * @param {string} [params.search] - Search query
     * @param {string} [params.sort] - Sort field
     * @param {string} [params.order] - Sort order ('asc' or 'desc')
     * @param {number} [params.limit] - Max results
     * @param {number} [params.offset] - Offset for pagination
     * @returns {Promise<Array>} Array of track objects
     */
    async getTracks(params = {}) {
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
     * Get a single track by ID
     * @param {string} id - Track ID
     * @returns {Promise<object>} Track object
     */
    async getTrack(id) {
      return request(`/library/${encodeURIComponent(id)}`);
    },

    /**
     * Scan paths for music files and add to library
     * @param {string[]} paths - File or directory paths to scan
     * @param {boolean} [recursive=true] - Scan subdirectories
     * @returns {Promise<{added: number, skipped: number, errors: number, tracks: Array}>}
     */
    async scan(paths, recursive = true) {
      return request('/library/scan', {
        method: 'POST',
        body: JSON.stringify({ paths, recursive }),
      });
    },

    /**
     * Get library statistics
     * @returns {Promise<{total_tracks: number, total_duration: number, ...}>}
     */
    async getStats() {
      return request('/library/stats');
    },

    /**
     * Delete a track from library
     * @param {string} id - Track ID
     * @returns {Promise<void>}
     */
    async deleteTrack(id) {
      return request(`/library/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
    },

    /**
     * Update play count for a track (increment by 1)
     * @param {string} id - Track ID
     * @returns {Promise<{id: number, play_count: number, last_played: string}>}
     */
    async updatePlayCount(id) {
      return request(`/library/${encodeURIComponent(id)}/play-count`, {
        method: 'PUT',
      });
    },

    /**
     * Rescan a track's metadata from its file
     * @param {string} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async rescanTrack(id) {
      return request(`/library/${encodeURIComponent(id)}/rescan`, {
        method: 'PUT',
      });
    },

    /**
     * Get album artwork for a track
     * @param {string} id - Track ID
     * @returns {Promise<{data: string, mime_type: string, source: string}|null>}
     */
    async getArtwork(id) {
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
     * Get all tracks marked as missing
     * @returns {Promise<{tracks: Array, total: number}>}
     */
    async getMissing() {
      return request('/library/missing');
    },

    /**
     * Locate a missing track by providing a new file path
     * @param {string} id - Track ID
     * @param {string} newPath - New file path
     * @returns {Promise<object>} Updated track object
     */
    async locate(id, newPath) {
      return request(`/library/${encodeURIComponent(id)}/locate`, {
        method: 'POST',
        body: JSON.stringify({ new_path: newPath }),
      });
    },

    /**
     * Check if a track's file exists and update its missing status
     * @param {string} id - Track ID
     * @returns {Promise<object>} Updated track object with current missing status
     */
    async checkStatus(id) {
      return request(`/library/${encodeURIComponent(id)}/check-status`, {
        method: 'POST',
      });
    },

    /**
     * Mark a track as missing
     * @param {string} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async markMissing(id) {
      return request(`/library/${encodeURIComponent(id)}/mark-missing`, {
        method: 'POST',
      });
    },

    /**
     * Mark a track as present (not missing)
     * @param {string} id - Track ID
     * @returns {Promise<object>} Updated track object
     */
    async markPresent(id) {
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
