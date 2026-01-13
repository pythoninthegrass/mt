/**
 * UI Store - manages application UI state
 * 
 * Handles view switching, sidebar state, modals,
 * and other UI-related state.
 */

export function createUIStore(Alpine) {
  Alpine.store('ui', {
    // Current view
    view: 'library',        // 'library', 'queue', 'nowPlaying', 'settings'
    
    // Sidebar state
    sidebarOpen: true,
    sidebarWidth: 250,      // pixels
    
    // Library view mode
    libraryViewMode: 'list', // 'list', 'grid', 'compact'
    
    // Modal state
    modal: null,            // null or { type: string, data: any }
    
    // Context menu state
    contextMenu: null,      // null or { x, y, items, data }
    
    // Toast notifications
    toasts: [],
    
    // Theme
    theme: 'system',        // 'light', 'dark', 'system'
    
    // Keyboard shortcuts enabled
    keyboardShortcutsEnabled: true,
    
    // Loading overlay
    globalLoading: false,
    loadingMessage: '',
    
    /**
     * Initialize UI state from localStorage
     */
    init() {
      // Load persisted preferences
      const saved = localStorage.getItem('mt:ui');
      if (saved) {
        try {
          const data = JSON.parse(saved);
          this.sidebarOpen = data.sidebarOpen ?? true;
          this.sidebarWidth = data.sidebarWidth ?? 250;
          this.libraryViewMode = data.libraryViewMode ?? 'list';
          this.theme = data.theme ?? 'system';
        } catch (e) {
          console.warn('Failed to load UI preferences:', e);
        }
      }
      
      // Apply theme
      this.applyTheme();
      
      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (this.theme === 'system') {
          this.applyTheme();
        }
      });
    },
    
    /**
     * Save UI preferences to localStorage
     */
    save() {
      localStorage.setItem('mt:ui', JSON.stringify({
        sidebarOpen: this.sidebarOpen,
        sidebarWidth: this.sidebarWidth,
        libraryViewMode: this.libraryViewMode,
        theme: this.theme,
      }));
    },
    
    /**
     * Set current view
     * @param {string} view - View name
     */
    setView(view) {
      const validViews = ['library', 'queue', 'nowPlaying', 'settings'];
      if (validViews.includes(view)) {
        this.view = view;
      }
    },
    
    /**
     * Toggle sidebar
     */
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen;
      this.save();
    },
    
    /**
     * Set sidebar width
     * @param {number} width - Width in pixels
     */
    setSidebarWidth(width) {
      this.sidebarWidth = Math.max(180, Math.min(400, width));
      this.save();
    },
    
    /**
     * Set library view mode
     * @param {string} mode - 'list', 'grid', or 'compact'
     */
    setLibraryViewMode(mode) {
      if (['list', 'grid', 'compact'].includes(mode)) {
        this.libraryViewMode = mode;
        this.save();
      }
    },
    
    /**
     * Set theme
     * @param {string} theme - 'light', 'dark', or 'system'
     */
    setTheme(theme) {
      if (['light', 'dark', 'system'].includes(theme)) {
        this.theme = theme;
        this.applyTheme();
        this.save();
      }
    },
    
    /**
     * Apply current theme to document
     */
    applyTheme() {
      let effectiveTheme = this.theme;
      
      if (this.theme === 'system') {
        effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches 
          ? 'dark' 
          : 'light';
      }
      
      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(effectiveTheme);
    },
    
    /**
     * Get effective theme (resolved system preference)
     */
    get effectiveTheme() {
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
