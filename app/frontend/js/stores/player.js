const { invoke } = window.__TAURI__?.core ?? { invoke: async () => console.warn('Tauri not available') };
const { listen } = window.__TAURI__?.event ?? { listen: async () => () => {} };

export function createPlayerStore(Alpine) {
  Alpine.store('player', {
    currentTrack: null,
    isPlaying: false,
    progress: 0,
    currentTime: 0,
    duration: 0,
    volume: 100,
    muted: false,
    
    _progressListener: null,
    _trackEndedListener: null,
    _previousVolume: 100,
    
    async init() {
      this._progressListener = await listen('audio://progress', (event) => {
        const { position_ms, duration_ms, state } = event.payload;
        this.currentTime = position_ms;
        this.duration = duration_ms;
        this.progress = duration_ms > 0 ? (position_ms / duration_ms) * 100 : 0;
        this.isPlaying = state === 'Playing';
      });
      
      this._trackEndedListener = await listen('audio://track-ended', () => {
        this.isPlaying = false;
        Alpine.store('queue').playNext();
      });
      
      try {
        const status = await invoke('audio_get_status');
        this.volume = Math.round(status.volume * 100);
      } catch (e) {
        console.warn('Could not get initial audio status:', e);
      }
    },
    
    destroy() {
      if (this._progressListener) this._progressListener();
      if (this._trackEndedListener) this._trackEndedListener();
    },
    
    async playTrack(track) {
      const trackPath = track?.filepath || track?.path;
      if (!trackPath) {
        console.error('Cannot play track without filepath/path:', track);
        return;
      }
      
      try {
        const info = await invoke('audio_load', { path: trackPath });
        this.currentTrack = { ...track, duration: info.duration_ms };
        this.duration = info.duration_ms;
        this.currentTime = 0;
        this.progress = 0;
        
        await invoke('audio_play');
        this.isPlaying = true;
      } catch (error) {
        console.error('Failed to play track:', error);
        this.isPlaying = false;
      }
    },
    
    async pause() {
      try {
        await invoke('audio_pause');
        this.isPlaying = false;
      } catch (error) {
        console.error('Failed to pause:', error);
      }
    },
    
    async resume() {
      try {
        await invoke('audio_play');
        this.isPlaying = true;
      } catch (error) {
        console.error('Failed to resume:', error);
      }
    },
    
    async toggle() {
      if (this.isPlaying) {
        await this.pause();
      } else if (this.currentTrack) {
        await this.resume();
      } else {
        const queue = Alpine.store('queue');
        if (queue.tracks.length > 0) {
          const idx = queue.currentIndex >= 0 ? queue.currentIndex : 0;
          await queue.playIndex(idx);
        }
      }
    },
    
    async stop() {
      try {
        await invoke('audio_stop');
        this.isPlaying = false;
        this.progress = 0;
        this.currentTime = 0;
        this.currentTrack = null;
      } catch (error) {
        console.error('Failed to stop:', error);
      }
    },
    
    async seek(positionMs) {
      try {
        await invoke('audio_seek', { positionMs });
        this.currentTime = positionMs;
        this.progress = this.duration > 0 ? (positionMs / this.duration) * 100 : 0;
      } catch (error) {
        console.error('Failed to seek:', error);
      }
    },
    
    async seekPercent(percent) {
      const positionMs = Math.round((percent / 100) * this.duration);
      await this.seek(positionMs);
    },
    
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
    
    formatTime(ms) {
      if (!ms || ms < 0) return '0:00';
      const totalSeconds = Math.floor(ms / 1000);
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },
    
    get formattedCurrentTime() {
      return this.formatTime(this.currentTime);
    },
    
    get formattedDuration() {
      return this.formatTime(this.duration);
    },
  });
}
