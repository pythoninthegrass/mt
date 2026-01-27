---
id: task-114
title: 'P3: Build Alpine.js player controls component'
status: Done
assignee: []
created_date: '2026-01-12 06:35'
updated_date: '2026-01-26 01:53'
labels:
  - frontend
  - alpine
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-115
  - task-117
priority: high
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the player controls UI component using Alpine.js and Basecoat.

**Features:**
- Play/pause button
- Previous/next track buttons
- Progress bar with seek (click to seek)
- Volume slider
- Loop mode toggle (off, track, queue)
- Shuffle toggle
- Current track info display (title, artist, album art)

**Implementation:**
- Alpine.js store for player state
- Communicate with Rust via Tauri invoke for playback control
- Progress updates via Tauri events from Rust audio engine
- Use Basecoat UI components (static file approach)

**Basecoat Setup (shared with task-112, task-113):**
```html
<link href="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/basecoat.cdn.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/js/all.min.js" defer></script>
```

**Basecoat Components to Use:**
- `.btn` - Transport buttons (play/pause, prev, next)
- `.btn-icon` - Icon-only buttons for controls
- `.slider` - Progress bar and volume control (custom or native range input)
- `.popover` - Volume popup (optional)

**Player Controls HTML Structure:**
```html
<div class="player-controls">
  <div class="now-playing">
    <img class="album-art" src="..." alt="Album art" />
    <div class="track-info">
      <span class="title">Track Title</span>
      <span class="artist">Artist Name</span>
    </div>
  </div>
  
  <div class="transport">
    <button class="btn btn-icon" @click="shuffle()">
      <i class="icon-shuffle"></i>
    </button>
    <button class="btn btn-icon" @click="previous()">
      <i class="icon-skip-back"></i>
    </button>
    <button class="btn btn-icon btn-lg" @click="playPause()">
      <i x-show="!playing" class="icon-play"></i>
      <i x-show="playing" class="icon-pause"></i>
    </button>
    <button class="btn btn-icon" @click="next()">
      <i class="icon-skip-forward"></i>
    </button>
    <button class="btn btn-icon" @click="toggleLoop()">
      <i class="icon-repeat"></i>
    </button>
  </div>
  
  <div class="progress-bar">
    <span class="time-current">1:23</span>
    <input type="range" min="0" :max="duration" x-model="position" @change="seek($event.target.value)" />
    <span class="time-total">3:45</span>
  </div>
  
  <div class="volume">
    <button class="btn btn-icon" @click="toggleMute()">
      <i class="icon-volume"></i>
    </button>
    <input type="range" min="0" max="100" x-model="volume" @input="setVolume($event.target.value)" />
  </div>
</div>
```

**Alpine.js Store Integration:**
```javascript
Alpine.store('player', {
  playing: false,
  position: 0,
  duration: 0,
  volume: 100,
  loop: 'off', // 'off', 'track', 'queue'
  shuffle: false,
  currentTrack: null,
  
  async playPause() {
    await invoke('play_pause');
  },
  async seek(position) {
    await invoke('seek', { position_ms: position });
  }
});
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Transport controls (play/pause/prev/next) work
- [ ] #2 Progress bar shows position and allows seeking
- [ ] #3 Volume control works
- [ ] #4 Loop and shuffle toggles work
<!-- AC:END -->
