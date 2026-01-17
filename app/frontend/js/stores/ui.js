export function createUIStore(Alpine) {
  Alpine.store('ui', {
    view: 'library',
    
    sidebarOpen: Alpine.$persist(true).as('mt:ui:sidebarOpen'),
    sidebarWidth: Alpine.$persist(250).as('mt:ui:sidebarWidth'),
    libraryViewMode: Alpine.$persist('list').as('mt:ui:libraryViewMode'),
    theme: Alpine.$persist('system').as('mt:ui:theme'),
    themePreset: Alpine.$persist('light').as('mt:ui:themePreset'),
    
    modal: null,
    contextMenu: null,
    toasts: [],
    keyboardShortcutsEnabled: true,
    globalLoading: false,
    loadingMessage: '',
    
    init() {
      this._migrateOldStorage();
      this.applyThemePreset();
      
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (this.themePreset === 'light' && this.theme === 'system') {
          this.applyThemePreset();
        }
      });
    },
    
    _migrateOldStorage() {
      const oldData = localStorage.getItem('mt:ui');
      if (oldData) {
        try {
          const data = JSON.parse(oldData);
          if (data.sidebarOpen !== undefined) this.sidebarOpen = data.sidebarOpen;
          if (data.sidebarWidth !== undefined) this.sidebarWidth = data.sidebarWidth;
          if (data.libraryViewMode !== undefined) this.libraryViewMode = data.libraryViewMode;
          if (data.theme !== undefined) this.theme = data.theme;
          localStorage.removeItem('mt:ui');
        } catch (e) {
          localStorage.removeItem('mt:ui');
        }
      }
    },
    
    setView(view) {
      const validViews = ['library', 'queue', 'nowPlaying', 'settings'];
      if (validViews.includes(view)) {
        this.view = view;
      }
    },
    
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen;
    },
    
    setSidebarWidth(width) {
      this.sidebarWidth = Math.max(180, Math.min(400, width));
    },
    
    setLibraryViewMode(mode) {
      if (['list', 'grid', 'compact'].includes(mode)) {
        this.libraryViewMode = mode;
      }
    },
    
    setTheme(theme) {
      if (['light', 'dark', 'system'].includes(theme)) {
        this.theme = theme;
        this.applyTheme();
      }
    },
    
    setThemePreset(preset) {
      if (['light', 'metro-teal'].includes(preset)) {
        this.themePreset = preset;
        this.applyThemePreset();
      }
    },
    
    applyThemePreset() {
      document.documentElement.classList.remove('light', 'dark');
      delete document.documentElement.dataset.themePreset;
      
      if (this.themePreset === 'metro-teal') {
        document.documentElement.classList.add('dark');
        document.documentElement.dataset.themePreset = 'metro-teal';
      } else {
        let effectiveTheme = this.theme;
        if (this.theme === 'system') {
          effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches 
            ? 'dark' 
            : 'light';
        }
        document.documentElement.classList.add(effectiveTheme);
      }
    },
    
    applyTheme() {
      this.applyThemePreset();
    },
    
    get effectiveTheme() {
      if (this.themePreset === 'metro-teal') {
        return 'dark';
      }
      if (this.theme === 'system') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches 
          ? 'dark' 
          : 'light';
      }
      return this.theme;
    },
    
    /**
     * Open modal
     * @param {string} type - Modal type
     * @param {any} data - Modal data
     */
    openModal(type, data = null) {
      this.modal = { type, data };
    },
    
    /**
     * Close modal
     */
    closeModal() {
      this.modal = null;
    },
    
    /**
     * Show context menu
     * @param {number} x - X position
     * @param {number} y - Y position
     * @param {Array} items - Menu items
     * @param {any} data - Associated data
     */
    showContextMenu(x, y, items, data = null) {
      this.contextMenu = { x, y, items, data };
    },
    
    /**
     * Hide context menu
     */
    hideContextMenu() {
      this.contextMenu = null;
    },
    
    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - 'info', 'success', 'warning', 'error'
     * @param {number} duration - Duration in ms (0 = persistent)
     */
    toast(message, type = 'info', duration = 3000) {
      const id = Date.now();
      this.toasts.push({ id, message, type });
      
      if (duration > 0) {
        setTimeout(() => {
          this.dismissToast(id);
        }, duration);
      }
      
      return id;
    },
    
    /**
     * Dismiss toast by ID
     * @param {number} id - Toast ID
     */
    dismissToast(id) {
      this.toasts = this.toasts.filter(t => t.id !== id);
    },
    
    /**
     * Show global loading overlay
     * @param {string} message - Loading message
     */
    showLoading(message = 'Loading...') {
      this.globalLoading = true;
      this.loadingMessage = message;
    },
    
    /**
     * Hide global loading overlay
     */
    hideLoading() {
      this.globalLoading = false;
      this.loadingMessage = '';
    },
    
    /**
     * Check if current view is active
     * @param {string} view - View to check
     */
    isView(view) {
      return this.view === view;
    },
  });
}
