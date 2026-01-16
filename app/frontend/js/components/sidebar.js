import { api } from '../api.js';

export function createSidebar(Alpine) {
  Alpine.data('sidebar', () => ({
    activeSection: 'all',
    playlists: [],
    isCollapsed: false,
    
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
      const name = prompt('Enter playlist name:');
      if (!name || !name.trim()) {
        return;
      }
      
      try {
        const playlist = await api.playlists.create(name.trim());
        this.ui.toast(`Created playlist "${playlist.name}"`, 'success');
        await this.loadPlaylists();
        this.loadPlaylist(`playlist-${playlist.id}`);
      } catch (error) {
        console.error('Failed to create playlist:', error);
        this.ui.toast('Failed to create playlist', 'error');
      }
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
      
      const newName = prompt('Enter new name:', this.contextMenuPlaylist.name);
      if (!newName || !newName.trim() || newName.trim() === this.contextMenuPlaylist.name) {
        this.hidePlaylistContextMenu();
        return;
      }
      
      try {
        await api.playlists.rename(this.contextMenuPlaylist.playlistId, newName.trim());
        this.ui.toast(`Renamed to "${newName.trim()}"`, 'success');
        await this.loadPlaylists();
      } catch (error) {
        console.error('Failed to rename playlist:', error);
        this.ui.toast('Failed to rename playlist', 'error');
      }
      this.hidePlaylistContextMenu();
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
