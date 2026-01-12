---
id: task-092
title: 'P1: Add Tauri migration architecture section to docs'
status: To Do
assignee: []
created_date: '2026-01-12 04:06'
labels:
  - documentation
  - phase-1
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a new section to docs/python-architecture.md (or create docs/tauri-architecture.md) describing the target end state:

**Target architecture:**
- Tauri shell (Rust): window lifecycle, menus, media keys, tray, updater
- Rust playback engine: symphonia for decode (FLAC/MP3/M4A/OGG), rodio/cpal for output
- Python sidecar (PEX): scanning, metadata, DB, playlists, lyrics
- Frontend (WebView): AlpineJS + Basecoat

**Include:**
- Runtime diagram
- Component responsibilities
- Communication patterns (Tauri invoke, REST, WebSocket)
- Platform targets (macOS first, then Linux/Windows)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Target architecture diagram added
- [ ] #2 Component responsibilities documented
- [ ] #3 Communication patterns documented
- [ ] #4 Platform support strategy documented
<!-- AC:END -->
