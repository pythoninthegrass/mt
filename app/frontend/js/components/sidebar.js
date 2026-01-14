/**
 * Sidebar Navigation Component
 * 
 * Left sidebar with library sections and playlists navigation.
 */

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
          await this.library.load();
          break;
        case 'added':
          this.library.searchQuery = '';
          this.library.sortBy = 'dateAdded';
          this.library.sortOrder = 'desc';
          await this.library.load();
          break;
        case 'top25':
          this.library.searchQuery = '';
          this.library.sortBy = 'playCount';
          this.library.sortOrder = 'desc';
          await this.library.load();
          break;
      }
    },
    
    async loadPlaylists() {
      // TODO: Load playlists from backend
      this.playlists = [
        { id: 'playlist-1', name: 'Chill Vibes' },
        { id: 'playlist-2', name: 'Workout Mix' },
        { id: 'playlist-3', name: 'Focus Music' },
      ];
    },
    
    async loadPlaylist(playlistId) {
      this.activeSection = playlistId;
      this.save();
      this.ui.setView('library');
      // TODO: Load playlist tracks
      this.ui.toast('Playlists coming soon!', 'info');
    },
    
    createPlaylist() {
      this.ui.openModal('createPlaylist');
    },
    
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed;
      this.save();
    },
    
    isActive(sectionId) {
      return this.activeSection === sectionId;
    },
  }));
}

export default createSidebar;
