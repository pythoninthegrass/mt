import { api } from '../api.js';

// Default column widths in pixels (all columns have explicit widths for grid layout)
const DEFAULT_COLUMN_WIDTHS = {
  index: 48,
  title: 320,
  artist: 180,
  album: 180,
  lastPlayed: 120,
  dateAdded: 120,
  playCount: 60,
  duration: 64,
};

// Minimum column widths to prevent unusable columns
const MIN_COLUMN_WIDTH = 40;
const MIN_TITLE_WIDTH = 120;

// Storage key for column settings
const COLUMN_SETTINGS_KEY = 'mt:column-settings';

export function createLibraryBrowser(Alpine) {
  Alpine.data('libraryBrowser', () => ({
    selectedTracks: new Set(),
    lastSelectedIndex: -1,
    contextMenu: null,
    headerContextMenu: null,
    playlists: [],
    showPlaylistSubmenu: false,
    submenuOnLeft: false,
    currentPlaylistId: null,
    draggingIndex: null,
    dragOverIndex: null,

    // Column resize state
    resizingColumn: null,
    resizeStartX: 0,
    resizeStartWidth: 0,
    wasResizing: false,

    // Column drag/reorder state
    draggingColumnKey: null,
    dragOverColumnKey: null,
    columnDragX: 0,

    // Column customization state
    columnWidths: { ...DEFAULT_COLUMN_WIDTHS },
    columnVisibility: {
      index: true,
      title: true,
      artist: true,
      album: true,
      lastPlayed: true,
      dateAdded: true,
      playCount: true,
      duration: true,
    },
    columnOrder: ['index', 'title', 'artist', 'album', 'lastPlayed', 'dateAdded', 'playCount', 'duration'],

    // Base column definitions
    baseColumns: [
      { key: 'index', label: '#', sortable: false, minWidth: 40, canHide: false },
      { key: 'title', label: 'Title', sortable: true, minWidth: 100, canHide: false },
      { key: 'artist', label: 'Artist', sortable: true, minWidth: 80, canHide: true },
      { key: 'album', label: 'Album', sortable: true, minWidth: 80, canHide: true },
    ],

    // Extra columns for dynamic playlists
    extraColumns: {
      recent: {
        key: 'lastPlayed',
        label: 'Last Played',
        sortable: true,
        minWidth: 80,
        canHide: true,
      },
      added: { key: 'dateAdded', label: 'Added', sortable: true, minWidth: 80, canHide: true },
      top25: { key: 'playCount', label: 'Plays', sortable: true, minWidth: 50, canHide: true },
    },

    getColumnDef(key) {
      const baseDef = this.baseColumns.find(c => c.key === key);
      if (baseDef) return baseDef;
      
      for (const extra of Object.values(this.extraColumns)) {
        if (extra.key === key) return extra;
      }
      
      if (key === 'duration') {
        return { key: 'duration', label: 'Time', sortable: true, minWidth: 60, canHide: true };
      }
      return null;
    },

    get columns() {
      const section = this.library.currentSection;
      const availableKeys = new Set(['index', 'title', 'artist', 'album', 'duration']);
      
      if (this.extraColumns[section]) {
        availableKeys.add(this.extraColumns[section].key);
      }

      return this.columnOrder
        .filter(key => availableKeys.has(key) && this.columnVisibility[key] !== false)
        .map(key => this.getColumnDef(key))
        .filter(Boolean);
    },

    get allColumns() {
      const section = this.library.currentSection;
      const availableKeys = new Set(['index', 'title', 'artist', 'album', 'duration']);
      
      if (this.extraColumns[section]) {
        availableKeys.add(this.extraColumns[section].key);
      }

      return this.columnOrder
        .filter(key => availableKeys.has(key))
        .map(key => this.getColumnDef(key))
        .filter(Boolean);
    },

    getColumnStyle(col) {
      const width = this.columnWidths[col.key] || DEFAULT_COLUMN_WIDTHS[col.key] || 100;
      const minWidth = col.key === 'title' ? MIN_TITLE_WIDTH : (col.minWidth || MIN_COLUMN_WIDTH);
      return `width: ${Math.max(width, minWidth)}px; min-width: ${minWidth}px;`;
    },

    getGridTemplateColumns() {
      return this.columns.map(col => {
        const width = this.columnWidths[col.key] || DEFAULT_COLUMN_WIDTHS[col.key] || 100;
        const minWidth = col.key === 'title' ? MIN_TITLE_WIDTH : (col.minWidth || MIN_COLUMN_WIDTH);
        const actualWidth = Math.max(width, minWidth);
        if (col.key === 'title') {
          return `minmax(${actualWidth}px, 1fr)`;
        }
        return `${actualWidth}px`;
      }).join(' ');
    },

    // Check if column is visible
    isColumnVisible(key) {
      return this.columnVisibility[key] !== false;
    },

    // Toggle column visibility
    toggleColumnVisibility(key) {
      const col = this.allColumns.find((c) => c.key === key);
      if (!col || !col.canHide) return;

      // Count visible columns that can be hidden
      const visibleHideableCount = this.allColumns.filter(
        (c) => c.canHide && this.columnVisibility[c.key] !== false,
      ).length;

      // Prevent hiding if it's the last hideable visible column
      if (this.columnVisibility[key] !== false && visibleHideableCount <= 1) {
        return;
      }

      this.columnVisibility[key] = !this.columnVisibility[key];
      this.saveColumnSettings();
    },

    // Get count of visible columns (for preventing hiding all)
    get visibleColumnCount() {
      return this.allColumns.filter((col) => this.columnVisibility[col.key] !== false).length;
    },

    init() {
      this.loadColumnSettings();

      if (this.$store.library.tracks.length === 0 && !this.$store.library.loading) {
        this.$store.library.load();
      }

      this.loadPlaylists();

      document.addEventListener('click', (e) => {
        if (this.contextMenu && !e.target.closest('.context-menu')) {
          this.contextMenu = null;
          this.showPlaylistSubmenu = false;
        }
        if (this.headerContextMenu && !e.target.closest('.header-context-menu')) {
          this.headerContextMenu = null;
        }
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          if (this.contextMenu) {
            this.contextMenu = null;
            this.showPlaylistSubmenu = false;
          }
          if (this.headerContextMenu) {
            this.headerContextMenu = null;
          }
        }
      });

      document.addEventListener('mouseup', () => {
        if (this.resizingColumn) {
          this.finishColumnResize();
        }
      });

      document.addEventListener('mousemove', (e) => {
        if (this.resizingColumn) {
          this.handleColumnResize(e);
        }
      });

      this.$watch('$store.player.currentTrack', (newTrack) => {
        if (newTrack?.id) {
          this.scrollToTrack(newTrack.id);
        }
      });

      window.addEventListener('mt:section-change', (e) => {
        this.clearSelection();
        const section = e.detail?.section || '';
        if (section.startsWith('playlist-')) {
          this.currentPlaylistId = parseInt(section.replace('playlist-', ''), 10);
        } else {
          this.currentPlaylistId = null;
        }
      });

      window.addEventListener('mt:playlists-updated', () => {
        this.loadPlaylists();
      });
    },

    loadColumnSettings() {
      try {
        const saved = localStorage.getItem(COLUMN_SETTINGS_KEY);
        if (saved) {
          const data = JSON.parse(saved);
          if (data.widths) {
            this.columnWidths = { ...DEFAULT_COLUMN_WIDTHS, ...data.widths };
          }
          if (data.visibility) {
            this.columnVisibility = { ...this.columnVisibility, ...data.visibility };
          }
          if (data.order && Array.isArray(data.order)) {
            this.columnOrder = data.order;
          }
        }
      } catch (e) {
        console.warn('Failed to load column settings:', e);
      }
    },

    saveColumnSettings() {
      try {
        localStorage.setItem(
          COLUMN_SETTINGS_KEY,
          JSON.stringify({
            widths: this.columnWidths,
            visibility: this.columnVisibility,
            order: this.columnOrder,
          }),
        );
      } catch (e) {
        console.warn('Failed to save column settings:', e);
      }
    },

    startColumnResize(col, event) {
      event.preventDefault();
      event.stopPropagation();

      this.resizingColumn = col.key;
      this.resizeStartX = event.clientX;
      this.resizeStartWidth = this.columnWidths[col.key] || DEFAULT_COLUMN_WIDTHS[col.key] || 100;

      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    },

    handleColumnResize(event) {
      if (!this.resizingColumn) return;

      const delta = event.clientX - this.resizeStartX;
      const col = this.allColumns.find((c) => c.key === this.resizingColumn);
      const minWidth = col?.key === 'title' ? MIN_TITLE_WIDTH : (col?.minWidth || MIN_COLUMN_WIDTH);
      const newWidth = Math.max(minWidth, this.resizeStartWidth + delta);

      this.columnWidths[this.resizingColumn] = newWidth;
    },

    finishColumnResize() {
      if (!this.resizingColumn) return;

      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      this.saveColumnSettings();
      this.wasResizing = true;
      this.resizingColumn = null;
      setTimeout(() => {
        this.wasResizing = false;
      }, 100);
    },

    startColumnDrag(col, event) {
      if (this.resizingColumn) return;
      
      event.preventDefault();
      this.draggingColumnKey = col.key;
      this.dragOverColumnKey = null;
      this.columnDragX = event.clientX;

      document.body.style.cursor = 'grabbing';
      document.body.style.userSelect = 'none';

      const onMove = (e) => {
        this.columnDragX = e.clientX;
        this.updateColumnDropTarget(e.clientX);
      };

      const onEnd = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onEnd);
        this.finishColumnDrag();
      };

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onEnd);
    },

    updateColumnDropTarget(x) {
      const header = document.querySelector('[data-testid="library-header"]');
      if (!header) return;

      const cells = header.querySelectorAll(':scope > div');
      let targetKey = null;

      for (const cell of cells) {
        const rect = cell.getBoundingClientRect();
        const midX = rect.left + rect.width / 2;
        
        if (x < midX) {
          const colIndex = Array.from(cells).indexOf(cell);
          if (colIndex >= 0 && colIndex < this.columns.length) {
            targetKey = this.columns[colIndex].key;
          }
          break;
        }
      }

      if (targetKey === null && this.columns.length > 0) {
        targetKey = this.columns[this.columns.length - 1].key;
      }

      if (targetKey !== this.draggingColumnKey) {
        this.dragOverColumnKey = targetKey;
      }
    },

    finishColumnDrag() {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      if (this.draggingColumnKey && this.dragOverColumnKey && 
          this.draggingColumnKey !== this.dragOverColumnKey) {
        this.reorderColumn(this.draggingColumnKey, this.dragOverColumnKey);
      }

      this.draggingColumnKey = null;
      this.dragOverColumnKey = null;
    },

    reorderColumn(fromKey, toKey) {
      const fromIdx = this.columnOrder.indexOf(fromKey);
      const toIdx = this.columnOrder.indexOf(toKey);
      
      if (fromIdx === -1 || toIdx === -1) return;

      const newOrder = [...this.columnOrder];
      newOrder.splice(fromIdx, 1);
      newOrder.splice(toIdx, 0, fromKey);
      
      this.columnOrder = newOrder;
      this.saveColumnSettings();
    },

    isColumnDragging(key) {
      return this.draggingColumnKey === key;
    },

    getColumnDragClass(key) {
      if (!this.draggingColumnKey) return '';
      if (key === this.draggingColumnKey) return 'opacity-50';
      if (key === this.dragOverColumnKey) return 'border-l-2 border-l-primary';
      return '';
    },

    autoFitColumn(col, event) {
      event.preventDefault();
      event.stopPropagation();

      const rows = document.querySelectorAll(`[data-column="${col.key}"]`);
      const minWidth = col.key === 'title' ? MIN_TITLE_WIDTH : (col.minWidth || MIN_COLUMN_WIDTH);
      let maxWidth = minWidth;

      rows.forEach((row) => {
        const textWidth = this.measureTextWidth(row.textContent || '', row);
        maxWidth = Math.max(maxWidth, textWidth + 24);
      });

      const maxAllowed = col.key === 'title' ? 600 : 400;
      maxWidth = Math.min(maxWidth, maxAllowed);

      this.columnWidths[col.key] = maxWidth;
      this.saveColumnSettings();
    },

    measureTextWidth(text, element) {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      const style = window.getComputedStyle(element);
      context.font = `${style.fontSize} ${style.fontFamily}`;
      return context.measureText(text).width;
    },

    handleHeaderContextMenu(event) {
      event.preventDefault();

      const menuItems = this.allColumns
        .filter((col) => col.canHide)
        .map((col) => ({
          key: col.key,
          label: col.label,
          visible: this.columnVisibility[col.key] !== false,
          canToggle: this.columnVisibility[col.key] === false ||
            this.allColumns.filter((c) => c.canHide && this.columnVisibility[c.key] !== false)
                .length > 1,
        }));

      let x = event.clientX;
      let y = event.clientY;
      const menuWidth = 180;
      const menuHeight = menuItems.length * 32 + 16;

      if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
      }
      if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
      }

      this.headerContextMenu = { x, y, items: menuItems };
    },

    resetColumnWidths() {
      this.columnWidths = { ...DEFAULT_COLUMN_WIDTHS };
      this.columnOrder = ['index', 'title', 'artist', 'album', 'lastPlayed', 'dateAdded', 'playCount', 'duration'];
      this.saveColumnSettings();
      this.headerContextMenu = null;
    },

    showAllColumns() {
      for (const col of this.allColumns) {
        this.columnVisibility[col.key] = true;
      }
      this.saveColumnSettings();
      this.headerContextMenu = null;
    },

    async loadPlaylists() {
      try {
        const data = await api.playlists.getAll();
        this.playlists = data.playlists || [];
      } catch (error) {
        console.error('Failed to load playlists:', error);
        this.playlists = [];
      }
    },

    scrollToTrack(trackId) {
      this.$nextTick(() => {
        const trackRow = document.querySelector(`[data-track-id="${trackId}"]`);
        if (trackRow) {
          trackRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    },

    /**
     * Get the library store
     */
    get library() {
      return this.$store.library;
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
     * Get sort indicator for column
     * @param {string} key - Column key
     */
    getSortIndicator(key) {
      if (this.library.sortBy !== key) return '';
      return this.library.sortOrder === 'asc' ? '▲' : '▼';
    },

    handleSort(key) {
      const col = this.allColumns.find(c => c.key === key);
      if (!col?.sortable || this.wasResizing) {
        return;
      }
      this.library.setSortBy(key);
    },

    /**
     * Handle track row click
     * @param {Event} event - Click event
     * @param {Object} track - Track object
     * @param {number} index - Track index
     */
    handleRowClick(event, track, index) {
      if (event.shiftKey && this.lastSelectedIndex >= 0) {
        // Shift+click: range selection
        const start = Math.min(this.lastSelectedIndex, index);
        const end = Math.max(this.lastSelectedIndex, index);

        if (!event.ctrlKey && !event.metaKey) {
          this.selectedTracks.clear();
        }

        for (let i = start; i <= end; i++) {
          const t = this.library.filteredTracks[i];
          if (t) this.selectedTracks.add(t.id);
        }
      } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd+click: toggle selection
        if (this.selectedTracks.has(track.id)) {
          this.selectedTracks.delete(track.id);
        } else {
          this.selectedTracks.add(track.id);
        }
        this.lastSelectedIndex = index;
      } else {
        // Regular click: single selection
        this.selectedTracks.clear();
        this.selectedTracks.add(track.id);
        this.lastSelectedIndex = index;
      }
    },

    async handleDoubleClick(track) {
      await this.queue.clear();
      await this.queue.add(this.library.filteredTracks, false);
      const index = this.library.filteredTracks.findIndex((t) => t.id === track.id);
      if (index >= 0) {
        await this.queue.playIndex(index);
      } else {
        await this.player.playTrack(track);
      }
    },

    /**
     * Handle right-click context menu
     * @param {Event} event - Context menu event
     * @param {Object} track - Track object
     * @param {number} index - Track index
     */
    handleContextMenu(event, track, index) {
      event.preventDefault();

      // Select track if not already selected
      if (!this.selectedTracks.has(track.id)) {
        this.selectedTracks.clear();
        this.selectedTracks.add(track.id);
        this.lastSelectedIndex = index;
      }

      const selectedCount = this.selectedTracks.size;
      const trackLabel = selectedCount === 1 ? 'track' : `${selectedCount} tracks`;

      const isInPlaylist = this.currentPlaylistId !== null;

      const menuItems = [
        {
          label: 'Play Now',
          action: () => this.playSelected(),
        },
        {
          label: `Add ${trackLabel} to Queue`,
          action: () => this.addSelectedToQueue(),
        },
        { type: 'separator' },
        {
          label: 'Play Next',
          action: () => this.playSelectedNext(),
        },
        {
          label: 'Add to Playlist',
          hasSubmenu: true,
          action: () => {
            this.showPlaylistSubmenu = !this.showPlaylistSubmenu;
          },
        },
      ];

      if (isInPlaylist) {
        menuItems.push({ type: 'separator' });
        menuItems.push({
          label: `Remove ${trackLabel} from Playlist`,
          action: () => this.removeFromPlaylist(),
        });
      }

      menuItems.push({ type: 'separator' });
      menuItems.push({
        label: 'Show in Finder',
        action: () => this.showInFinder(track),
        disabled: selectedCount > 1,
      });
      menuItems.push({
        label: 'Track Info...',
        action: () => this.showTrackInfo(track),
        disabled: selectedCount > 1,
      });
      menuItems.push({ type: 'separator' });
      menuItems.push({
        label: `Remove ${trackLabel} from Library`,
        action: () => this.removeSelected(),
        danger: true,
      });

      const menuHeight = 320;
      const menuWidth = 200;
      let x = event.clientX;
      let y = event.clientY;

      if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
      }
      if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
      }

      this.contextMenu = {
        x,
        y,
        track,
        items: menuItems,
      };
      this.showPlaylistSubmenu = false;
      this.submenuOnLeft = false;
    },

    /**
     * Check if track is selected
     * @param {string} trackId - Track ID
     */
    isSelected(trackId) {
      return this.selectedTracks.has(trackId);
    },

    /**
     * Check if track is currently playing
     * @param {string} trackId - Track ID
     */
    isPlaying(trackId) {
      return this.player.currentTrack?.id === trackId;
    },

    /**
     * Get selected tracks
     */
    getSelectedTracks() {
      return this.library.filteredTracks.filter((t) => this.selectedTracks.has(t.id));
    },

    /**
     * Play selected tracks
     */
    async playSelected() {
      const tracks = this.getSelectedTracks();
      if (tracks.length > 0) {
        await this.queue.clear();
        await this.queue.addTracks(tracks);
        await this.player.playTrack(tracks[0]);
      }
      this.contextMenu = null;
    },

    /**
     * Add selected tracks to queue
     */
    async addSelectedToQueue() {
      const tracks = this.getSelectedTracks();
      if (tracks.length > 0) {
        await this.queue.addTracks(tracks);
        this.$store.ui.toast(
          `Added ${tracks.length} track${tracks.length > 1 ? 's' : ''} to queue`,
          'success',
        );
      }
      this.contextMenu = null;
    },

    /**
     * Play selected tracks next
     */
    async playSelectedNext() {
      const tracks = this.getSelectedTracks();
      if (tracks.length > 0) {
        // Insert after current track
        const insertIndex = this.queue.currentIndex + 1;
        for (let i = 0; i < tracks.length; i++) {
          await this.queue.add(tracks[i].id, insertIndex + i);
        }
        this.$store.ui.toast(
          `Playing ${tracks.length} track${tracks.length > 1 ? 's' : ''} next`,
          'success',
        );
      }
      this.contextMenu = null;
    },

    async addToPlaylist(playlistId) {
      const tracks = this.getSelectedTracks();
      if (tracks.length === 0) return;

      try {
        const trackIds = tracks.map((t) => t.id);
        const result = await api.playlists.addTracks(playlistId, trackIds);
        const playlist = this.playlists.find((p) => p.id === playlistId);
        const playlistName = playlist?.name || 'playlist';

        if (result.added > 0) {
          this.$store.ui.toast(
            `Added ${result.added} track${result.added > 1 ? 's' : ''} to "${playlistName}"`,
            'success',
          );
        } else {
          this.$store.ui.toast(
            `Track${tracks.length > 1 ? 's' : ''} already in "${playlistName}"`,
            'info',
          );
        }

        window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
      } catch (error) {
        console.error('Failed to add to playlist:', error);
        this.$store.ui.toast('Failed to add to playlist', 'error');
      }

      this.contextMenu = null;
      this.showPlaylistSubmenu = false;
    },

    async createPlaylistWithTracks() {
      const tracks = this.getSelectedTracks();
      if (tracks.length === 0) return;

      const name = prompt('Enter playlist name:');
      if (!name || !name.trim()) {
        this.contextMenu = null;
        this.showPlaylistSubmenu = false;
        return;
      }

      try {
        const playlist = await api.playlists.create(name.trim());
        const trackIds = tracks.map((t) => t.id);
        await api.playlists.addTracks(playlist.id, trackIds);

        this.$store.ui.toast(
          `Created "${name.trim()}" with ${tracks.length} track${tracks.length > 1 ? 's' : ''}`,
          'success',
        );
        window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
      } catch (error) {
        console.error('Failed to create playlist:', error);
        this.$store.ui.toast('Failed to create playlist', 'error');
      }

      this.contextMenu = null;
      this.showPlaylistSubmenu = false;
    },

    async removeFromPlaylist() {
      if (!this.currentPlaylistId) return;

      const tracks = this.getSelectedTracks();
      if (tracks.length === 0) return;

      try {
        const positions = [];
        for (const track of tracks) {
          const index = this.library.filteredTracks.findIndex((t) => t.id === track.id);
          if (index >= 0) positions.push(index);
        }

        positions.sort((a, b) => b - a);

        for (const position of positions) {
          await api.playlists.removeTrack(this.currentPlaylistId, position);
        }

        this.$store.ui.toast(
          `Removed ${tracks.length} track${tracks.length > 1 ? 's' : ''} from playlist`,
          'success',
        );

        const playlist = await api.playlists.get(this.currentPlaylistId);
        const newTracks = (playlist.tracks || []).map((item) => item.track);
        this.library.tracks = newTracks;
        this.library.totalTracks = newTracks.length;
        this.library.totalDuration = newTracks.reduce((sum, t) => sum + (t.duration || 0), 0);
        this.library.applyFilters();

        this.clearSelection();
        window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
      } catch (error) {
        console.error('Failed to remove from playlist:', error);
        this.$store.ui.toast('Failed to remove from playlist', 'error');
      }

      this.contextMenu = null;
    },

    /**
     * Show track in Finder/file manager
     * @param {Object} track - Track object
     */
    async showInFinder(track) {
      try {
        const { invoke } = window.__TAURI__?.core ?? {};
        if (invoke) {
          await invoke('show_in_folder', { path: track.path });
        } else {
          console.log('Show in folder:', track.path);
        }
      } catch (error) {
        console.error('Failed to show in folder:', error);
        this.$store.ui.toast('Failed to open folder', 'error');
      }
      this.contextMenu = null;
    },

    /**
     * Show track info modal
     * @param {Object} track - Track object
     */
    showTrackInfo(track) {
      this.$store.ui.openModal('trackInfo', track);
      this.contextMenu = null;
    },

    async removeSelected() {
      const tracks = this.getSelectedTracks();
      if (tracks.length === 0) return;

      const confirmMsg = tracks.length === 1
        ? `Remove "${tracks[0].title}" from library?`
        : `Remove ${tracks.length} tracks from library?`;

      this.contextMenu = null;

      const confirmed = await window.__TAURI__?.dialog?.confirm(confirmMsg, {
        title: 'Remove from Library',
        kind: 'warning',
      }) ?? window.confirm(confirmMsg);

      if (confirmed) {
        for (const track of tracks) {
          await this.library.remove(track.id);
        }
        this.selectedTracks.clear();
        this.$store.ui.toast(
          `Removed ${tracks.length} track${tracks.length > 1 ? 's' : ''}`,
          'success',
        );
      }
    },

    formatDuration(seconds) {
      if (!seconds) return '--:--';
      const totalSeconds = Math.floor(seconds);
      const minutes = Math.floor(totalSeconds / 60);
      const secs = totalSeconds % 60;
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    },

    formatRelativeTime(timestamp) {
      if (!timestamp) return '--';
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;

      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    },

    /**
     * Clear selection
     */
    clearSelection() {
      this.selectedTracks.clear();
      this.lastSelectedIndex = -1;
    },

    /**
     * Select all tracks
     */
    selectAll() {
      this.library.filteredTracks.forEach((t) => this.selectedTracks.add(t.id));
    },

    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} event
     */
    handleKeydown(event) {
      // Cmd/Ctrl+A: Select all
      if ((event.metaKey || event.ctrlKey) && event.key === 'a') {
        event.preventDefault();
        this.selectAll();
      }

      // Escape: Clear selection
      if (event.key === 'Escape') {
        this.clearSelection();
      }

      // Enter: Play selected
      if (event.key === 'Enter' && this.selectedTracks.size > 0) {
        this.playSelected();
      }

      // Delete/Backspace: Remove selected
      if ((event.key === 'Delete' || event.key === 'Backspace') && this.selectedTracks.size > 0) {
        event.preventDefault();
        this.removeSelected();
      }
    },

    isInPlaylistView() {
      return this.currentPlaylistId !== null;
    },

    startPlaylistDrag(index, event) {
      if (!this.isInPlaylistView()) return;
      event.preventDefault();
      this.draggingIndex = index;
      this.dragOverIndex = null;

      const onMove = (e) => {
        const y = e.clientY || e.touches?.[0]?.clientY;
        if (y === undefined) return;
        this.updatePlaylistDragTarget(y);
      };

      const onEnd = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onEnd);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', onEnd);
        this.finishPlaylistDrag();
      };

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onEnd);
      document.addEventListener('touchmove', onMove, { passive: true });
      document.addEventListener('touchend', onEnd);
    },

    updatePlaylistDragTarget(y) {
      const rows = document.querySelectorAll('[data-track-id]');
      let newOverIdx = null;

      for (let i = 0; i < rows.length; i++) {
        if (i === this.draggingIndex) continue;
        const rect = rows[i].getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        if (y < midY) {
          newOverIdx = i;
          break;
        }
      }

      if (newOverIdx === null) {
        newOverIdx = this.library.filteredTracks.length;
      }

      if (newOverIdx > this.draggingIndex) {
        newOverIdx = Math.min(newOverIdx, this.library.filteredTracks.length);
      }

      this.dragOverIndex = newOverIdx;
    },

    async finishPlaylistDrag() {
      if (
        this.draggingIndex !== null && this.dragOverIndex !== null &&
        this.draggingIndex !== this.dragOverIndex
      ) {
        let toPosition = this.dragOverIndex;
        if (this.draggingIndex < toPosition) {
          toPosition--;
        }

        if (this.draggingIndex !== toPosition) {
          try {
            await api.playlists.reorder(this.currentPlaylistId, this.draggingIndex, toPosition);

            const playlist = await api.playlists.get(this.currentPlaylistId);
            const tracks = (playlist.tracks || []).map((item) => item.track);
            this.library.tracks = tracks;
            this.library.applyFilters();
          } catch (error) {
            console.error('Failed to reorder playlist:', error);
            this.$store.ui.toast('Failed to reorder tracks', 'error');
          }
        }
      }

      this.draggingIndex = null;
      this.dragOverIndex = null;
    },

    isDraggingTrack(index) {
      return this.draggingIndex === index;
    },

    getDragOverClass(index) {
      if (this.draggingIndex === null || this.dragOverIndex === null) return '';
      if (index === this.draggingIndex) return '';

      if (this.draggingIndex < this.dragOverIndex) {
        if (index > this.draggingIndex && index < this.dragOverIndex) {
          return 'translate-y-[-100%]';
        }
      } else {
        if (index >= this.dragOverIndex && index < this.draggingIndex) {
          return 'translate-y-[100%]';
        }
      }
      return '';
    },
  }));
}

export default createLibraryBrowser;
