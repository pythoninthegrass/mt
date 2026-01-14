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
    dragVolume: 0,
    showVolumeTooltip: false,
    _volumeDebounce: null,
    
    init() {
      document.addEventListener('mouseup', () => {
        if (this.isDraggingProgress) {
          this.isDraggingProgress = false;
          this.player.seek(this.dragPosition);
        }
        if (this.isDraggingVolume) {
          this.isDraggingVolume = false;
          this.commitVolume(this.dragVolume);
        }
      });
      
      document.addEventListener('mousemove', (event) => {
        if (this.isDraggingVolume) {
          this.updateDragVolume(event);
        }
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
    
    get hasTrack() {
      return !!this.currentTrack;
    },
    
    get isFavorite() {
      return this.player.isFavorite;
    },
    
    toggleFavorite() {
      if (!this.hasTrack) return;
      this.player.toggleFavorite();
    },
    
    get trackDisplayName() {
      if (!this.currentTrack) return '';
      const artist = this.currentTrack.artist || 'Unknown Artist';
      const title = this.currentTrack.title || this.currentTrack.filename || 'Unknown Track';
      return `${artist} - ${title}`;
    },
    
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
    
    get displayPosition() {
      if (this.isDraggingProgress) {
        return this.dragPosition;
      }
      return this.player.currentTime;
    },
    
    get progressPercent() {
      if (!this.player.duration) return 0;
      return (this.displayPosition / this.player.duration) * 100;
    },
    
    formatTime(ms) {
      if (!ms || isNaN(ms)) return '0:00';
      const totalSeconds = Math.floor(ms / 1000);
      const mins = Math.floor(totalSeconds / 60);
      const secs = totalSeconds % 60;
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
    
    handleVolumeChange(event) {
      const value = parseInt(event.target.value, 10);
      this.commitVolume(value);
    },
    
    handleVolumeClick(event) {
      const rect = event.currentTarget.getBoundingClientRect();
      const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
      const volume = Math.round(percent * 100);
      this.commitVolume(volume);
    },
    
    handleVolumeDragStart(event) {
      this.isDraggingVolume = true;
      this.updateDragVolume(event);
    },
    
    updateDragVolume(event) {
      const volumeBar = this.$refs.volumeBar;
      if (!volumeBar) return;
      
      const rect = volumeBar.getBoundingClientRect();
      const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
      this.dragVolume = Math.round(percent * 100);
    },
    
    commitVolume(volume) {
      if (this._volumeDebounce) {
        clearTimeout(this._volumeDebounce);
      }
      
      this._volumeDebounce = setTimeout(() => {
        this.player.setVolume(volume);
        this._volumeDebounce = null;
      }, 30);
    },
    
    get displayVolume() {
      return this.isDraggingVolume ? this.dragVolume : this.player.volume;
    },
    
    get volumeTooltipText() {
      return `${this.displayVolume}%`;
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
