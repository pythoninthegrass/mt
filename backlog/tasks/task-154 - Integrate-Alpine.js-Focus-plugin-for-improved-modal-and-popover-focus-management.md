---
id: task-154
title: >-
  Integrate Alpine.js Focus plugin for improved modal and popover focus
  management
status: To Do
assignee: []
created_date: '2026-01-16 22:19'
updated_date: '2026-01-19 06:12'
labels:
  - frontend
  - alpine.js
  - accessibility
  - refactor
dependencies: []
priority: medium
ordinal: 25500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Overview

Integrate Alpine.js's official Focus plugin (`@alpinejs/focus`) to improve focus management in modals, popovers, and dropdown menus, replacing manual focus handling code.

## Current State

The basecoat components have manual focus management patterns:

### Popover (`public/js/basecoat/popover.js:14-32`)
```javascript
const closePopover = (focusOnTrigger = true) => {
  if (trigger.getAttribute('aria-expanded') === 'false') return;
  trigger.setAttribute('aria-expanded', 'false');
  content.setAttribute('aria-hidden', 'true');
  if (focusOnTrigger) {
    trigger.focus();
  }
};

const openPopover = () => {
  // ...
  const elementToFocus = content.querySelector('[autofocus]');
  if (elementToFocus) {
    content.addEventListener('transitionend', () => {
      elementToFocus.focus();
    }, { once: true });
  }
};
```

### Dropdown Menu (`public/js/basecoat/dropdown-menu.js:19-27`)
```javascript
const closePopover = (focusOnTrigger = true) => {
  if (trigger.getAttribute('aria-expanded') === 'false') return;
  trigger.setAttribute('aria-expanded', 'false');
  popover.setAttribute('aria-hidden', 'true');
  
  if (focusOnTrigger) {
    trigger.focus();
  }
};
```

### Select (`public/js/basecoat/select.js:100-117, 324-365`)
```javascript
const closePopover = (focusOnTrigger = true) => {
  // ...
  if (focusOnTrigger) trigger.focus();
  // ...
};

// On open:
if (hasTransition()) {
  popover.addEventListener('transitionend', () => {
    filter.focus();
  }, { once: true });
} else {
  filter.focus();
}
```

### Missing Focus Trapping

Currently, **no focus trapping** is implemented for modals or dialogs. Users can Tab out of open modals, which is an accessibility issue.

## Proposed Solution

### Installation
```bash
npm install @alpinejs/focus
```

### Registration (`main.js`)
```javascript
import Alpine from 'alpinejs';
import focus from '@alpinejs/focus';

Alpine.plugin(focus);
Alpine.start();
```

### Focus Trapping with `x-trap`

**Modal/Dialog Example:**
```html
<div 
  x-show="$store.ui.modal" 
  x-trap.noscroll="$store.ui.modal"
  class="modal-overlay"
>
  <div class="modal-content">
    <h2>Modal Title</h2>
    <input type="text" autofocus>
    <button @click="$store.ui.closeModal()">Close</button>
  </div>
</div>
```

**Dropdown with Focus Trap:**
```html
<div x-data="{ open: false }">
  <button @click="open = !open">Menu</button>
  <div 
    x-show="open" 
    x-trap="open"
    @keydown.escape="open = false"
  >
    <a href="#">Item 1</a>
    <a href="#">Item 2</a>
    <a href="#">Item 3</a>
  </div>
</div>
```

### Simplified Focus Return

**Before:**
```javascript
const closePopover = (focusOnTrigger = true) => {
  // ... close logic
  if (focusOnTrigger) {
    trigger.focus();
  }
};
```

**After (with x-trap):**
```html
<!-- Focus automatically returns to trigger when trap is disabled -->
<div x-trap="isOpen">
  <!-- content -->
</div>
```

### Focus Modifiers

```html
<!-- Trap focus and prevent body scroll -->
<div x-trap.noscroll="isOpen">

<!-- Trap focus with inert background -->
<div x-trap.inert="isOpen">

<!-- Initial focus on specific element -->
<div x-trap="isOpen">
  <input x-ref="searchInput" x-init="$watch('isOpen', v => v && $refs.searchInput.focus())">
</div>
```

## Projected Value

| Metric | Before | After |
|--------|--------|-------|
| Focus trap implementation | None | Built-in with x-trap |
| Manual focus() calls | ~15 | ~3 |
| Focus return logic | Manual in each component | Automatic |
| Accessibility compliance | Partial | WCAG 2.1 compliant |
| Keyboard navigation | Manual | Enhanced |

## Use Cases in mt

1. **Add Music Modal** - Focus trap, return focus to button
2. **Playlist Context Menu** - Focus first item, trap, return on close
3. **Library Column Menu** - Focus management
4. **Track Info Dialog** - Focus trap with inert background
5. **Settings Modal** (future) - Full focus management
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Install and register @alpinejs/focus plugin
- [ ] #2 Add x-trap to modal overlay for focus trapping
- [ ] #3 Add x-trap to context menus and dropdowns
- [ ] #4 Verify Tab key cycles within trapped elements
- [ ] #5 Verify Escape closes and returns focus to trigger
- [ ] #6 Remove manual focus() calls where x-trap handles it
- [ ] #7 Test with screen reader for accessibility
- [ ] #8 Verify no focus escape from modals
<!-- AC:END -->
