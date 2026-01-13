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
      if (params.sort) query.set('sort', params.sort);
      if (params.order) query.set('order', params.order);
      if (params.limit) query.set('limit', params.limit.toString());
      if (params.offset) query.set('offset', params.offset.toString());
      
      const queryString = query.toString();
      return request(`/library/tracks${queryString ? `?${queryString}` : ''}`);
    },
    
    /**
     * Get a single track by ID
     * @param {string} id - Track ID
     * @returns {Promise<object>} Track object
     */
    async getTrack(id) {
      return request(`/library/tracks/${encodeURIComponent(id)}`);
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
      return request(`/library/tracks/${encodeURIComponent(id)}`, {
        method: 'DELETE',
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
     * Add track(s) to queue
     * @param {string|string[]} trackIds - Track ID(s) to add
     * @param {number} [position] - Position to insert at (end if omitted)
     * @returns {Promise<{queue: Array}>}
     */
    async add(trackIds, position) {
      const ids = Array.isArray(trackIds) ? trackIds : [trackIds];
      return request('/queue', {
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
     * Move track within queue
     * @param {number} from - Current position
     * @param {number} to - New position
     * @returns {Promise<{queue: Array}>}
     */
    async move(from, to) {
      return request('/queue/move', {
        method: 'POST',
        body: JSON.stringify({ from, to }),
      });
    },
    
    /**
     * Shuffle the queue
     * @param {boolean} [keepCurrent=true] - Keep current track at position 0
     * @returns {Promise<{queue: Array}>}
     */
    async shuffle(keepCurrent = true) {
      return request('/queue/shuffle', {
        method: 'POST',
        body: JSON.stringify({ keep_current: keepCurrent }),
      });
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
};

export default api;
