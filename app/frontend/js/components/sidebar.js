import { api } from '../api.js';

export function createSidebar(Alpine) {
  Alpine.data('sidebar', () => ({
    activeSection: 'all',
    playlists: [],
    isCollapsed: false,
    
    editingPlaylist: null,
    editingName: '',
    editingIsNew: false,
    dragOverPlaylistId: null,
    
    sections: [
      { id: 'all', label: 'Music', icon: 'music' },
      { id: 'nowPlaying', label: 'Now Playing', icon: 'speaker' },
      { id: 'liked', label: 'Liked Songs', icon: 'heart' },
      { id: 'recent', label: 'Recently Played', icon: 'clock' },
      { id: 'added', label: 'Recently Added', icon: 'sparkles' },
      { id: 'top25', label: 'Top 25', icon: 'fire' },
    ],
    
    init() {
      const saved = localStorage.getItem('mt:sidebar');
      if (saved) {
        try {
          const data = JSON.parse(saved);
          this.activeSection = data.activeSection || 'all';
          this.isCollapsed = data.isCollapsed || false;
        } catch (e) {
          // ignore
        }
      }
      this.loadPlaylists();
      this.loadSection(this.activeSection);
    },
    
    get library() {
      return this.$store.library;
    },
    
    get ui() {
      return this.$store.ui;
    },
    
    save() {
      localStorage.setItem('mt:sidebar', JSON.stringify({
        activeSection: this.activeSection,
        isCollapsed: this.isCollapsed,
      }));
    },
    
    async loadSection(sectionId) {
      this.activeSection = sectionId;
      this.save();
      
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
      this.save();
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
    
    async createPlaylist() {
      try {
        const { name: uniqueName } = await api.playlists.generateName();
        const playlist = await api.playlists.create(uniqueName);
        await this.loadPlaylists();
        
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
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
      this.dragOverPlaylistId = playlist.playlistId;
    },
    
    handlePlaylistDragLeave() {
      this.dragOverPlaylistId = null;
    },
    
    async handlePlaylistDrop(event, playlist) {
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
    
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed;
      this.save();
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
      
      const confirmed = confirm(`Delete playlist "${this.contextMenuPlaylist.name}"?`);
      if (!confirmed) {
        this.hidePlaylistContextMenu();
        return;
      }
      
      try {
        await api.playlists.delete(this.contextMenuPlaylist.playlistId);
        this.ui.toast(`Deleted "${this.contextMenuPlaylist.name}"`, 'success');
        await this.loadPlaylists();
        if (this.activeSection === this.contextMenuPlaylist.id) {
          this.loadSection('all');
        }
      } catch (error) {
        console.error('Failed to delete playlist:', error);
        this.ui.toast('Failed to delete playlist', 'error');
      }
      this.hidePlaylistContextMenu();
    },
  }));
}

export default createSidebar;
