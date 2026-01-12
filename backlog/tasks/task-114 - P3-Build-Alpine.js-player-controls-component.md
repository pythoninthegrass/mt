---
id: task-114
title: 'P3: Build Alpine.js player controls component'
status: To Do
assignee: []
created_date: '2026-01-12 06:35'
labels:
  - frontend
  - alpine
  - phase-3
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the player controls UI component using Alpine.js.

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
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Transport controls (play/pause/prev/next) work
- [ ] #2 Progress bar shows position and allows seeking
- [ ] #3 Volume control works
- [ ] #4 Loop and shuffle toggles work
<!-- AC:END -->
