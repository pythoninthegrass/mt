export function createSettingsView(Alpine) {
  Alpine.data('settingsView', () => ({
    appInfo: {
      version: '—',
      build: '—',
      platform: '—',
    },

    // Last.fm settings
    lastfm: {
      enabled: false,
      username: null,
      authenticated: false,
      scrobbleThreshold: 90,
      isConnecting: false,
      importInProgress: false,
      queueStatus: { queued_scrobbles: 0 },
    },

    async init() {
      await this.loadAppInfo();
      await this.loadLastfmSettings();
    },
    
    async loadAppInfo() {
      if (!window.__TAURI__) {
        this.appInfo = {
          version: 'dev',
          build: 'browser',
          platform: navigator.platform || 'unknown',
        };
        return;
      }
      
      try {
        const { invoke } = window.__TAURI__.core;
        const info = await invoke('app_get_info');
        this.appInfo = {
          version: info.version || '—',
          build: info.build || '—',
          platform: info.platform || '—',
        };
      } catch (error) {
        console.error('[settings] Failed to load app info:', error);
        this.appInfo = {
          version: 'unknown',
          build: 'unknown',
          platform: 'unknown',
        };
      }
    },
    
    async resetSettings() {
      let confirmed = false;
      
      if (window.__TAURI__?.dialog?.confirm) {
        confirmed = await window.__TAURI__.dialog.confirm(
          'This will reset all settings to their defaults. Your library and playlists will not be affected.',
          { title: 'Reset Settings', kind: 'warning' }
        );
      } else {
        confirmed = confirm('This will reset all settings to their defaults. Your library and playlists will not be affected.');
      }
      
      if (!confirmed) return;
      
      const keysToReset = [
        'mt:ui:themePreset',
        'mt:ui:theme',
        'mt:settings:activeSection',
      ];
      
      keysToReset.forEach(key => localStorage.removeItem(key));
      
      window.location.reload();
    },
    
    async exportLogs() {
      if (!window.__TAURI__) {
        Alpine.store('ui').toast('Export logs is only available in the desktop app', 'info');
        return;
      }

      try {
        const { invoke } = window.__TAURI__.core;
        const { save } = window.__TAURI__.dialog;

        const path = await save({
          defaultPath: `mt-diagnostics-${new Date().toISOString().slice(0, 10)}.txt`,
          filters: [{ name: 'Text', extensions: ['txt'] }],
        });

        if (!path) return;

        await invoke('export_diagnostics', { path });
        Alpine.store('ui').toast('Diagnostics exported successfully', 'success');
      } catch (error) {
        console.error('[settings] Failed to export logs:', error);
        Alpine.store('ui').toast('Failed to export diagnostics', 'error');
      }
    },

    // ============================================
    // Last.fm methods
    // ============================================

    async loadLastfmSettings() {
      try {
        const settings = await Alpine.store('api').lastfm.getSettings();
        this.lastfm.enabled = settings.enabled;
        this.lastfm.username = settings.username;
        this.lastfm.authenticated = settings.authenticated;
        this.lastfm.scrobbleThreshold = settings.scrobble_threshold;
      } catch (error) {
        console.error('[settings] Failed to load Last.fm settings:', error);
        Alpine.store('ui').toast('Failed to load Last.fm settings', 'error');
      }
    },

    async toggleLastfm() {
      try {
        await Alpine.store('api').lastfm.updateSettings({
          enabled: !this.lastfm.enabled
        });
        this.lastfm.enabled = !this.lastfm.enabled;
        Alpine.store('ui').toast(
          `Last.fm scrobbling ${this.lastfm.enabled ? 'enabled' : 'disabled'}`,
          'success'
        );
      } catch (error) {
        console.error('[settings] Failed to toggle Last.fm:', error);
        Alpine.store('ui').toast('Failed to update Last.fm settings', 'error');
      }
    },

    async updateScrobbleThreshold() {
      try {
        // Clamp value to valid range
        const clampedValue = Math.max(25, Math.min(100, this.lastfm.scrobbleThreshold));
        if (clampedValue !== this.lastfm.scrobbleThreshold) {
          this.lastfm.scrobbleThreshold = clampedValue;
        }

        await Alpine.store('api').lastfm.updateSettings({
          scrobble_threshold: this.lastfm.scrobbleThreshold
        });
        Alpine.store('ui').toast('Scrobble threshold updated', 'success');
      } catch (error) {
        console.error('[settings] Failed to update scrobble threshold:', error);
        Alpine.store('ui').toast('Failed to update scrobble threshold', 'error');
      }
    },

    async connectLastfm() {
      this.lastfm.isConnecting = true;
      try {
        const response = await Alpine.store('api').lastfm.getAuthUrl();
        const authUrl = response.auth_url;

        // Open auth URL in browser
        if (window.__TAURI__) {
          // In Tauri app, use shell.open
          const { open } = window.__TAURI__.shell;
          await open(authUrl);
        } else {
          // In browser, open new tab
          window.open(authUrl, '_blank', 'noopener,noreferrer');
        }

        Alpine.store('ui').toast(
          'Last.fm authorization page opened. Complete the authentication and return here.',
          'info'
        );
      } catch (error) {
        console.error('[settings] Failed to get Last.fm auth URL:', error);
        Alpine.store('ui').toast('Failed to connect to Last.fm', 'error');
      } finally {
        this.lastfm.isConnecting = false;
      }
    },

    async disconnectLastfm() {
      try {
        await Alpine.store('api').lastfm.disconnect();
        this.lastfm.enabled = false;
        this.lastfm.username = null;
        this.lastfm.authenticated = false;
        Alpine.store('ui').toast('Disconnected from Last.fm', 'success');
      } catch (error) {
        console.error('[settings] Failed to disconnect from Last.fm:', error);
        Alpine.store('ui').toast('Failed to disconnect from Last.fm', 'error');
      }
    },

    async importLovedTracks() {
      if (!this.lastfm.authenticated) {
        Alpine.store('ui').toast('Please connect to Last.fm first', 'warning');
        return;
      }

      this.lastfm.importInProgress = true;
      try {
        const result = await Alpine.store('api').lastfm.importLovedTracks();
        Alpine.store('ui').toast(
          `Imported ${result.imported_count} loved tracks from Last.fm`,
          'success'
        );

        // Refresh library to show updated favorites
        Alpine.store('library').loadTracks();
      } catch (error) {
        console.error('[settings] Failed to import loved tracks:', error);
        Alpine.store('ui').toast('Failed to import loved tracks', 'error');
      } finally {
        this.lastfm.importInProgress = false;
      }
    },

    async loadQueueStatus() {
      try {
        this.lastfm.queueStatus = await Alpine.store('api').lastfm.getQueueStatus();
      } catch (error) {
        console.error('[settings] Failed to load queue status:', error);
      }
    },

    async retryQueuedScrobbles() {
      try {
        const result = await Alpine.store('api').lastfm.retryQueuedScrobbles();
        Alpine.store('ui').toast(
          `Retried queued scrobbles. ${result.remaining_queued} remaining.`,
          'success'
        );
        await this.loadQueueStatus();
      } catch (error) {
        console.error('[settings] Failed to retry queued scrobbles:', error);
        Alpine.store('ui').toast('Failed to retry queued scrobbles', 'error');
      }
    },
  }));
}

export default createSettingsView;
