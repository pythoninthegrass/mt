---
id: task-101
title: 'P4: Implement Alpine.js global stores for player state'
status: To Do
assignee: []
created_date: '2026-01-12 04:08'
labels:
  - frontend
  - alpinejs
  - phase-4
milestone: Tauri Migration
dependencies:
  - task-100
  - task-095
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create Alpine.js stores for managing global application state.

**Stores to implement:**

```javascript
// src/js/stores.js

// Player state (audio playback)
Alpine.store('player', {
    currentTrack: null,      // { id, title, artist, album, duration, path }
    isPlaying: false,
    progress: 0,             // 0-100
    currentTime: 0,          // ms
    duration: 0,             // ms
    volume: 100,             // 0-100
    
    async play(track) { ... },
    async pause() { ... },
    async toggle() { ... },
    async next() { ... },
    async previous() { ... },
    async seek(position) { ... },
    async setVolume(vol) { ... },
});

// Queue state
Alpine.store('queue', {
    items: [],               // Array of track objects
    currentIndex: -1,
    shuffle: false,
    loop: 'none',            // 'none', 'all', 'one'
    
    async load() { ... },
    async add(tracks) { ... },
    async remove(index) { ... },
    async clear() { ... },
    async reorder(from, to) { ... },
});

// Library state
Alpine.store('library', {
    tracks: [],
    searchQuery: '',
    sortBy: 'artist',
    loading: false,
    
    async load(query) { ... },
    async scan(path) { ... },
    async remove(trackId) { ... },
});

// UI state
Alpine.store('ui', {
    view: 'library',         // 'library', 'queue', 'nowPlaying'
    sidebarWidth: 250,
    
    setView(view) { ... },
});
```

**Integration with Tauri:**
- Use `window.__TAURI__.invoke()` for audio commands
- Use `fetch()` for Python backend API calls
- Subscribe to Tauri events for progress updates
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Player store manages playback state
- [ ] #2 Queue store syncs with backend
- [ ] #3 Library store loads and searches tracks
- [ ] #4 UI store manages view switching
- [ ] #5 Stores react to Tauri events
- [ ] #6 State persists correctly across view changes
<!-- AC:END -->
