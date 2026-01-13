/**
 * Library Browser Component
 * 
 * Displays the music library with search, sort, and track actions.
 * Uses Alpine.js stores for state management.
 */

/**
 * Create the library browser Alpine component
 * @param {object} Alpine - Alpine.js instance
 */
export function createLibraryBrowser(Alpine) {
  Alpine.data('libraryBrowser', () => ({
    // Local component state
    selectedTracks: new Set(),
    lastSelectedIndex: -1,
    contextMenu: null,
    
    // Column definitions
    columns: [
      { key: 'title', label: 'Title', sortable: true, width: 'flex-1 min-w-[200px]' },
      { key: 'artist', label: 'Artist', sortable: true, width: 'w-48' },
      { key: 'album', label: 'Album', sortable: true, width: 'w-48' },
      { key: 'duration', label: 'Duration', sortable: true, width: 'w-20 text-right' },
    ],
    
    /**
     * Initialize component
     */
    init() {
      // Load library on init if not already loaded
      if (this.$store.library.tracks.length === 0) {
        this.$store.library.load();
      }
      
      // Close context menu on click outside
      document.addEventListener('click', (e) => {
        if (this.contextMenu && !e.target.closest('.context-menu')) {
          this.contextMenu = null;
        }
      });
      
      // Close context menu on escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.contextMenu) {
          this.contextMenu = null;
        }
      });
    },
    
    /**
     * Get the library store
     */
    get library() {
      return this.$store.library;
    },
    
    /**
     * Get the player store
     */
    get player() {
      return this.$store.player;
    },
    
    /**
     * Get the queue store
     */
    get queue() {
      return this.$store.queue;
    },
    
    /**
     * Get sort indicator for column
     * @param {string} key - Column key
     */
    getSortIndicator(key) {
      if (this.library.sortBy !== key) return '';
      return this.library.sortOrder === 'asc' ? '▲' : '▼';
    },
    
    /**
     * Handle column header click for sorting
     * @param {string} key - Column key
     */
    handleSort(key) {
      this.library.setSortBy(key);
    },
    
    /**
     * Handle track row click
     * @param {Event} event - Click event
     * @param {Object} track - Track object
     * @param {number} index - Track index
     */
    handleRowClick(event, track, index) {
      if (event.shiftKey && this.lastSelectedIndex >= 0) {
        // Shift+click: range selection
        const start = Math.min(this.lastSelectedIndex, index);
        const end = Math.max(this.lastSelectedIndex, index);
        
        if (!event.ctrlKey && !event.metaKey) {
          this.selectedTracks.clear();
        }
        
        for (let i = start; i <= end; i++) {
          const t = this.library.filteredTracks[i];
          if (t) this.selectedTracks.add(t.id);
        }
      } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd+click: toggle selection
        if (this.selectedTracks.has(track.id)) {
          this.selectedTracks.delete(track.id);
        } else {
          this.selectedTracks.add(track.id);
        }
        this.lastSelectedIndex = index;
      } else {
        // Regular click: single selection
        this.selectedTracks.clear();
        this.selectedTracks.add(track.id);
        this.lastSelectedIndex = index;
      }
    },
    
    /**
     * Handle track double-click to play
     * @param {Object} track - Track object
     */
    handleDoubleClick(track) {
      this.player.playTrack(track);
    },
    
    /**
     * Handle right-click context menu
     * @param {Event} event - Context menu event
     * @param {Object} track - Track object
     * @param {number} index - Track index
     */
    handleContextMenu(event, track, index) {
      event.preventDefault();
      
      // Select track if not already selected
      if (!this.selectedTracks.has(track.id)) {
        this.selectedTracks.clear();
        this.selectedTracks.add(track.id);
        this.lastSelectedIndex = index;
      }
      
      const selectedCount = this.selectedTracks.size;
      const trackLabel = selectedCount === 1 ? 'track' : `${selectedCount} tracks`;
      
      this.contextMenu = {
        x: event.clientX,
        y: event.clientY,
        track,
        items: [
          { 
            label: 'Play Now', 
            icon: '▶',
            action: () => this.playSelected() 
          },
          { 
            label: `Add ${trackLabel} to Queue`, 
            icon: '+',
            action: () => this.addSelectedToQueue() 
          },
          { type: 'separator' },
          { 
            label: 'Play Next', 
            icon: '⏭',
            action: () => this.playSelectedNext() 
          },
          { 
            label: 'Add to Playlist...', 
            icon: '📋',
            action: () => this.addToPlaylist(),
            disabled: true // TODO: implement playlists
          },
          { type: 'separator' },
          { 
            label: 'Show in Finder', 
            icon: '📁',
            action: () => this.showInFinder(track),
            disabled: selectedCount > 1
          },
          { 
            label: 'Track Info...', 
            icon: 'ℹ',
            action: () => this.showTrackInfo(track),
            disabled: selectedCount > 1
          },
          { type: 'separator' },
          { 
            label: `Remove ${trackLabel} from Library`, 
            icon: '🗑',
            action: () => this.removeSelected(),
            danger: true
          },
        ]
      };
    },
    
    /**
     * Check if track is selected
     * @param {string} trackId - Track ID
     */
    isSelected(trackId) {
      return this.selectedTracks.has(trackId);
    },
    
    /**
     * Check if track is currently playing
     * @param {string} trackId - Track ID
     */
    isPlaying(trackId) {
      return this.player.currentTrack?.id === trackId;
    },
    
    /**
     * Get selected tracks
     */
    getSelectedTracks() {
      return this.library.filteredTracks.filter(t => this.selectedTracks.has(t.id));
    },
    
    /**
     * Play selected tracks
     */
    async playSelected() {
      const tracks = this.getSelectedTracks();
      if (tracks.length > 0) {
        await this.queue.clear();
        await this.queue.addTracks(tracks);
        await this.player.playTrack(tracks[0]);
      }
      this.contextMenu = null;
    },
    
    /**
     * Add selected tracks to queue
     */
    async addSelectedToQueue() {
      const tracks = this.getSelectedTracks();
      if (tracks.length > 0) {
        await this.queue.addTracks(tracks);
        this.$store.ui.toast(`Added ${tracks.length} track${tracks.length > 1 ? 's' : ''} to queue`, 'success');
      }
      this.contextMenu = null;
    },
    
    /**
     * Play selected tracks next
     */
    async playSelectedNext() {
      const tracks = this.getSelectedTracks();
      if (tracks.length > 0) {
        // Insert after current track
        const insertIndex = this.queue.currentIndex + 1;
        for (let i = 0; i < tracks.length; i++) {
          await this.queue.add(tracks[i].id, insertIndex + i);
        }
        this.$store.ui.toast(`Playing ${tracks.length} track${tracks.length > 1 ? 's' : ''} next`, 'success');
      }
      this.contextMenu = null;
    },
    
    /**
     * Add to playlist (placeholder)
     */
    addToPlaylist() {
      this.$store.ui.toast('Playlists coming soon!', 'info');
      this.contextMenu = null;
    },
    
    /**
     * Show track in Finder/file manager
     * @param {Object} track - Track object
     */
    async showInFinder(track) {
      try {
        const { invoke } = window.__TAURI__?.core ?? {};
        if (invoke) {
          await invoke('show_in_folder', { path: track.path });
        } else {
          console.log('Show in folder:', track.path);
        }
      } catch (error) {
        console.error('Failed to show in folder:', error);
        this.$store.ui.toast('Failed to open folder', 'error');
      }
      this.contextMenu = null;
    },
    
    /**
     * Show track info modal
     * @param {Object} track - Track object
     */
    showTrackInfo(track) {
      this.$store.ui.openModal('trackInfo', track);
      this.contextMenu = null;
    },
    
    /**
     * Remove selected tracks from library
     */
    async removeSelected() {
      const tracks = this.getSelectedTracks();
      if (tracks.length === 0) return;
      
      const confirmMsg = tracks.length === 1 
        ? `Remove "${tracks[0].title}" from library?`
        : `Remove ${tracks.length} tracks from library?`;
      
      if (confirm(confirmMsg)) {
        for (const track of tracks) {
          await this.library.remove(track.id);
        }
        this.selectedTracks.clear();
        this.$store.ui.toast(`Removed ${tracks.length} track${tracks.length > 1 ? 's' : ''}`, 'success');
      }
      this.contextMenu = null;
    },
    
    /**
     * Format duration for display
     * @param {number} ms - Duration in milliseconds
     */
    formatDuration(ms) {
      if (!ms) return '--:--';
      const totalSeconds = Math.floor(ms / 1000);
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },
    
    /**
     * Clear selection
     */
    clearSelection() {
      this.selectedTracks.clear();
      this.lastSelectedIndex = -1;
    },
    
    /**
     * Select all tracks
     */
    selectAll() {
      this.library.filteredTracks.forEach(t => this.selectedTracks.add(t.id));
    },
    
    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} event
     */
    handleKeydown(event) {
      // Cmd/Ctrl+A: Select all
      if ((event.metaKey || event.ctrlKey) && event.key === 'a') {
        event.preventDefault();
        this.selectAll();
      }
      
      // Escape: Clear selection
      if (event.key === 'Escape') {
        this.clearSelection();
      }
      
      // Enter: Play selected
      if (event.key === 'Enter' && this.selectedTracks.size > 0) {
        this.playSelected();
      }
      
      // Delete/Backspace: Remove selected
      if ((event.key === 'Delete' || event.key === 'Backspace') && this.selectedTracks.size > 0) {
        event.preventDefault();
        this.removeSelected();
      }
    },
  }));
}

export default createLibraryBrowser;
