---
id: task-115
title: 'P4: Implement Rust audio engine with symphonia + rodio'
status: Done
assignee: []
created_date: '2026-01-12 06:36'
updated_date: '2026-01-26 01:29'
labels:
  - rust
  - audio
  - phase-4
milestone: Tauri Migration
dependencies: []
priority: high
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build the native Rust audio playback engine to replace VLC.

**Features:**
- Decode audio files (MP3, FLAC, M4A/AAC, OGG, WAV)
- Play/pause/stop/seek operations
- Volume control
- Track position reporting
- Gapless playback (stretch goal)

**Implementation:**
- Use symphonia for decoding
- Use rodio for audio output
- Expose Tauri commands: `play_track`, `pause`, `resume`, `stop`, `seek`, `set_volume`
- Emit Tauri events: `playback-progress`, `track-ended`, `playback-error`
- Store audio state in Rust managed state

**Reference:**
- See docs/tauri-architecture.md for design
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Can play MP3, FLAC, M4A files
- [ ] #2 Play/pause/seek commands work
- [ ] #3 Progress events emit to frontend
- [ ] #4 Volume control works
- [ ] #5 Track-ended event fires correctly
<!-- AC:END -->
