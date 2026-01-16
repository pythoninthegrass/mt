/**
 * Library Store - manages music library state
 * 
 * Handles track loading, searching, sorting, and
 * library scanning via Python backend.
 */

import { api } from '../api.js';

export function createLibraryStore(Alpine) {
  Alpine.store('library', {
    // Track data
    tracks: [],          // All tracks in library
    filteredTracks: [],  // Tracks after search/filter
    
    // Search and filter state
    searchQuery: '',
    sortBy: 'default',   // 'default', 'artist', 'album', 'title', 'index', 'dateAdded', 'duration'
    sortOrder: 'asc',    // 'asc', 'desc'
    currentSection: 'all',
    
    // Loading state
    loading: false,
    scanning: false,
    scanProgress: 0,     // 0-100
    
    // Statistics
    totalTracks: 0,
    totalDuration: 0,    // milliseconds
    
    // Internal
    _searchDebounce: null,
    
    /**
     * Initialize library from backend
     */
    async init() {
      await this.load();
    },
    
    async load() {
      this.loading = true;
      try {
        const data = await api.library.getTracks({ limit: 10000 });
        this.tracks = data.tracks || [];
        this.totalTracks = data.total || this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
      } catch (error) {
        console.error('Failed to load library:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadFavorites() {
      this.loading = true;
      try {
        const data = await api.favorites.get({ limit: 1000 });
        this.tracks = data.tracks || [];
        this.totalTracks = this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
      } catch (error) {
        console.error('Failed to load favorites:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadRecentlyPlayed(days = 14) {
      this.loading = true;
      try {
        const data = await api.favorites.getRecentlyPlayed({ days, limit: 100 });
        this.tracks = data.tracks || [];
        this.totalTracks = this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
      } catch (error) {
        console.error('Failed to load recently played:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadRecentlyAdded(days = 14) {
      this.loading = true;
      try {
        const data = await api.favorites.getRecentlyAdded({ days, limit: 100 });
        this.tracks = data.tracks || [];
        this.totalTracks = this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
      } catch (error) {
        console.error('Failed to load recently added:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadTop25() {
      this.loading = true;
      try {
        const data = await api.favorites.getTop25();
        this.tracks = data.tracks || [];
        this.totalTracks = this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
      } catch (error) {
        console.error('Failed to load top 25:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async loadPlaylist(playlistId) {
      this.loading = true;
      try {
        const data = await api.playlists.get(playlistId);
        this.tracks = data.tracks || [];
        this.totalTracks = this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
        return data;
      } catch (error) {
        console.error('Failed to load playlist:', error);
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    setSection(section) {
      this.currentSection = section;
    },
    
    refreshIfLikedSongs() {
      if (this.currentSection === 'liked') {
        this.loadFavorites();
      }
    },
    
    /**
     * Search tracks with debounce
     * @param {string} query - Search query
     */
    search(query) {
      this.searchQuery = query;
      
      // Debounce search
      if (this._searchDebounce) {
        clearTimeout(this._searchDebounce);
      }
      
      this._searchDebounce = setTimeout(() => {
        this.applyFilters();
      }, 150);
    },
    
    /**
     * Apply search and sort filters
     */
    applyFilters() {
      let result = [...this.tracks];
      
      // Apply search filter
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(track => 
          track.title?.toLowerCase().includes(query) ||
          track.artist?.toLowerCase().includes(query) ||
          track.album?.toLowerCase().includes(query)
        );
      }
      
      // Apply sorting
      const sortKeyMap = {
        index: 'track_number',
        dateAdded: 'added_date',
        lastPlayed: 'last_played',
        playCount: 'play_count',
      };
      
      const parseTrackNumber = (val) => parseInt(String(val || '').split('/')[0], 10) || 999999;
      
      const compareValues = (aVal, bVal, key) => {
        if (key === 'track_number') {
          aVal = parseTrackNumber(aVal);
          bVal = parseTrackNumber(bVal);
        } else if (['duration', 'play_count'].includes(key)) {
          aVal = Number(aVal) || 0;
          bVal = Number(bVal) || 0;
        } else if (['added_date', 'last_played'].includes(key)) {
          aVal = aVal ? new Date(aVal).getTime() : 0;
          bVal = bVal ? new Date(bVal).getTime() : 0;
        } else {
          aVal = String(aVal || '').toLowerCase();
          bVal = String(bVal || '').toLowerCase();
        }
        if (aVal < bVal) return -1;
        if (aVal > bVal) return 1;
        return 0;
      };
      
      if (this.sortBy === 'default') {
        result.sort((a, b) => {
          let cmp = compareValues(a.album, b.album, 'album');
          if (cmp !== 0) return cmp;
          cmp = compareValues(a.artist, b.artist, 'artist');
          if (cmp !== 0) return cmp;
          return compareValues(a.track_number, b.track_number, 'track_number');
        });
      } else {
        const sortKey = sortKeyMap[this.sortBy] || this.sortBy;
        result.sort((a, b) => {
          const cmp = compareValues(a[sortKey], b[sortKey], sortKey);
          return this.sortOrder === 'desc' ? -cmp : cmp;
        });
      }
      
      this.filteredTracks = result;
    },
    
    /**
     * Set sort field
     * @param {string} field - Field to sort by
     */
    setSortBy(field) {
      if (this.sortBy === field) {
        // Toggle order if same field
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortBy = field;
        this.sortOrder = 'asc';
      }
      this.applyFilters();
    },
    
    /**
     * Scan paths for music files
     * @param {string[]} paths - File or directory paths to scan
     * @param {boolean} [recursive=true] - Scan subdirectories
     */
    async scan(paths, recursive = true) {
      if (!paths || paths.length === 0) {
        console.log('[library] scan: no paths provided');
        return { added: 0, skipped: 0, errors: 0 };
      }
      
      console.log('[library] scan: scanning', paths.length, 'paths:', paths);
      this.scanning = true;
      this.scanProgress = 0;
      
      try {
        const result = await api.library.scan(paths, recursive);
        console.log('[library] scan result:', result);
        
        await this.load();
        
        return result;
      } catch (error) {
        console.error('[library] scan failed:', error);
        throw error;
      } finally {
        this.scanning = false;
        this.scanProgress = 0;
      }
    },
    
    async openAddMusicDialog() {
      try {
        console.log('[library] opening add music dialog...');
        
        if (!window.__TAURI__) {
          throw new Error('Tauri not available');
        }
        
        // Use Rust command instead of JS plugin API for better reliability
        const { invoke } = window.__TAURI__.core;
        const paths = await invoke('open_add_music_dialog');
        
        console.log('[library] dialog returned paths:', paths);
        
        if (paths && (Array.isArray(paths) ? paths.length > 0 : paths)) {
          const pathArray = Array.isArray(paths) ? paths : [paths];
          const result = await this.scan(pathArray);
          const ui = Alpine.store('ui');
          if (result.added > 0) {
            ui.toast(`Added ${result.added} track${result.added === 1 ? '' : 's'} to library`, 'success');
          } else if (result.skipped > 0) {
            ui.toast(`All ${result.skipped} track${result.skipped === 1 ? '' : 's'} already in library`, 'info');
          } else {
            ui.toast('No audio files found', 'info');
          }
          return result;
        } else {
          console.log('[library] dialog cancelled or no paths selected');
        }
        return null;
      } catch (error) {
        console.error('[library] openAddMusicDialog failed:', error);
        Alpine.store('ui').toast('Failed to add music', 'error');
        throw error;
      }
    },
    
    /**
     * Remove track from library
     * @param {string} trackId - Track ID to remove
     */
    async remove(trackId) {
      try {
        await api.library.deleteTrack(trackId);
        
        // Update local state
        this.tracks = this.tracks.filter(t => t.id !== trackId);
        this.totalTracks = this.tracks.length;
        this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.applyFilters();
        
        // Also remove from queue if present
        const queue = Alpine.store('queue');
        const queueIndex = queue.items.findIndex(t => t.id === trackId);
        if (queueIndex >= 0) {
          await queue.remove(queueIndex);
        }
      } catch (error) {
        console.error('Failed to remove track:', error);
        throw error;
      }
    },
    
    /**
     * Get track by ID
     * @param {string} trackId - Track ID
     * @returns {Object|null} Track object or null
     */
    getTrack(trackId) {
      return this.tracks.find(t => t.id === trackId) || null;
    },
    
    /**
     * Add track to queue
     * @param {Object} track - Track to add
     * @param {boolean} playNow - Start playing immediately
     */
    async addToQueue(track, playNow = false) {
      await Alpine.store('queue').add(track, playNow);
    },
    
    /**
     * Add all filtered tracks to queue
     * @param {boolean} playNow - Start playing immediately
     */
    async addAllToQueue(playNow = false) {
      await Alpine.store('queue').add(this.filteredTracks, playNow);
    },
    
    /**
     * Play track immediately (clears queue and plays)
     * @param {Object} track - Track to play
     */
    async playNow(track) {
      const queue = Alpine.store('queue');
      await queue.clear();
      await queue.add(track, true);
    },
    
    /**
     * Format total duration for display
     */
    get formattedTotalDuration() {
      const hours = Math.floor(this.totalDuration / 3600000);
      const minutes = Math.floor((this.totalDuration % 3600000) / 60000);
      
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes} min`;
    },
    
    /**
     * Get unique artists
     */
    get artists() {
      const artistSet = new Set(this.tracks.map(t => t.artist).filter(Boolean));
      return Array.from(artistSet).sort();
    },
    
    /**
     * Get unique albums
     */
    get albums() {
      const albumSet = new Set(this.tracks.map(t => t.album).filter(Boolean));
      return Array.from(albumSet).sort();
    },
    
    /**
     * Get tracks grouped by artist
     */
    get tracksByArtist() {
      const grouped = {};
      for (const track of this.filteredTracks) {
        const artist = track.artist || 'Unknown Artist';
        if (!grouped[artist]) {
          grouped[artist] = [];
        }
        grouped[artist].push(track);
      }
      return grouped;
    },
    
    /**
     * Get tracks grouped by album
     */
    get tracksByAlbum() {
      const grouped = {};
      for (const track of this.filteredTracks) {
        const album = track.album || 'Unknown Album';
        if (!grouped[album]) {
          grouped[album] = [];
        }
        grouped[album].push(track);
      }
      return grouped;
    },
  });
}
