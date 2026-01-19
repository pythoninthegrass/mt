---
id: task-113
title: 'P3: Build Alpine.js queue view component'
status: To Do
assignee: []
created_date: '2026-01-12 06:35'
updated_date: '2026-01-19 00:41'
labels:
  - frontend
  - alpine
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-111
  - task-117
priority: high
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the queue view UI component using Alpine.js and Basecoat.

**Features:**
- Display current queue with track info
- Highlight currently playing track
- Drag-and-drop reordering
- Remove tracks from queue
- Clear queue button
- Show queue duration total

**Implementation:**
- Alpine.js store for queue state
- Fetch from sidecar `/api/queue` endpoints
- Use Basecoat UI components (static file approach)

**Basecoat Setup (shared with task-112):**
```html
<link href="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/basecoat.cdn.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/js/all.min.js" defer></script>
```

**Basecoat Components to Use:**
- `.card` - Queue item container
- `.btn` - Remove/clear buttons
- `.dropdown-menu` - Track context menu (`role="menu"`, `role="menuitem"`)

**Queue Item HTML Structure:**
```html
<div class="card queue-item" draggable="true" data-track-id="123">
  <div class="queue-item-info">
    <span class="title">Track Title</span>
    <span class="artist">Artist Name</span>
  </div>
  <span class="duration">3:45</span>
  <div class="dropdown-menu">
    <button type="button" class="btn btn-ghost">...</button>
    <div role="menu">
      <button role="menuitem">Remove</button>
      <button role="menuitem">Play Next</button>
    </div>
  </div>
</div>
```

**Currently Playing Highlight:**
Use `aria-current="true"` or a `.playing` class on the active queue item.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Queue displays with track metadata
- [ ] #2 Drag-and-drop reordering works
- [ ] #3 Currently playing track is highlighted
- [ ] #4 Remove and clear operations work
<!-- AC:END -->
