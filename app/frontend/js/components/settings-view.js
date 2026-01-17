export function createSettingsView(Alpine) {
  Alpine.data('settingsView', () => ({
    appInfo: {
      version: '—',
      build: '—',
      platform: '—',
    },
    
    async init() {
      await this.loadAppInfo();
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
  }));
}

export default createSettingsView;
