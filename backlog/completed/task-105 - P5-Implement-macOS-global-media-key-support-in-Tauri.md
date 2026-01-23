---
id: task-105
title: 'P5: Implement macOS global media key support in Tauri'
status: Done
assignee: []
created_date: '2026-01-12 04:09'
updated_date: '2026-01-14 08:24'
labels:
  - rust
  - macos
  - phase-5
milestone: Tauri Migration
dependencies:
  - task-095
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add support for macOS media keys (play/pause, next, previous) in the Tauri app.

**Options:**
1. **Tauri plugin**: Use `tauri-plugin-global-shortcut` for basic shortcuts
2. **Native Rust**: Use `objc` crate to register for media key events via NSEvent
3. **MPNowPlayingInfoCenter**: Integrate with macOS Now Playing widget

**Recommended approach (MPNowPlayingInfoCenter):**
```rust
// src-tauri/src/media_keys.rs
use objc::{class, msg_send, sel, sel_impl};

pub fn setup_media_keys(app: &AppHandle) {
    // Register for remote command center events
    // - Play/pause command
    // - Next track command  
    // - Previous track command
    // - Seek command
    
    // Update Now Playing info when track changes
    // - Title, artist, album
    // - Duration, elapsed time
    // - Playback state
}
```

**Benefits of MPNowPlayingInfoCenter:**
- Works with Touch Bar, AirPods, Control Center
- Shows track info in macOS Now Playing widget
- Proper system integration
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Media keys (F7/F8/F9 or Touch Bar) control playback
- [x] #2 Now Playing widget shows current track info
- [x] #3 Works with AirPods/Bluetooth headphones
- [x] #4 Playback state syncs with system
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation

### Backend (Rust)
1. Added `souvlaki` crate for cross-platform media controls (macOS MPNowPlayingInfoCenter, Linux MPRIS, Windows SMTC)
2. Created `src-tauri/src/media_keys.rs` with `MediaKeyManager` struct
3. Added Tauri commands: `media_set_metadata`, `media_set_playing`, `media_set_paused`, `media_set_stopped`
4. Media key events emitted as Tauri events: `mediakey://play`, `mediakey://pause`, `mediakey://toggle`, `mediakey://next`, `mediakey://previous`, `mediakey://stop`

### Frontend (JavaScript)
1. Player store listens for media key events and triggers corresponding actions
2. Now Playing metadata updated when track changes (title, artist, album, duration)
3. Playback state synced on play/pause/stop
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Files Modified
- `src-tauri/Cargo.toml` - Added souvlaki dependency
- `src-tauri/src/media_keys.rs` - New module for media key integration
- `src-tauri/src/lib.rs` - Integrated MediaKeyManager and added Tauri commands
- `app/frontend/js/stores/player.js` - Added media key event listeners and Now Playing updates
<!-- SECTION:NOTES:END -->
