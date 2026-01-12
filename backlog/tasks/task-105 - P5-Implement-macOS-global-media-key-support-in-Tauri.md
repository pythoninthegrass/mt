---
id: task-105
title: 'P5: Implement macOS global media key support in Tauri'
status: To Do
assignee: []
created_date: '2026-01-12 04:09'
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
- [ ] #1 Media keys (F7/F8/F9 or Touch Bar) control playback
- [ ] #2 Now Playing widget shows current track info
- [ ] #3 Works with AirPods/Bluetooth headphones
- [ ] #4 Playback state syncs with system
<!-- AC:END -->
