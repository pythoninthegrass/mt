/**
 * Player Store - manages audio playback state
 * 
 * Integrates with Tauri commands for audio control (task-095)
 * and receives progress updates via Tauri events.
 */

const { invoke } = window.__TAURI__?.core ?? { invoke: async () => console.warn('Tauri not available') };
const { listen } = window.__TAURI__?.event ?? { listen: async () => () => {} };

export function createPlayerStore(Alpine) {
  Alpine.store('player', {
    // Current track metadata
    currentTrack: null, // { id, title, artist, album, duration, path, artwork }
    
    // Playback state
    isPlaying: false,
    progress: 0,        // 0-100 percentage
    currentTime: 0,     // milliseconds
    duration: 0,        // milliseconds
    volume: 100,        // 0-100
    muted: false,
    
    // Internal state
    _progressListener: null,
    _stateListener: null,
    
    /**
     * Initialize event listeners for Tauri audio events
     */
    async init() {
      // Listen for progress updates from Rust audio engine
      this._progressListener = await listen('audio:progress', (event) => {
        const { current_time, duration, progress } = event.payload;
        this.currentTime = current_time;
        this.duration = duration;
        this.progress = progress;
      });
      
      // Listen for playback state changes
      this._stateListener = await listen('audio:state', (event) => {
        const { is_playing, track } = event.payload;
        this.isPlaying = is_playing;
        if (track) {
          this.currentTrack = track;
        }
      });
      
      // Listen for track end
      await listen('audio:ended', () => {
        this.isPlaying = false;
        // Queue store will handle advancing to next track
        Alpine.store('queue').playNext();
      });
    },
    
    /**
     * Clean up event listeners
     */
    destroy() {
      if (this._progressListener) this._progressListener();
      if (this._stateListener) this._stateListener();
    },
    
    /**
     * Play a specific track
     * @param {Object} track - Track object with path and metadata
     */
    async play(track) {
      if (!track?.path) {
        console.error('Cannot play track without path');
        return;
      }
      
      try {
        await invoke('audio_play', { path: track.path });
        this.currentTrack = track;
        this.isPlaying = true;
        this.progress = 0;
        this.currentTime = 0;
        this.duration = track.duration || 0;
      } catch (error) {
        console.error('Failed to play track:', error);
        this.isPlaying = false;
      }
    },
    
    /**
     * Pause playback
     */
    async pause() {
      try {
        await invoke('audio_pause');
        this.isPlaying = false;
      } catch (error) {
        console.error('Failed to pause:', error);
      }
    },
    
    /**
     * Resume playback
     */
    async resume() {
      try {
        await invoke('audio_resume');
        this.isPlaying = true;
      } catch (error) {
        console.error('Failed to resume:', error);
      }
    },
    
    /**
     * Toggle play/pause
     */
    async toggle() {
      if (this.isPlaying) {
        await this.pause();
      } else if (this.currentTrack) {
        await this.resume();
      } else {
        // No track loaded, try to play from queue
        const queue = Alpine.store('queue');
        if (queue.items.length > 0) {
          await queue.playIndex(queue.currentIndex >= 0 ? queue.currentIndex : 0);
        }
      }
    },
    
    /**
     * Stop playback and reset state
     */
    async stop() {
      try {
        await invoke('audio_stop');
        this.isPlaying = false;
        this.progress = 0;
        this.currentTime = 0;
      } catch (error) {
        console.error('Failed to stop:', error);
      }
    },
    
    /**
     * Seek to position
     * @param {number} position - Position in milliseconds
     */
    async seek(position) {
      try {
        await invoke('audio_seek', { position });
        this.currentTime = position;
        this.progress = this.duration > 0 ? (position / this.duration) * 100 : 0;
      } catch (error) {
        console.error('Failed to seek:', error);
      }
    },
    
    /**
     * Seek to percentage
     * @param {number} percent - Position as percentage (0-100)
     */
    async seekPercent(percent) {
      const position = (percent / 100) * this.duration;
      await this.seek(position);
    },
    
    /**
     * Set volume
     * @param {number} vol - Volume level (0-100)
     */
    async setVolume(vol) {
      const clampedVol = Math.max(0, Math.min(100, vol));
      try {
        await invoke('audio_set_volume', { volume: clampedVol / 100 });
        this.volume = clampedVol;
        if (clampedVol > 0) {
          this.muted = false;
        }
      } catch (error) {
        console.error('Failed to set volume:', error);
      }
    },
    
    /**
     * Toggle mute
     */
    async toggleMute() {
      if (this.muted) {
        await this.setVolume(this._previousVolume || 100);
        this.muted = false;
      } else {
        this._previousVolume = this.volume;
        await this.setVolume(0);
        this.muted = true;
      }
    },
    
    /**
     * Format time in mm:ss
     * @param {number} ms - Time in milliseconds
     * @returns {string} Formatted time string
     */
    formatTime(ms) {
      if (!ms || ms < 0) return '0:00';
      const totalSeconds = Math.floor(ms / 1000);
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },
    
    /**
     * Get formatted current time
     */
    get formattedCurrentTime() {
      return this.formatTime(this.currentTime);
    },
    
    /**
     * Get formatted duration
     */
    get formattedDuration() {
      return this.formatTime(this.duration);
    },
  });
}
