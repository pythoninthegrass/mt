---
id: task-094
title: 'P2: Implement Rust audio playback engine with symphonia'
status: To Do
assignee: []
created_date: '2026-01-12 04:07'
labels:
  - rust
  - audio
  - phase-2
milestone: Tauri Migration
dependencies:
  - task-090
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build the core audio playback engine in Rust using symphonia for decoding and rodio/cpal for output.

**Codec support (symphonia):**
- FLAC
- MP3
- AAC/M4A
- OGG/Vorbis
- WAV

**Features:**
- Load and play audio file by path
- Play/pause/stop controls
- Seek to position
- Volume control
- Progress reporting (current position, duration)
- End-of-track event emission

**Architecture:**
```rust
// src-tauri/src/audio/mod.rs
pub struct AudioEngine {
    // symphonia decoder
    // rodio sink
    // state (playing, paused, stopped)
    // current file info
}

impl AudioEngine {
    pub fn load(&mut self, path: &str) -> Result<TrackInfo>;
    pub fn play(&mut self);
    pub fn pause(&mut self);
    pub fn stop(&mut self);
    pub fn seek(&mut self, position_ms: u64);
    pub fn set_volume(&mut self, volume: f32);
    pub fn get_progress(&self) -> Progress;
}
```

**Platform targets:**
- macOS (primary)
- Linux (secondary)
- Windows (tertiary)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Can load and decode FLAC, MP3, M4A files
- [ ] #2 Play/pause/stop works correctly
- [ ] #3 Seek to arbitrary position works
- [ ] #4 Volume control works (0.0-1.0 range)
- [ ] #5 Progress reporting returns current_ms and duration_ms
- [ ] #6 End-of-track event fires when playback completes
- [ ] #7 Works on macOS
<!-- AC:END -->
