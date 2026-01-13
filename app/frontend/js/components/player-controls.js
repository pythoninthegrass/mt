/**
 * Player Controls Component
 * 
 * Bottom player controls bar with transport controls, progress bar,
 * volume control, and now playing info.
 */

/**
 * Create the player controls Alpine component
 * @param {object} Alpine - Alpine.js instance
 */
export function createPlayerControls(Alpine) {
  Alpine.data('playerControls', () => ({
    // Local state for drag operations
    isDraggingProgress: false,
    isDraggingVolume: false,
    dragPosition: 0,
    
    /**
     * Initialize component
     */
    init() {
      // Handle mouse up anywhere to stop dragging
      document.addEventListener('mouseup', () => {
        if (this.isDraggingProgress) {
          this.isDraggingProgress = false;
          this.player.seek(this.dragPosition);
        }
        this.isDraggingVolume = false;
      });
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
     * Get the UI store
     */
    get ui() {
      return this.$store.ui;
    },
    
    /**
     * Get current track
     */
    get currentTrack() {
      return this.player.currentTrack;
    },
    
    /**
     * Check if there's a track loaded
     */
    get hasTrack() {
      return !!this.currentTrack;
    },
    
    /**
     * Get play/pause icon
     */
    get playIcon() {
      return this.player.isPlaying ? 'pause' : 'play';
    },
    
    /**
     * Get volume icon based on level
     */
    get volumeIcon() {
      if (this.player.muted || this.player.volume === 0) {
        return 'muted';
      } else if (this.player.volume < 33) {
        return 'low';
      } else if (this.player.volume < 66) {
        return 'medium';
      }
      return 'high';
    },
    
    /**
     * Get loop icon based on mode
     */
    get loopIcon() {
      return this.queue.loopMode === 'one' ? 'repeat-one' : 'repeat';
    },
    
    /**
     * Check if loop is active
     */
    get isLoopActive() {
      return this.queue.loopMode !== 'none';
    },
    
    /**
     * Get progress percentage for display during drag
     */
    get displayPosition() {
      if (this.isDraggingProgress) {
        return this.dragPosition;
      }
      return this.player.position;
    },
    
    /**
     * Get progress percentage (0-100)
     */
    get progressPercent() {
      if (!this.player.duration) return 0;
      return (this.displayPosition / this.player.duration) * 100;
    },
    
    /**
     * Format time for display
     * @param {number} seconds - Time in seconds
     */
    formatTime(seconds) {
      if (!seconds || isNaN(seconds)) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    /**
     * Handle play/pause toggle
     */
    togglePlay() {
      this.player.togglePlay();
    },
    
    /**
     * Handle previous track
     */
    previous() {
      this.player.previous();
    },
    
    /**
     * Handle next track
     */
    next() {
      this.player.next();
    },
    
    /**
     * Handle progress bar click
     * @param {MouseEvent} event
     */
    handleProgressClick(event) {
      if (!this.hasTrack) return;
      
      const rect = event.currentTarget.getBoundingClientRect();
      const percent = (event.clientX - rect.left) / rect.width;
      const position = percent * this.player.duration;
      this.player.seek(position);
    },
    
    /**
     * Handle progress bar drag start
     * @param {MouseEvent} event
     */
    handleProgressDragStart(event) {
      if (!this.hasTrack) return;
      
      this.isDraggingProgress = true;
      this.updateDragPosition(event);
    },
    
    /**
     * Handle progress bar drag
     * @param {MouseEvent} event
     */
    handleProgressDrag(event) {
      if (!this.isDraggingProgress) return;
      this.updateDragPosition(event);
    },
    
    /**
     * Update drag position from mouse event
     * @param {MouseEvent} event
     */
    updateDragPosition(event) {
      const progressBar = this.$refs.progressBar;
      if (!progressBar) return;
      
      const rect = progressBar.getBoundingClientRect();
      const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
      this.dragPosition = percent * this.player.duration;
    },
    
    /**
     * Handle volume change
     * @param {Event} event
     */
    handleVolumeChange(event) {
      const value = parseInt(event.target.value, 10);
      this.player.setVolume(value);
    },
    
    /**
     * Handle volume slider click
     * @param {MouseEvent} event
     */
    handleVolumeClick(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      const percent = (event.clientX - rect.left) / rect.width;
      const volume = Math.round(percent * 100);
      this.player.setVolume(volume);
    },
    
    /**
     * Toggle mute
     */
    toggleMute() {
      this.player.toggleMute();
    },
    
    /**
     * Toggle shuffle
     */
    toggleShuffle() {
      this.queue.toggleShuffle();
    },
    
    /**
     * Cycle loop mode
     */
    cycleLoop() {
      this.queue.cycleLoopMode();
    },
    
    /**
     * Toggle queue view
     */
    toggleQueue() {
      if (this.ui.view === 'queue') {
        this.ui.setView('library');
      } else {
        this.ui.setView('queue');
      }
    },
    
    /**
     * Show now playing view
     */
    showNowPlaying() {
      this.ui.setView('nowPlaying');
    },
    
    get library() {
      return this.$store.library;
    },
    
    get libraryStats() {
      const tracks = this.library.tracks;
      const count = tracks.length;
      const totalBytes = tracks.reduce((sum, t) => sum + (t.file_size || 0), 0);
      const sizeStr = this.formatBytes(totalBytes);
      const totalSeconds = tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
      const durationStr = this.formatDurationLong(totalSeconds);
      return `${count} files  ${sizeStr}  ${durationStr}`;
    },
    
    formatBytes(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const units = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      const value = bytes / Math.pow(1024, i);
      return `${value.toFixed(1)} ${units[i]}`;
    },
    
    formatDurationLong(seconds) {
      if (!seconds || isNaN(seconds)) return '0m';
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      if (days > 0) return `${days}d ${hours}h ${mins}m`;
      if (hours > 0) return `${hours}h ${mins}m`;
      return `${mins}m`;
    },
  }));
}

export default createPlayerControls;
