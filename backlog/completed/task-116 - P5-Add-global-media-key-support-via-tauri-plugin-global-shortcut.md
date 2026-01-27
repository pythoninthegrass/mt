---
id: task-116
title: 'P5: Add global media key support via tauri-plugin-global-shortcut'
status: Done
assignee: []
created_date: '2026-01-12 06:36'
updated_date: '2026-01-27 03:03'
labels:
  - rust
  - platform
  - phase-5
milestone: Tauri Migration
dependencies: []
priority: medium
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement system-wide media key handling for play/pause, next, previous.

**Features:**
- Respond to media keys even when app is not focused
- Play/Pause key toggles playback
- Next/Previous keys change tracks
- Works on macOS (primary), Linux, Windows

**Implementation:**
- Use tauri-plugin-global-shortcut (already added to Cargo.toml)
- Register shortcuts in Rust setup
- Connect to audio engine commands
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Media keys work when app is in background
- [ ] #2 Play/Pause toggles correctly
- [ ] #3 Next/Previous change tracks
- [ ] #4 Works on macOS
<!-- AC:END -->
