---
id: task-095
title: 'P2: Expose audio engine via Tauri commands'
status: To Do
assignee: []
created_date: '2026-01-12 04:07'
labels:
  - rust
  - tauri
  - phase-2
milestone: Tauri Migration
dependencies:
  - task-093
  - task-094
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create Tauri invoke commands to control the audio engine from the frontend.

**Commands to implement:**
```rust
#[tauri::command]
fn audio_load(path: String) -> Result<TrackInfo, String>;

#[tauri::command]
fn audio_play() -> Result<(), String>;

#[tauri::command]
fn audio_pause() -> Result<(), String>;

#[tauri::command]
fn audio_stop() -> Result<(), String>;

#[tauri::command]
fn audio_seek(position_ms: u64) -> Result<(), String>;

#[tauri::command]
fn audio_set_volume(volume: f32) -> Result<(), String>;

#[tauri::command]
fn audio_get_status() -> Result<PlaybackStatus, String>;
```

**Events to emit:**
- `audio://progress` - periodic progress updates
- `audio://track-ended` - when track finishes
- `audio://error` - playback errors

**Thread safety:**
- Audio engine runs in dedicated thread
- Commands communicate via channels
- State accessed through Arc<Mutex<>> or similar
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All audio commands callable from JS via invoke()
- [ ] #2 Progress events emit at regular intervals during playback
- [ ] #3 Track-ended event fires when playback completes
- [ ] #4 Error events fire on decode/playback failures
- [ ] #5 Thread-safe access to audio engine state
<!-- AC:END -->
