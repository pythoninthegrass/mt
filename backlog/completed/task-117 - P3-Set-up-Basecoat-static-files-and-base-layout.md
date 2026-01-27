---
id: task-117
title: 'P3: Set up Basecoat static files and base layout'
status: Done
assignee: []
created_date: '2026-01-12 06:43'
updated_date: '2026-01-26 01:28'
labels:
  - frontend
  - basecoat
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-093
priority: high
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Set up Basecoat UI framework using static files (no build step) for the Tauri frontend.

**Approach:** Static file inclusion (like lunch repo) rather than npm/Vite bundling.

**Files to add:**
1. Copy or download Basecoat CSS and JS to `static/`:
   - `static/css/basecoat.cdn.min.css` (from CDN or lunch repo)
   - `static/js/basecoat/all.min.js` (from lunch repo)
2. Create base `index.html` with proper includes

**CDN Sources:**
```html
<link href="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/basecoat.cdn.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/basecoat-css@latest/dist/js/all.min.js" defer></script>
```

**Or copy from lunch repo:**
- `/Users/lance/git/lunch/app/static/basecoat.min.css`
- `/Users/lance/git/lunch/app/static/js/basecoat/all.min.js`

**Base HTML Structure:**
```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>mt</title>
  <link rel="stylesheet" href="/static/css/basecoat.cdn.min.css">
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <script defer src="/static/js/basecoat/all.min.js"></script>
  <link rel="stylesheet" href="/static/css/app.css">
</head>
<body x-data class="app-container">
  <!-- Sidebar (library browser) -->
  <nav class="sidebar">...</nav>
  
  <!-- Main content (queue view) -->
  <main class="main-content">...</main>
  
  <!-- Player controls (bottom bar) -->
  <footer class="player-controls">...</footer>
</body>
</html>
```

**Custom app.css:**
Create `static/css/app.css` for mt-specific styles (layout, colors, etc.)

**Basecoat Auto-Initialization:**
- Basecoat JS auto-initializes on `DOMContentLoaded`
- Uses `MutationObserver` for dynamically added components
- Manual reinit available via `window.basecoat.initAll()`

**Dark Mode:**
Basecoat respects `.dark` class on `<html>` element. Add theme toggle using Basecoat's `.theme-switcher` component.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Basecoat CSS loaded and styling works
- [ ] #2 Basecoat JS loaded and components auto-initialize
- [ ] #3 Dark mode toggle works
- [ ] #4 Base layout structure in place (sidebar, main, footer)
<!-- AC:END -->
