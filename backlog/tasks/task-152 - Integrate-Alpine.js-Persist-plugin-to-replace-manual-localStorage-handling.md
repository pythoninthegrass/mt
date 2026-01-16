---
id: task-152
title: Integrate Alpine.js Persist plugin to replace manual localStorage handling
status: In Progress
assignee: []
created_date: '2026-01-16 22:19'
updated_date: '2026-01-16 22:21'
labels:
  - frontend
  - alpine.js
  - refactor
  - tech-debt
dependencies: []
priority: high
ordinal: 23500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Overview

Replace bespoke localStorage persistence logic across multiple stores/components with Alpine.js's official Persist plugin (`@alpinejs/persist`).

## Current State

The codebase has **4 separate implementations** of manual localStorage read/write patterns:

### 1. Queue Store (`js/stores/queue.js:38-63`)
```javascript
_loadLoopState() {
  try {
    const saved = localStorage.getItem('mt:loop-state');
    if (saved) {
      const { loop, shuffle } = JSON.parse(saved);
      if (['none', 'all', 'one'].includes(loop)) this.loop = loop;
      if (typeof shuffle === 'boolean') this.shuffle = shuffle;
    }
  } catch (e) { console.error('[queue] Failed to load loop state:', e); }
},
_saveLoopState() {
  try {
    localStorage.setItem('mt:loop-state', JSON.stringify({
      loop: this.loop,
      shuffle: this.shuffle,
    }));
  } catch (e) { console.error('[queue] Failed to save loop state:', e); }
}
```

### 2. UI Store (`js/stores/ui.js:40-76`)
```javascript
init() {
  const saved = localStorage.getItem('mt:ui');
  if (saved) {
    try {
      const data = JSON.parse(saved);
      this.sidebarOpen = data.sidebarOpen ?? true;
      this.sidebarWidth = data.sidebarWidth ?? 256;
      this.currentView = data.currentView ?? 'library';
    } catch (e) { console.error('[ui] Failed to load preferences:', e); }
  }
},
save() {
  localStorage.setItem('mt:ui', JSON.stringify({
    sidebarOpen: this.sidebarOpen,
    sidebarWidth: this.sidebarWidth,
    currentView: this.currentView,
  }));
}
```

### 3. Sidebar Component (`js/components/sidebar.js:26-52`)
```javascript
init() {
  const saved = localStorage.getItem('mt:sidebar');
  if (saved) {
    try {
      const data = JSON.parse(saved);
      this.activeSection = data.activeSection ?? 'library';
      this.isCollapsed = data.isCollapsed ?? false;
    } catch {}
  }
},
save() {
  localStorage.setItem('mt:sidebar', JSON.stringify({
    activeSection: this.activeSection,
    isCollapsed: this.isCollapsed,
  }));
}
```

### 4. Library Browser (`js/components/library-browser.js:347-390`)
```javascript
loadColumnSettings() {
  try {
    const saved = localStorage.getItem(COLUMN_SETTINGS_KEY);
    if (saved) {
      const data = JSON.parse(saved);
      // ... complex merging logic
    }
  } catch (e) { console.error('[library-browser] Failed to load column settings:', e); }
},
saveColumnSettings() {
  try {
    localStorage.setItem(COLUMN_SETTINGS_KEY, JSON.stringify({
      widths: this._baseColumnWidths || this.columnWidths,
      visibility: this.columnVisibility,
      order: this.columnOrder,
    }));
  } catch (e) { console.error('[library-browser] Failed to save:', e); }
}
```

## Proposed Solution

### Installation
```bash
npm install @alpinejs/persist
```

### Registration (`main.js`)
```javascript
import Alpine from 'alpinejs';
import persist from '@alpinejs/persist';

Alpine.plugin(persist);
Alpine.start();
```

### Refactored Examples

**Queue Store:**
```javascript
Alpine.store('queue', {
  loop: Alpine.$persist('none').as('mt:loop'),
  shuffle: Alpine.$persist(false).as('mt:shuffle'),
  // No more _loadLoopState/_saveLoopState methods needed
});
```

**UI Store:**
```javascript
Alpine.store('ui', {
  sidebarOpen: Alpine.$persist(true).as('mt:ui:sidebarOpen'),
  sidebarWidth: Alpine.$persist(256).as('mt:ui:sidebarWidth'),
  currentView: Alpine.$persist('library').as('mt:ui:currentView'),
  // No more init()/save() methods needed
});
```

**Sidebar Component:**
```javascript
Alpine.data('sidebar', () => ({
  activeSection: Alpine.$persist('library').as('mt:sidebar:section'),
  isCollapsed: Alpine.$persist(false).as('mt:sidebar:collapsed'),
}));
```

## Projected Value

| Metric | Before | After |
|--------|--------|-------|
| Lines of code | ~120 | ~20 |
| Manual error handling | 8 try/catch blocks | 0 |
| Boilerplate methods | 8 (load/save pairs) | 0 |
| Consistency | 4 different patterns | 1 declarative pattern |

## Migration Notes

- Storage keys can remain the same for backwards compatibility OR use new flat keys
- Consider using `Alpine.$persist().using(sessionStorage)` for session-only data
- The plugin handles JSON serialization automatically
- Reactive updates are automatic - no manual `save()` calls needed
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Install and register @alpinejs/persist plugin
- [ ] #2 Refactor queue.js loop/shuffle state to use $persist
- [ ] #3 Refactor ui.js preferences to use $persist
- [ ] #4 Refactor sidebar.js state to use $persist
- [ ] #5 Refactor library-browser.js column settings to use $persist
- [ ] #6 Remove all manual localStorage load/save methods
- [ ] #7 Verify backwards compatibility with existing stored preferences
- [ ] #8 All existing Playwright tests pass without modification
<!-- AC:END -->
