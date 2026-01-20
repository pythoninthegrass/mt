import { api } from '../api.js';

const { invoke } = window.__TAURI__?.core ?? { invoke: async () => console.warn('Tauri not available') };
const { listen } = window.__TAURI__?.event ?? { listen: async () => () => {} };

// Scrobbling state
let scrobbleCheckInterval = null;
let currentScrobbleData = null;

export function createPlayerStore(Alpine) {
  Alpine.store('player', {
    currentTrack: null,
    isPlaying: false,
    progress: 0,
    currentTime: 0,
    duration: 0,
    volume: 100,
    muted: false,
    isSeeking: false,
    isFavorite: false,
    artwork: null,

    _progressListener: null,
    _trackEndedListener: null,
    _mediaKeyListeners: [],
    _previousVolume: 100,
    _seekDebounce: null,
    _playCountUpdated: false,
    _playCountThreshold: 0.75,
    _scrobbleThreshold: 0.9, // Default 90%, will be updated from settings
    _scrobbleChecked: false,

    async init() {
      // Load Last.fm settings
      await this._loadLastfmSettings();

      this._progressListener = await listen('audio://progress', (event) => {
        if (this.isSeeking) return;
        const { position_ms, duration_ms, state } = event.payload;
        this.currentTime = position_ms;
        // Only update duration if Rust provides a valid value, or we don't have one yet
        // This preserves the database fallback duration for VBR MP3s where rodio can't determine duration
        if (duration_ms > 0 || this.duration === 0) {
          this.duration = duration_ms;
        }
        const effectiveDuration = this.duration;
        this.progress = effectiveDuration > 0 ? (position_ms / effectiveDuration) * 100 : 0;
        this.isPlaying = state === 'Playing';

        // Check for play count update
        if (!this._playCountUpdated && effectiveDuration > 0 && this.currentTrack?.id) {
          const ratio = position_ms / effectiveDuration;
          if (ratio >= this._playCountThreshold) {
            this._updatePlayCount();
          }
        }

        // Check for scrobbling
        if (!this._scrobbleChecked && effectiveDuration > 0 && this.currentTrack) {
          const ratio = position_ms / effectiveDuration;
          if (ratio >= this._scrobbleThreshold) {
            this._checkScrobble();
          }
        }
      });

      this._trackEndedListener = await listen('audio://track-ended', () => {
        this.isPlaying = false;
        Alpine.store('queue').playNext();
      });

      this._mediaKeyListeners = await Promise.all([
        listen('mediakey://play', () => this.resume()),
        listen('mediakey://pause', () => this.pause()),
        listen('mediakey://toggle', () => this.togglePlay()),
        listen('mediakey://next', () => this.next()),
        listen('mediakey://previous', () => this.previous()),
        listen('mediakey://stop', () => this.stop()),
      ]);

      try {
        const status = await invoke('audio_get_status');
        this.volume = Math.round(status.volume * 100);
      } catch (e) {
        console.warn('Could not get initial audio status:', e);
      }
    },

    async _loadLastfmSettings() {
      try {
        const settings = await api.lastfm.getSettings();
        // Convert percentage to decimal (90% -> 0.9)
        this._scrobbleThreshold = settings.scrobble_threshold / 100;
      } catch (error) {
        console.warn('[player] Failed to load Last.fm settings, using defaults:', error);
        this._scrobbleThreshold = 0.9; // Default 90%
      }
    },

    async _checkScrobble() {
      if (!this.currentTrack || this._scrobbleChecked) return;

      try {
        const settings = await api.lastfm.getSettings();
        if (!settings.enabled || !settings.authenticated) return;

        // Log the threshold check values for debugging
        const fractionPlayed = this.duration > 0 ? this.currentTime / this.duration : 0;
        console.debug('[scrobble] Threshold check:', {
          track: this.currentTrack.title,
          currentTime: this.currentTime,
          duration: this.duration,
          fractionPlayed: fractionPlayed.toFixed(3),
          thresholdFraction: this._scrobbleThreshold,
          thresholdPercent: (this._scrobbleThreshold * 100).toFixed(0) + '%',
          meetsThreshold: fractionPlayed >= this._scrobbleThreshold
        });

        // Prepare scrobble data
        // Use Math.ceil for duration/played_time to avoid off-by-one threshold failures
        // (frontend fraction check uses ms precision, but backend uses seconds)
        const scrobbleData = {
          artist: this.currentTrack.artist || 'Unknown Artist',
          track: this.currentTrack.title || 'Unknown Track',
          album: this.currentTrack.album || undefined,
          timestamp: Math.floor(Date.now() / 1000), // Current time when scrobbled
          duration: Math.ceil(this.duration / 1000), // Convert ms to seconds (ceil to avoid truncation)
          played_time: Math.ceil(this.currentTime / 1000), // Time actually played (ceil to match frontend check)
        };

        // Scrobble in background
        api.lastfm.scrobble(scrobbleData).then(result => {
          if (result.status === 'threshold_not_met') {
            console.debug('[scrobble] Threshold not met (backend):', scrobbleData.track);
          } else if (result.status === 'queued') {
            console.warn('[scrobble] Queued for retry:', result.message);
          } else if (result.status === 'disabled') {
            console.debug('[scrobble] Scrobbling disabled');
          } else if (result.status === 'not_authenticated') {
            console.debug('[scrobble] Not authenticated with Last.fm');
          } else if (result.scrobbles && result.scrobbles['@attr'] && Number(result.scrobbles['@attr'].accepted) > 0) {
            console.log('[scrobble] Successfully scrobbled:', scrobbleData.track);
          } else {
            console.warn('[scrobble] Unexpected response:', result);
          }
        }).catch(error => {
          console.error('[scrobble] Failed to scrobble:', error);
        });

        this._scrobbleChecked = true;
      } catch (error) {
        console.error('[player] Failed to check scrobble settings:', error);
      }
    },

    destroy() {
      if (this._progressListener) this._progressListener();
      if (this._trackEndedListener) this._trackEndedListener();
      this._mediaKeyListeners.forEach(unlisten => unlisten());
    },

    async playTrack(track) {
      const trackPath = track?.filepath || track?.path;
      if (!trackPath) {
        console.error('Cannot play track without filepath/path:', track);
        return;
      }

      console.log('[playback]', 'play_track', {
        trackId: track.id,
        trackTitle: track.title,
        trackArtist: track.artist,
        trackPath
      });

      try {
        const info = await invoke('audio_load', { path: trackPath });
        const trackDurationMs = track.duration ? Math.round(track.duration * 1000) : 0;
        const durationMs = (info.duration_ms > 0 ? info.duration_ms : trackDurationMs) || 0;
        console.debug('[playTrack] duration sources:', {
          rust: info.duration_ms,
          track: track.duration,
          trackMs: trackDurationMs,
          final: durationMs
        });
        this.currentTrack = { ...track, duration: durationMs };
        this.duration = durationMs;
        this.currentTime = 0;
        this.progress = 0;
        this._playCountUpdated = false;
        this._scrobbleChecked = false; // Reset scrobble check for new track

        await invoke('audio_play');
        this.isPlaying = true;

        await this.checkFavoriteStatus();
        await this.loadArtwork();
        await this._updateNowPlayingMetadata();
        await this._updateNowPlayingState();
      } catch (error) {
        console.error('[playback]', 'play_track_error', { trackId: track.id, error: error.message });
        this.isPlaying = false;
      }
    },

    async pause() {
      console.log('[playback]', 'pause', {
        trackId: this.currentTrack?.id,
        currentTime: this.currentTime
      });

      try {
        await invoke('audio_pause');
        this.isPlaying = false;
        await this._updateNowPlayingState();
      } catch (error) {
        console.error('[playback]', 'pause_error', { error: error.message });
      }
    },

    async resume() {
      console.log('[playback]', 'resume', {
        trackId: this.currentTrack?.id,
        currentTime: this.currentTime
      });

      try {
        await invoke('audio_play');
        this.isPlaying = true;
        await this._updateNowPlayingState();
      } catch (error) {
        console.error('[playback]', 'resume_error', { error: error.message });
      }
    },

    async togglePlay() {
      console.log('[playback]', 'toggle_play', {
        currentlyPlaying: this.isPlaying,
        hasTrack: !!this.currentTrack
      });

      if (this.isPlaying) {
        await this.pause();
      } else if (this.currentTrack) {
        await this.resume();
      } else {
        const queue = Alpine.store('queue');
        if (queue.items.length > 0) {
          const idx = queue.currentIndex >= 0 ? queue.currentIndex : 0;
          await queue.playIndex(idx);
        } else {
          const library = Alpine.store('library');
          if (library.filteredTracks.length > 0) {
            await queue.add(library.filteredTracks, true);
          }
        }
      }
    },

    async previous() {
      console.log('[playback]', 'previous', {
        currentTrackId: this.currentTrack?.id
      });
      await Alpine.store('queue').skipPrevious();
    },

    async next() {
      console.log('[playback]', 'next', {
        currentTrackId: this.currentTrack?.id
      });
      await Alpine.store('queue').skipNext();
    },

    async stop() {
      console.log('[playback]', 'stop', {
        trackId: this.currentTrack?.id
      });

      try {
        await invoke('audio_stop');
        this.isPlaying = false;
        this.progress = 0;
        this.currentTime = 0;
        this.currentTrack = null;
        await invoke('media_set_stopped').catch(() => {});
      } catch (error) {
        console.error('[playback]', 'stop_error', { error: error.message });
      }
    },

    async seek(positionMs) {
      if (isNaN(positionMs) || positionMs < 0) return;

      if (this._seekDebounce) {
        clearTimeout(this._seekDebounce);
      }

      const pos = Math.max(0, Math.round(positionMs));
      this.isSeeking = true;
      this.currentTime = pos;
      this.progress = this.duration > 0 ? (pos / this.duration) * 100 : 0;

      console.log('[playback]', 'seek', {
        trackId: this.currentTrack?.id,
        positionMs: pos,
        progressPercent: this.progress.toFixed(1)
      });

      this._seekDebounce = setTimeout(async () => {
        try {
          await invoke('audio_seek', { positionMs: pos });
        } catch (error) {
          console.error('[playback]', 'seek_error', { error: error.message, positionMs: pos });
        } finally {
          this.isSeeking = false;
          this._seekDebounce = null;
        }
      }, 50);
    },

    async seekPercent(percent) {
      if (!this.duration || this.duration <= 0) return;
      const positionMs = Math.round((percent / 100) * this.duration);
      if (isNaN(positionMs) || positionMs < 0) return;
      await this.seek(positionMs);
    },

    async setVolume(vol) {
      const clampedVol = Math.max(0, Math.min(100, vol));

      console.log('[playback]', 'set_volume', {
        volume: clampedVol,
        previousVolume: this.volume
      });

      try {
        await invoke('audio_set_volume', { volume: clampedVol / 100 });
        this.volume = clampedVol;
        if (clampedVol > 0) {
          this.muted = false;
        }
      } catch (error) {
        console.error('[playback]', 'set_volume_error', { error: error.message, volume: clampedVol });
      }
    },

    async toggleMute() {
      console.log('[playback]', 'toggle_mute', {
        currentlyMuted: this.muted,
        currentVolume: this.volume
      });

      if (this.muted) {
        await this.setVolume(this._previousVolume || 100);
        this.muted = false;
      } else {
        this._previousVolume = this.volume;
        await this.setVolume(0);
        this.muted = true;
      }
    },

    async checkFavoriteStatus() {
      if (!this.currentTrack?.id) {
        this.isFavorite = false;
        return;
      }

      try {
        const result = await api.favorites.check(this.currentTrack.id);
        this.isFavorite = result.is_favorite;
      } catch (error) {
        console.error('Failed to check favorite status:', error);
        this.isFavorite = false;
      }
    },

    async toggleFavorite() {
      if (!this.currentTrack?.id) return;

      console.log('[playback]', 'toggle_favorite', {
        trackId: this.currentTrack.id,
        trackTitle: this.currentTrack.title,
        currentlyFavorite: this.isFavorite,
        action: this.isFavorite ? 'remove' : 'add'
      });

      try {
        if (this.isFavorite) {
          await api.favorites.remove(this.currentTrack.id);
          this.isFavorite = false;
        } else {
          await api.favorites.add(this.currentTrack.id);
          this.isFavorite = true;
        }

        Alpine.store('library').refreshIfLikedSongs();
      } catch (error) {
        console.error('[playback]', 'toggle_favorite_error', {
          trackId: this.currentTrack.id,
          error: error.message
        });
      }
    },

    async loadArtwork() {
      if (!this.currentTrack?.id) {
        this.artwork = null;
        return;
      }

      try {
        this.artwork = await api.library.getArtwork(this.currentTrack.id);
      } catch (error) {
        // Silently fail if artwork not found (404 is expected for tracks without artwork)
        if (error.status !== 404) {
          console.error('Failed to load artwork:', error);
        }
        this.artwork = null;
      }
    },

    async _updatePlayCount() {
      if (this._playCountUpdated || !this.currentTrack?.id) return;

      this._playCountUpdated = true;
      try {
        await api.library.updatePlayCount(this.currentTrack.id);
      } catch (error) {
        console.error('Failed to update play count:', error);
      }
    },

    async _updateNowPlayingMetadata() {
      if (!this.currentTrack) return;

      try {
        await invoke('media_set_metadata', {
          title: this.currentTrack.title || null,
          artist: this.currentTrack.artist || null,
          album: this.currentTrack.album || null,
          durationMs: this.duration || null,
          coverUrl: null,
        });
      } catch (error) {
        console.warn('Failed to update Now Playing metadata:', error);
      }

      // Update Last.fm Now Playing in background
      this._updateLastfmNowPlaying();
    },

    async _updateLastfmNowPlaying() {
      if (!this.currentTrack) return;

      try {
        const nowPlayingData = {
          artist: this.currentTrack.artist || 'Unknown Artist',
          track: this.currentTrack.title || 'Unknown Track',
          album: this.currentTrack.album || undefined,
          duration: Math.floor(this.duration / 1000), // Convert ms to seconds
        };

        api.lastfm.updateNowPlaying(nowPlayingData).then(result => {
          if (result.status === 'disabled' || result.status === 'not_authenticated') {
            // Silently ignore if not configured
            return;
          }
          console.debug('[lastfm] Now Playing updated:', nowPlayingData.track);
        }).catch(error => {
          console.warn('[lastfm] Failed to update Now Playing:', error);
        });
      } catch (error) {
        // Silently ignore Now Playing errors
        console.warn('[lastfm] Error preparing Now Playing data:', error);
      }
    },

    async _updateNowPlayingState() {
      try {
        if (this.isPlaying) {
          await invoke('media_set_playing', { progressMs: this.currentTime || null });
        } else {
          await invoke('media_set_paused', { progressMs: this.currentTime || null });
        }
      } catch (error) {
        console.warn('Failed to update Now Playing state:', error);
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
