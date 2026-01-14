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
    
    // Base column definitions
    baseColumns: [
      { key: 'index', label: '#', sortable: false, width: 'w-12 text-right' },
      { key: 'title', label: 'Title', sortable: true, width: 'flex-1 min-w-[200px]' },
      { key: 'artist', label: 'Artist', sortable: true, width: 'w-40' },
      { key: 'album', label: 'Album', sortable: true, width: 'w-40' },
    ],
    
    // Extra columns for dynamic playlists
    extraColumns: {
      recent: { key: 'lastPlayed', label: 'Last Played', sortable: true, width: 'w-32' },
      added: { key: 'dateAdded', label: 'Added', sortable: true, width: 'w-32' },
      top25: { key: 'playCount', label: 'Plays', sortable: true, width: 'w-16 text-right' },
    },
    
    // Computed columns based on current section
    get columns() {
      const section = this.library.currentSection;
      const cols = [...this.baseColumns];
      
      if (this.extraColumns[section]) {
        cols.push(this.extraColumns[section]);
      }
      
      cols.push({ key: 'duration', label: 'Duration', sortable: true, width: 'w-20 text-right' });
      return cols;
    },
    
    init() {
      if (this.$store.library.tracks.length === 0 && !this.$store.library.loading) {
        this.$store.library.load();
      }
      
      document.addEventListener('click', (e) => {
        if (this.contextMenu && !e.target.closest('.context-menu')) {
          this.contextMenu = null;
        }
      });
      
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.contextMenu) {
          this.contextMenu = null;
        }
      });
      
      this.$watch('$store.player.currentTrack', (newTrack) => {
        if (newTrack?.id) {
          this.scrollToTrack(newTrack.id);
        }
      });
    },
    
    scrollToTrack(trackId) {
      this.$nextTick(() => {
        const trackRow = document.querySelector(`[data-track-id="${trackId}"]`);
        if (trackRow) {
          trackRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
    
    async handleDoubleClick(track) {
      await this.queue.clear();
      await this.queue.add(this.library.filteredTracks, false);
      const index = this.library.filteredTracks.findIndex(t => t.id === track.id);
      if (index >= 0) {
        await this.queue.playIndex(index);
      } else {
        await this.player.playTrack(track);
      }
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
    
    async removeSelected() {
      const tracks = this.getSelectedTracks();
      if (tracks.length === 0) return;
      
      const confirmMsg = tracks.length === 1 
        ? `Remove "${tracks[0].title}" from library?`
        : `Remove ${tracks.length} tracks from library?`;
      
      this.contextMenu = null;
      
      const confirmed = await window.__TAURI__?.dialog?.confirm(confirmMsg, {
        title: 'Remove from Library',
        kind: 'warning',
      }) ?? window.confirm(confirmMsg);
      
      if (confirmed) {
        for (const track of tracks) {
          await this.library.remove(track.id);
        }
        this.selectedTracks.clear();
        this.$store.ui.toast(`Removed ${tracks.length} track${tracks.length > 1 ? 's' : ''}`, 'success');
      }
    },
    
    formatDuration(seconds) {
      if (!seconds) return '--:--';
      const totalSeconds = Math.floor(seconds);
      const minutes = Math.floor(totalSeconds / 60);
      const secs = totalSeconds % 60;
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    },
    
    formatRelativeTime(timestamp) {
      if (!timestamp) return '--';
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
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
