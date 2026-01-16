/**
 * Queue Store - manages playback queue state
 * 
 * Syncs with Python backend for persistence and
 * coordinates with player store for playback.
 */

import { api } from '../api.js';

export function createQueueStore(Alpine) {
  Alpine.store('queue', {
    // Queue items
    items: [],           // Array of track objects
    currentIndex: -1,    // Currently playing index (-1 = none)
    
    // Playback modes
    shuffle: false,
    loop: 'none',        // 'none', 'all', 'one'
    
    // Repeat-one "play once more" state
    _repeatOnePending: false,  // true = currently in second playthrough, will auto-revert
    
    // Loading state
    loading: false,
    
    // Shuffle history for proper back navigation
    _shuffleHistory: [],
    _originalOrder: [],
    
    /**
     * Initialize queue from backend
     */
    async init() {
      this._loadLoopState();
      await this.load();
    },
    
    _loadLoopState() {
      try {
        const saved = localStorage.getItem('mt:loop-state');
        if (saved) {
          const { loop, shuffle } = JSON.parse(saved);
          if (['none', 'all', 'one'].includes(loop)) {
            this.loop = loop;
          }
          if (typeof shuffle === 'boolean') {
            this.shuffle = shuffle;
          }
        }
      } catch (e) {
        // ignore
      }
    },
    
    _saveLoopState() {
      try {
        localStorage.setItem('mt:loop-state', JSON.stringify({
          loop: this.loop,
          shuffle: this.shuffle,
        }));
      } catch (e) {
        // ignore
      }
    },
    
    async load() {
      this.loading = true;
      try {
        const data = await api.queue.get();
        this.items = data.items || [];
        this.currentIndex = data.currentIndex ?? -1;
        this._originalOrder = [...this.items];
      } catch (error) {
        console.error('Failed to load queue:', error);
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * Save queue state to backend
     */
    async save() {
      try {
        await api.queue.save({
          items: this.items,
          currentIndex: this.currentIndex,
          shuffle: this.shuffle,
          loop: this.loop,
        });
      } catch (error) {
        console.error('Failed to save queue:', error);
      }
    },
    
    /**
     * Add tracks to queue
     * @param {Array|Object} tracks - Track(s) to add
     * @param {boolean} playNow - Start playing immediately
     */
    async add(tracks, playNow = false) {
      const tracksArray = Array.isArray(tracks) ? tracks : [tracks];
      const startIndex = this.items.length;
      
      this.items.push(...tracksArray);
      this._originalOrder.push(...tracksArray);
      
      await this.save();
      
      if (playNow && tracksArray.length > 0) {
        await this.playIndex(startIndex);
      }
    },
    
    /**
     * Insert tracks at specific position
     * @param {number} index - Position to insert at
     * @param {Array|Object} tracks - Track(s) to insert
     */
    async insert(index, tracks) {
      const tracksArray = Array.isArray(tracks) ? tracks : [tracks];
      this.items.splice(index, 0, ...tracksArray);
      
      // Adjust current index if needed
      if (this.currentIndex >= index) {
        this.currentIndex += tracksArray.length;
      }
      
      await this.save();
    },
    
    /**
     * Remove track at index
     * @param {number} index - Index to remove
     */
    async remove(index) {
      if (index < 0 || index >= this.items.length) return;
      
      this.items.splice(index, 1);
      
      // Adjust current index
      if (index < this.currentIndex) {
        this.currentIndex--;
      } else if (index === this.currentIndex) {
        // Currently playing track was removed
        if (this.items.length === 0) {
          this.currentIndex = -1;
          Alpine.store('player').stop();
        } else if (this.currentIndex >= this.items.length) {
          this.currentIndex = this.items.length - 1;
        }
      }
      
      await this.save();
    },
    
    /**
     * Clear entire queue
     */
    async clear() {
      this.items = [];
      this.currentIndex = -1;
      this._originalOrder = [];
      this._shuffleHistory = [];
      
      Alpine.store('player').stop();
      await this.save();
    },
    
    /**
     * Reorder track in queue (drag and drop)
     * @param {number} from - Source index
     * @param {number} to - Destination index
     */
    async reorder(from, to) {
      if (from === to) return;
      if (from < 0 || from >= this.items.length) return;
      if (to < 0 || to >= this.items.length) return;
      
      const [item] = this.items.splice(from, 1);
      this.items.splice(to, 0, item);
      
      // Adjust current index
      if (from === this.currentIndex) {
        this.currentIndex = to;
      } else if (from < this.currentIndex && to >= this.currentIndex) {
        this.currentIndex--;
      } else if (from > this.currentIndex && to <= this.currentIndex) {
        this.currentIndex++;
      }
      
      await this.save();
    },
    
    /**
     * Play track at specific index
     * @param {number} index - Index to play
     */
    async playIndex(index) {
      if (index < 0 || index >= this.items.length) return;
      
      this.currentIndex = index;
      const track = this.items[index];
      
      if (this.shuffle) {
        this._shuffleHistory.push(index);
      }
      
      await Alpine.store('player').playTrack(track);
      await this.save();
    },
    
    /**
     * Play next track in queue
     */
    async playNext() {
      if (this.items.length === 0) return;
      
      // Handle repeat-one "play once more" pattern
      if (this.loop === 'one') {
        if (this._repeatOnePending) {
          // Second playthrough complete - auto-revert to 'none'
          this._repeatOnePending = false;
          this.loop = 'none';
          this._saveLoopState();
        } else {
          // First playthrough - replay and mark pending
          this._repeatOnePending = true;
          await this.playIndex(this.currentIndex);
          return;
        }
      }
      
      let nextIndex;
      
      if (this.shuffle) {
        const available = this.items
          .map((_, i) => i)
          .filter(i => i !== this.currentIndex);
        
        if (available.length === 0) {
          if (this.loop === 'all') {
            nextIndex = Math.floor(Math.random() * this.items.length);
          } else {
            return;
          }
        } else {
          nextIndex = available[Math.floor(Math.random() * available.length)];
        }
      } else {
        nextIndex = this.currentIndex + 1;
        
        if (nextIndex >= this.items.length) {
          if (this.loop === 'all') {
            nextIndex = 0;
          } else {
            return;
          }
        }
      }
      
      await this.playIndex(nextIndex);
    },
    
    /**
     * Play previous track in queue
     */
    async playPrevious() {
      if (this.items.length === 0) return;
      
      const player = Alpine.store('player');
      
      if (player.currentTime > 3000) {
        await player.seek(0);
        return;
      }
      
      let prevIndex;
      
      if (this.shuffle && this._shuffleHistory.length > 1) {
        this._shuffleHistory.pop();
        prevIndex = this._shuffleHistory[this._shuffleHistory.length - 1];
      } else {
        prevIndex = this.currentIndex - 1;
        
        if (prevIndex < 0) {
          if (this.loop === 'all') {
            prevIndex = this.items.length - 1;
          } else {
            prevIndex = 0;
          }
        }
      }
      
      await this.playIndex(prevIndex);
    },
    
    /**
     * Manual skip to next track (user-initiated)
     * If in repeat-one mode, reverts to 'all' and skips
     */
    async skipNext() {
      if (this.loop === 'one') {
        this.loop = 'all';
        this._repeatOnePending = false;
        this._saveLoopState();
      }
      await this._doSkipNext();
    },
    
    /**
     * Manual skip to previous track (user-initiated)
     * If in repeat-one mode, reverts to 'all' and skips
     */
    async skipPrevious() {
      if (this.loop === 'one') {
        this.loop = 'all';
        this._repeatOnePending = false;
        this._saveLoopState();
      }
      await this.playPrevious();
    },
    
    async _doSkipNext() {
      if (this.items.length === 0) return;
      
      let nextIndex;
      
      if (this.shuffle) {
        const available = this.items
          .map((_, i) => i)
          .filter(i => i !== this.currentIndex);
        
        if (available.length === 0) {
          nextIndex = Math.floor(Math.random() * this.items.length);
        } else {
          nextIndex = available[Math.floor(Math.random() * available.length)];
        }
      } else {
        nextIndex = this.currentIndex + 1;
        if (nextIndex >= this.items.length) {
          nextIndex = 0;
        }
      }
      
      await this.playIndex(nextIndex);
    },
    
    /**
     * Toggle shuffle mode
     */
    async toggleShuffle() {
      this.shuffle = !this.shuffle;
      
      if (this.shuffle) {
        this._originalOrder = [...this.items];
        this._shuffleHistory = [this.currentIndex];
      } else {
        const currentTrack = this.items[this.currentIndex];
        this.items = [...this._originalOrder];
        this.currentIndex = this.items.findIndex(t => t.id === currentTrack?.id);
        this._shuffleHistory = [];
      }
      
      this._saveLoopState();
      await this.save();
    },
    
    async shuffleQueue() {
      if (this.items.length < 2) return;
      
      const currentTrack = this.items[this.currentIndex];
      const otherTracks = this.items.filter((_, i) => i !== this.currentIndex);
      
      for (let i = otherTracks.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [otherTracks[i], otherTracks[j]] = [otherTracks[j], otherTracks[i]];
      }
      
      if (currentTrack) {
        this.items = [currentTrack, ...otherTracks];
        this.currentIndex = 0;
      } else {
        this.items = otherTracks;
      }
      
      this._originalOrder = [...this.items];
      await this.save();
    },
    
    async cycleLoop() {
      const modes = ['none', 'all', 'one'];
      const currentIdx = modes.indexOf(this.loop);
      this.loop = modes[(currentIdx + 1) % modes.length];
      this._repeatOnePending = false;
      this._saveLoopState();
      await this.save();
    },
    
    /**
     * Set loop mode directly
     * @param {string} mode - 'none', 'all', or 'one'
     */
    async setLoop(mode) {
      if (['none', 'all', 'one'].includes(mode)) {
        this.loop = mode;
        this._repeatOnePending = false;
        this._saveLoopState();
        await this.save();
      }
    },
    
    /**
     * Get tracks (alias for items, used by UI templates)
     */
    get tracks() {
      return this.items;
    },
    
    /**
     * Get current track
     */
    get currentTrack() {
      return this.currentIndex >= 0 ? this.items[this.currentIndex] : null;
    },
    
    /**
     * Check if there's a next track
     */
    get hasNext() {
      if (this.items.length === 0) return false;
      if (this.loop !== 'none') return true;
      return this.currentIndex < this.items.length - 1;
    },
    
    /**
     * Check if there's a previous track
     */
    get hasPrevious() {
      if (this.items.length === 0) return false;
      if (this.loop !== 'none') return true;
      return this.currentIndex > 0;
    },
    
    /**
     * Get loop icon for UI
     */
    get loopIcon() {
      switch (this.loop) {
        case 'one': return 'repeat-1';
        case 'all': return 'repeat';
        default: return 'repeat';
      }
    },
  });
}
