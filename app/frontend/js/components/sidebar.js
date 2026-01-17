import { api } from '../api.js';

export function createSidebar(Alpine) {
  Alpine.data('sidebar', () => ({
    activeSection: Alpine.$persist('all').as('mt:sidebar:activeSection'),
    playlists: [],
    isCollapsed: Alpine.$persist(false).as('mt:sidebar:isCollapsed'),
    
    editingPlaylist: null,
    editingName: '',
    editingIsNew: false,
    dragOverPlaylistId: null,
    
    reorderDraggingIndex: null,
    reorderDragOverIndex: null,
    
    selectedPlaylistIds: new Set(),
    selectionAnchorIndex: null,
    
    sections: [
      { id: 'all', label: 'Music', icon: 'music' },
      { id: 'nowPlaying', label: 'Now Playing', icon: 'speaker' },
      { id: 'liked', label: 'Liked Songs', icon: 'heart' },
      { id: 'recent', label: 'Recently Played', icon: 'clock' },
      { id: 'added', label: 'Recently Added', icon: 'sparkles' },
      { id: 'top25', label: 'Top 25', icon: 'fire' },
    ],
    
    init() {
      this._migrateOldStorage();
      this.loadPlaylists();
      this.loadSection(this.activeSection);
    },
    
    _migrateOldStorage() {
      const oldData = localStorage.getItem('mt:sidebar');
      if (oldData) {
        try {
          const data = JSON.parse(oldData);
          if (data.activeSection) this.activeSection = data.activeSection;
          if (data.isCollapsed !== undefined) this.isCollapsed = data.isCollapsed;
          localStorage.removeItem('mt:sidebar');
        } catch (e) {
          localStorage.removeItem('mt:sidebar');
        }
      }
    },
    
    get library() {
      return this.$store.library;
    },
    
    get ui() {
      return this.$store.ui;
    },
    
    async loadSection(sectionId) {
      this.activeSection = sectionId;
      
      this.ui.setView('library');
      this.library.setSection(sectionId);
      
      switch (sectionId) {
        case 'all':
          this.library.searchQuery = '';
          this.library.sortBy = 'artist';
          this.library.sortOrder = 'asc';
          await this.library.load();
          break;
        case 'nowPlaying':
          this.ui.setView('nowPlaying');
          return;
        case 'liked':
          this.library.searchQuery = '';
          this.library.sortBy = 'artist';
          this.library.sortOrder = 'asc';
          await this.library.loadFavorites();
          break;
        case 'recent':
          this.library.searchQuery = '';
          this.library.sortBy = 'lastPlayed';
          this.library.sortOrder = 'desc';
          await this.library.loadRecentlyPlayed(14);
          break;
        case 'added':
          this.library.searchQuery = '';
          this.library.sortBy = 'dateAdded';
          this.library.sortOrder = 'desc';
          await this.library.loadRecentlyAdded(14);
          break;
        case 'top25':
          this.library.searchQuery = '';
          this.library.sortBy = 'playCount';
          this.library.sortOrder = 'desc';
          await this.library.loadTop25();
          break;
      }
    },
    
    async loadPlaylists() {
      try {
        const playlists = await api.playlists.getAll();
        this.playlists = playlists.map(p => ({
          id: `playlist-${p.id}`,
          playlistId: p.id,
          name: p.name,
        }));
      } catch (error) {
        console.error('Failed to load playlists:', error);
        this.playlists = [];
      }
    },
    
    async loadPlaylist(sectionId) {
      this.activeSection = sectionId;
      this.ui.setView('library');
      this.library.setSection(sectionId);
      
      const playlistId = parseInt(sectionId.replace('playlist-', ''), 10);
      if (isNaN(playlistId)) {
        this.ui.toast('Invalid playlist', 'error');
        return;
      }
      
      this.library.searchQuery = '';
      this.library.sortBy = 'title';
      this.library.sortOrder = 'asc';
      await this.library.loadPlaylist(playlistId);
    },
    
    handlePlaylistClick(event, playlist, index) {
      const isMeta = event.metaKey || event.ctrlKey;
      const isShift = event.shiftKey;
      
      if (isMeta) {
        if (this.selectedPlaylistIds.has(playlist.playlistId)) {
          this.selectedPlaylistIds.delete(playlist.playlistId);
        } else {
          this.selectedPlaylistIds.add(playlist.playlistId);
        }
        this.selectionAnchorIndex = index;
      } else if (isShift && this.selectionAnchorIndex !== null) {
        const start = Math.min(this.selectionAnchorIndex, index);
        const end = Math.max(this.selectionAnchorIndex, index);
        this.selectedPlaylistIds.clear();
        for (let i = start; i <= end; i++) {
          this.selectedPlaylistIds.add(this.playlists[i].playlistId);
        }
      } else {
        this.selectedPlaylistIds.clear();
        this.selectionAnchorIndex = index;
        this.loadPlaylist(playlist.id);
      }
    },
    
    isPlaylistSelected(playlistId) {
      return this.selectedPlaylistIds.has(playlistId);
    },
    
    clearPlaylistSelection() {
      this.selectedPlaylistIds.clear();
      this.selectionAnchorIndex = null;
    },
    
    async createPlaylist() {
      try {
        const { name: uniqueName } = await api.playlists.generateName();
        const playlist = await api.playlists.create(uniqueName);
        await this.loadPlaylists();
        
        // Notify other components (e.g., context menu) that playlists changed
        window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
        
        const newPlaylist = this.playlists.find(p => p.playlistId === playlist.id);
        if (newPlaylist) {
          this.startInlineRename(newPlaylist, true);
        }
      } catch (error) {
        console.error('Failed to create playlist:', error);
        this.ui.toast('Failed to create playlist', 'error');
      }
    },
    
    startInlineRename(playlist, isNew = false) {
      this.editingPlaylist = playlist;
      this.editingName = playlist.name;
      this.editingIsNew = isNew;
      this.$nextTick(() => {
        const input = document.querySelector('[data-testid="playlist-rename-input"]');
        if (input) {
          input.focus();
          input.select();
        }
      });
    },
    
    async commitInlineRename() {
      if (!this.editingPlaylist) return;
      
      const newName = this.editingName.trim();
      if (!newName) {
        if (this.editingIsNew) {
          this.cancelInlineRename();
        } else {
          this.editingName = this.editingPlaylist.name;
        }
        return;
      }
      
      if (newName === this.editingPlaylist.name) {
        const wasNew = this.editingIsNew;
        const playlistId = this.editingPlaylist.playlistId;
        this.editingPlaylist = null;
        if (wasNew) {
          this.loadPlaylist(`playlist-${playlistId}`);
        }
        return;
      }
      
      try {
        await api.playlists.rename(this.editingPlaylist.playlistId, newName);
        const wasNew = this.editingIsNew;
        const playlistId = this.editingPlaylist.playlistId;
        this.editingPlaylist = null;
        await this.loadPlaylists();
        
        if (wasNew) {
          this.loadPlaylist(`playlist-${playlistId}`);
        }
      } catch (error) {
        console.error('Failed to rename playlist:', error);
        if (error.message?.includes('UNIQUE constraint') || error.message?.includes('already exists')) {
          this.ui.toast('A playlist with that name already exists', 'error');
        } else {
          this.ui.toast('Failed to rename playlist', 'error');
          this.editingPlaylist = null;
        }
      }
    },
    
    async cancelInlineRename() {
      if (this.editingIsNew && this.editingPlaylist) {
        try {
          await api.playlists.delete(this.editingPlaylist.playlistId);
          await this.loadPlaylists();
        } catch (error) {
          console.error('Failed to delete cancelled playlist:', error);
        }
      }
      this.editingPlaylist = null;
      this.editingName = '';
      this.editingIsNew = false;
    },
    
    handleRenameKeydown(event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        this.commitInlineRename();
      } else if (event.key === 'Escape') {
        event.preventDefault();
        this.cancelInlineRename();
      }
    },
    
    handlePlaylistDragOver(event, playlist) {
      if (this.reorderDraggingIndex !== null) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
      this.dragOverPlaylistId = playlist.playlistId;
    },
    
    handlePlaylistDragLeave() {
      this.dragOverPlaylistId = null;
    },
    
    async handlePlaylistDrop(event, playlist) {
      if (this.reorderDraggingIndex !== null) return;
      event.preventDefault();
      this.dragOverPlaylistId = null;
      
      const trackIdsJson = event.dataTransfer.getData('application/json');
      if (!trackIdsJson) return;
      
      try {
        const trackIds = JSON.parse(trackIdsJson);
        if (!Array.isArray(trackIds) || trackIds.length === 0) return;
        
        const result = await api.playlists.addTracks(playlist.playlistId, trackIds);
        if (result.added > 0) {
          this.ui.toast(`Added ${result.added} track${result.added > 1 ? 's' : ''} to "${playlist.name}"`, 'success');
        } else {
          this.ui.toast(`Track${trackIds.length > 1 ? 's' : ''} already in "${playlist.name}"`, 'info');
        }
        window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
      } catch (error) {
        console.error('Failed to add tracks to playlist:', error);
        this.ui.toast('Failed to add tracks to playlist', 'error');
      }
    },
    
    isPlaylistDragOver(playlistId) {
      return this.dragOverPlaylistId === playlistId;
    },
    
    startPlaylistReorder(index, event) {
      event.preventDefault();
      this.reorderDraggingIndex = index;
      this.reorderDragOverIndex = null;

      const onMove = (e) => {
        const y = e.clientY || e.touches?.[0]?.clientY;
        if (y === undefined) return;
        this.updatePlaylistReorderTarget(y);
      };

      const onEnd = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onEnd);
        document.removeEventListener('touchmove', onMove);
        document.removeEventListener('touchend', onEnd);
        this.finishPlaylistReorder();
      };

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onEnd);
      document.addEventListener('touchmove', onMove, { passive: true });
      document.addEventListener('touchend', onEnd);
    },

    updatePlaylistReorderTarget(y) {
      const buttons = document.querySelectorAll('[data-playlist-reorder-index]');
      let newOverIdx = null;

      for (let i = 0; i < buttons.length; i++) {
        if (i === this.reorderDraggingIndex) continue;
        const rect = buttons[i].getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        if (y < midY) {
          newOverIdx = i;
          break;
        }
      }

      if (newOverIdx === null) {
        newOverIdx = this.playlists.length;
      }

      if (newOverIdx > this.reorderDraggingIndex) {
        newOverIdx = Math.min(newOverIdx, this.playlists.length);
      }

      this.reorderDragOverIndex = newOverIdx;
    },

    async finishPlaylistReorder() {
      if (
        this.reorderDraggingIndex !== null && this.reorderDragOverIndex !== null &&
        this.reorderDraggingIndex !== this.reorderDragOverIndex
      ) {
        let toPosition = this.reorderDragOverIndex;
        if (this.reorderDraggingIndex < toPosition) {
          toPosition--;
        }

        if (this.reorderDraggingIndex !== toPosition) {
          try {
            await api.playlists.reorderPlaylists(this.reorderDraggingIndex, toPosition);
            await this.loadPlaylists();
          } catch (error) {
            console.error('Failed to reorder playlists:', error);
            this.ui.toast('Failed to reorder playlists', 'error');
          }
        }
      }

      this.reorderDraggingIndex = null;
      this.reorderDragOverIndex = null;
    },
    
    getPlaylistReorderClass(index) {
      if (this.reorderDraggingIndex === null || this.reorderDragOverIndex === null) return '';
      if (index === this.reorderDraggingIndex) return '';
      
      if (this.reorderDraggingIndex < this.reorderDragOverIndex) {
        if (index > this.reorderDraggingIndex && index < this.reorderDragOverIndex) {
          return 'playlist-shift-up';
        }
      } else {
        if (index >= this.reorderDragOverIndex && index < this.reorderDraggingIndex) {
          return 'playlist-shift-down';
        }
      }
      return '';
    },
    
    isPlaylistDragging(index) {
      return this.reorderDraggingIndex === index;
    },
    
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed;
    },
    
    isActive(sectionId) {
      return this.activeSection === sectionId;
    },
    
    contextMenuPlaylist: null,
    contextMenuX: 0,
    contextMenuY: 0,
    
    showPlaylistContextMenu(event, playlist) {
      event.preventDefault();
      this.contextMenuPlaylist = playlist;
      this.contextMenuX = event.clientX;
      this.contextMenuY = event.clientY;
    },
    
    hidePlaylistContextMenu() {
      this.contextMenuPlaylist = null;
    },
    
    async renamePlaylist() {
      if (!this.contextMenuPlaylist) return;
      
      const playlist = this.contextMenuPlaylist;
      this.hidePlaylistContextMenu();
      this.startInlineRename(playlist, false);
    },
    
    async deletePlaylist() {
      if (!this.contextMenuPlaylist) return;
      
      const playlistName = this.contextMenuPlaylist.name;
      const playlistId = this.contextMenuPlaylist.playlistId;
      const sectionId = this.contextMenuPlaylist.id;
      
      let confirmed = false;
      if (window.__TAURI__?.dialog?.confirm) {
        confirmed = await window.__TAURI__.dialog.confirm(
          `Delete playlist "${playlistName}"?`,
          { title: 'Delete Playlist', kind: 'warning' }
        );
      } else {
        confirmed = confirm(`Delete playlist "${playlistName}"?`);
      }
      
      if (!confirmed) {
        this.hidePlaylistContextMenu();
        return;
      }
      
      try {
        await api.playlists.delete(playlistId);
        this.ui.toast(`Deleted "${playlistName}"`, 'success');
        await this.loadPlaylists();
        window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
        if (this.activeSection === sectionId) {
          this.loadSection('all');
        }
      } catch (error) {
        console.error('Failed to delete playlist:', error);
        this.ui.toast('Failed to delete playlist', 'error');
      }
      this.hidePlaylistContextMenu();
    },
    
    handlePlaylistKeydown(event) {
      if (this.editingPlaylist) return;
      
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (this.selectedPlaylistIds.size > 0) {
          event.preventDefault();
          this.deleteSelectedPlaylists();
        }
      }
    },
    
    async deleteSelectedPlaylists() {
      if (this.selectedPlaylistIds.size === 0) return;
      
      const selectedPlaylists = this.playlists.filter(p => this.selectedPlaylistIds.has(p.playlistId));
      const names = selectedPlaylists.map(p => p.name);
      const message = selectedPlaylists.length === 1
        ? `Delete playlist "${names[0]}"?`
        : `Delete ${selectedPlaylists.length} playlists?\n\n${names.join('\n')}`;
      
      let confirmed = false;
      if (window.__TAURI__?.dialog?.confirm) {
        confirmed = await window.__TAURI__.dialog.confirm(message, {
          title: selectedPlaylists.length === 1 ? 'Delete Playlist' : 'Delete Playlists',
          kind: 'warning'
        });
      } else {
        confirmed = confirm(message);
      }
      
      if (!confirmed) return;
      
      const deletedIds = new Set();
      const errors = [];
      
      for (const playlist of selectedPlaylists) {
        try {
          await api.playlists.delete(playlist.playlistId);
          deletedIds.add(playlist.playlistId);
        } catch (error) {
          console.error(`Failed to delete playlist ${playlist.name}:`, error);
          errors.push(playlist.name);
        }
      }
      
      if (deletedIds.size > 0) {
        const msg = deletedIds.size === 1
          ? `Deleted "${selectedPlaylists.find(p => deletedIds.has(p.playlistId)).name}"`
          : `Deleted ${deletedIds.size} playlists`;
        this.ui.toast(msg, 'success');
      }
      
      if (errors.length > 0) {
        this.ui.toast(`Failed to delete: ${errors.join(', ')}`, 'error');
      }
      
      await this.loadPlaylists();
      window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
      
      if (deletedIds.has(parseInt(this.activeSection.replace('playlist-', ''), 10))) {
        this.loadSection('all');
      }
      
      this.clearPlaylistSelection();
    },
  }));
}

export default createSidebar;
