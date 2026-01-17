export function createMetadataModal(Alpine) {
  Alpine.data('metadataModal', () => ({
    isOpen: false,
    isLoading: false,
    isSaving: false,
    tracks: [],
    library: null,
    metadata: {
      title: '',
      artist: '',
      album: '',
      album_artist: '',
      track_number: '',
      track_total: '',
      disc_number: '',
      disc_total: '',
      year: '',
      genre: '',
    },
    originalMetadata: {},
    mixedFields: new Set(),
    fileInfo: {
      format: '',
      duration: '',
      bitrate: '',
      sample_rate: '',
      channels: '',
      path: '',
    },

    init() {
      this.$watch('$store.ui.modal', (modal) => {
        if (modal?.type === 'editMetadata') {
          this.open(modal.data);
        } else if (this.isOpen) {
          this.close();
        }
      });
    },

    get isBatchEdit() {
      return this.tracks.length > 1;
    },

    get modalTitle() {
      if (this.isBatchEdit) {
        return `Edit Metadata (${this.tracks.length} tracks)`;
      }
      return 'Edit Metadata';
    },

    async open(data) {
      this.tracks = data.tracks || (data.track ? [data.track] : []);
      this.library = data.library;
      this.isOpen = true;
      this.isLoading = true;
      this.mixedFields = new Set();

      try {
        await this.loadMetadata();
      } catch (error) {
        console.error('[metadata] Failed to load metadata:', error);
        Alpine.store('ui').toast('Failed to load track metadata', 'error');
        this.close();
      } finally {
        this.isLoading = false;
      }
    },

    close() {
      this.isOpen = false;
      this.tracks = [];
      this.library = null;
      this.mixedFields = new Set();
      this.$store.ui.closeModal();
    },

    getTrackPath(track) {
      return track?.path || track?.filepath;
    },

    async loadMetadata() {
      if (this.tracks.length === 0) {
        throw new Error('No tracks to edit');
      }

      if (this.isBatchEdit) {
        await this.loadBatchMetadata();
      } else {
        await this.loadSingleMetadata();
      }

      this.originalMetadata = { ...this.metadata };
    },

    async loadSingleMetadata() {
      const track = this.tracks[0];
      const trackPath = this.getTrackPath(track);
      if (!trackPath) {
        throw new Error('No track path available');
      }

      if (!window.__TAURI__) {
        this.metadata = {
          title: track.title || '',
          artist: track.artist || '',
          album: track.album || '',
          album_artist: track.album_artist || '',
          track_number: track.track_number?.toString() || '',
          track_total: '',
          disc_number: track.disc_number?.toString() || '',
          disc_total: '',
          year: track.year?.toString() || '',
          genre: track.genre || '',
        };
        this.fileInfo = {
          format: 'Unknown',
          duration: this.formatDuration(track.duration),
          bitrate: '—',
          sample_rate: '—',
          channels: '—',
          path: trackPath,
        };
        return;
      }

      const { invoke } = window.__TAURI__.core;
      const data = await invoke('get_track_metadata', { path: trackPath });

      this.metadata = {
        title: data.title || '',
        artist: data.artist || '',
        album: data.album || '',
        album_artist: data.album_artist || '',
        track_number: data.track_number?.toString() || '',
        track_total: data.track_total?.toString() || '',
        disc_number: data.disc_number?.toString() || '',
        disc_total: data.disc_total?.toString() || '',
        year: data.year?.toString() || '',
        genre: data.genre || '',
      };

      this.fileInfo = {
        format: data.format || 'Unknown',
        duration: this.formatDuration(data.duration_ms ? data.duration_ms / 1000 : 0),
        bitrate: data.bitrate ? `${data.bitrate} kbps` : '—',
        sample_rate: data.sample_rate ? `${data.sample_rate} Hz` : '—',
        channels: data.channels ? (data.channels === 1 ? 'Mono' : data.channels === 2 ? 'Stereo' : `${data.channels} ch`) : '—',
        path: data.path || '',
      };
    },

    async loadBatchMetadata() {
      const fields = ['title', 'artist', 'album', 'album_artist', 'track_number', 'track_total', 'disc_number', 'disc_total', 'year', 'genre'];
      const allMetadata = [];

      for (const track of this.tracks) {
        const trackPath = this.getTrackPath(track);
        if (!trackPath) continue;

        let trackMeta;
        if (!window.__TAURI__) {
          trackMeta = {
            title: track.title || '',
            artist: track.artist || '',
            album: track.album || '',
            album_artist: track.album_artist || '',
            track_number: track.track_number?.toString() || '',
            track_total: '',
            disc_number: track.disc_number?.toString() || '',
            disc_total: '',
            year: track.year?.toString() || '',
            genre: track.genre || '',
          };
        } else {
          const { invoke } = window.__TAURI__.core;
          const data = await invoke('get_track_metadata', { path: trackPath });
          trackMeta = {
            title: data.title || '',
            artist: data.artist || '',
            album: data.album || '',
            album_artist: data.album_artist || '',
            track_number: data.track_number?.toString() || '',
            track_total: data.track_total?.toString() || '',
            disc_number: data.disc_number?.toString() || '',
            disc_total: data.disc_total?.toString() || '',
            year: data.year?.toString() || '',
            genre: data.genre || '',
          };
        }
        allMetadata.push(trackMeta);
      }

      const mergedMetadata = {};
      for (const field of fields) {
        const values = allMetadata.map(m => m[field]);
        const uniqueValues = [...new Set(values)];
        if (uniqueValues.length === 1) {
          mergedMetadata[field] = uniqueValues[0];
        } else {
          mergedMetadata[field] = '';
          this.mixedFields.add(field);
        }
      }

      this.metadata = mergedMetadata;

      const totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
      this.fileInfo = {
        format: 'Multiple',
        duration: this.formatDuration(totalDuration),
        bitrate: '—',
        sample_rate: '—',
        channels: '—',
        path: `${this.tracks.length} files selected`,
      };
    },

    isMixedField(field) {
      return this.mixedFields.has(field);
    },

    getPlaceholder(field) {
      if (this.isMixedField(field)) {
        return 'Multiple values';
      }
      return '';
    },

    hasFieldChanged(field) {
      return this.metadata[field] !== this.originalMetadata[field];
    },

    async save() {
      if (!window.__TAURI__) {
        Alpine.store('ui').toast('Cannot save: Tauri not available', 'error');
        return;
      }

      this.isSaving = true;

      try {
        const { invoke } = window.__TAURI__.core;
        let savedCount = 0;

        for (const track of this.tracks) {
          const trackPath = this.getTrackPath(track);
          if (!trackPath) continue;

          const update = { path: trackPath };
          let hasChanges = false;

          const fields = ['title', 'artist', 'album', 'album_artist', 'genre'];
          for (const field of fields) {
            if (this.hasFieldChanged(field) || !this.isBatchEdit) {
              update[field] = this.metadata[field] || null;
              hasChanges = true;
            }
          }

          const intFields = ['track_number', 'track_total', 'disc_number', 'disc_total', 'year'];
          for (const field of intFields) {
            if (this.hasFieldChanged(field) || !this.isBatchEdit) {
              update[field] = this.metadata[field] ? parseInt(this.metadata[field], 10) : null;
              hasChanges = true;
            }
          }

          if (hasChanges) {
            await invoke('save_track_metadata', { update });
            savedCount++;
          }
        }

        if (savedCount > 0) {
          const msg = savedCount === 1 ? 'Metadata saved successfully' : `Metadata saved for ${savedCount} tracks`;
          Alpine.store('ui').toast(msg, 'success');

          if (this.library) {
            for (const track of this.tracks) {
              await this.library.rescanTrack(track.id);
            }
          }
        }

        this.close();
      } catch (error) {
        console.error('[metadata] Failed to save metadata:', error);
        Alpine.store('ui').toast(`Failed to save: ${error}`, 'error');
      } finally {
        this.isSaving = false;
      }
    },

    formatDuration(seconds) {
      if (!seconds) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    handleKeydown(event) {
      if (event.key === 'Escape') {
        this.close();
      } else if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        this.save();
      }
    },
  }));
}
