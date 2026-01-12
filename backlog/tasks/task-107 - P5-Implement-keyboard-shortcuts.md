---
id: task-107
title: 'P5: Implement keyboard shortcuts'
status: To Do
assignee: []
created_date: '2026-01-12 04:09'
labels:
  - frontend
  - ux
  - phase-5
milestone: Tauri Migration
dependencies:
  - task-101
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add keyboard shortcuts for common actions.

**Shortcuts to implement:**
- `Space`: Play/pause
- `→`: Next track (or seek forward 5s with modifier)
- `←`: Previous track (or seek back 5s with modifier)
- `↑`: Volume up
- `↓`: Volume down
- `M`: Mute/unmute
- `L`: Toggle loop mode
- `S`: Toggle shuffle
- `Cmd+F` / `Ctrl+F`: Focus search
- `Escape`: Clear search / close dialogs
- `Delete` / `Backspace`: Remove selected from queue

**Implementation:**
```javascript
// src/js/shortcuts.js
document.addEventListener('keydown', (e) => {
    // Ignore if typing in input
    if (e.target.tagName === 'INPUT') return;
    
    switch(e.code) {
        case 'Space':
            e.preventDefault();
            Alpine.store('player').toggle();
            break;
        case 'ArrowRight':
            if (e.metaKey || e.ctrlKey) {
                Alpine.store('player').seek(Alpine.store('player').progress + 5);
            } else {
                Alpine.store('player').next();
            }
            break;
        // ... etc
    }
});
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Space toggles playback
- [ ] #2 Arrow keys navigate tracks
- [ ] #3 Volume keys work
- [ ] #4 Cmd+F focuses search
- [ ] #5 Shortcuts don't interfere with text input
<!-- AC:END -->
