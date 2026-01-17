---
id: task-162
title: Implement Metro Teal theme preset
status: Done
assignee: []
created_date: '2026-01-17 05:24'
updated_date: '2026-01-17 05:27'
labels:
  - ui
  - appearance
  - themes
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Metro Teal as a dark theme preset alongside the current Light theme. This establishes the preset system that Settings (task-046) will use for theme selection.

**Reference:** `docs/images/mt_repeat_once.png` defines the Metro Teal look.

**Key colors (from reference image):**
- Main background: `#121212`
- Sidebar/panels: `#1a1a1a`
- Borders/separators: `#333333`
- Primary accent (teal): `#00b7c3`
- Playing/selected row bg: `#00343a` / `#1e3a3a`
- Playing row text: `#33eeff`
- Foreground text: `#ffffff`
- Muted text: `#888888`

**Implementation approach:**
- Introduce `themePreset` persisted setting (`$persist`) with values: `"light"` | `"metro-teal"`
- Apply preset via root attribute: `document.documentElement.dataset.themePreset`
- Metro Teal forces dark mode (`classList.add('dark')`) plus preset-specific CSS variable overrides
- CSS variables to override: `--background`, `--foreground`, `--muted`, `--border`, `--primary`, `--accent`, `--card`, `--popover`, plus custom vars for playing row, progress fill, etc.
- Update `ui.js` store: add `themePreset`, `setThemePreset()`, `applyThemePreset()`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 themePreset setting persisted via Alpine $persist with values light | metro-teal
- [x] #2 Metro Teal preset applies dark mode base plus CSS variable overrides
- [x] #3 CSS variables cover: background, foreground, muted, border, primary, accent, card, popover, playing row, progress fill
- [ ] #4 Visual appearance matches docs/images/mt_repeat_once.png reference
- [x] #5 Switching presets updates UI immediately without page reload
- [x] #6 Playwright test verifies preset switch changes root attribute and a visible color
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

**Files changed:**
- `app/frontend/js/stores/ui.js`: Added `themePreset` with `$persist`, `setThemePreset()`, `applyThemePreset()` methods
- `app/frontend/styles.css`: Added Metro Teal CSS variable overrides under `[data-theme-preset="metro-teal"]`
- `app/frontend/tests/stores.spec.js`: Added 4 Playwright tests for theme preset functionality

**CSS Variables defined for Metro Teal:**
- Core: background, foreground, card, popover, primary, secondary, muted, accent, destructive, border, input, ring
- Custom: mt-playing-bg, mt-playing-fg, mt-row-alt, mt-row-hover, mt-progress-bg, mt-progress-fill, mt-sidebar-bg

**AC#4 (visual match to reference):** Requires manual verification in Tauri. Colors are mapped from the reference image but fine-tuning may be needed.
<!-- SECTION:NOTES:END -->
