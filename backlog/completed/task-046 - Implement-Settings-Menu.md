---
id: task-046
title: Implement Settings Menu
status: Done
assignee: []
created_date: '2025-10-12 07:56'
updated_date: '2026-01-17 05:34'
labels: []
dependencies:
  - task-162
ordinal: 125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create comprehensive settings menu with General, Appearance, Shortcuts, Now Playing, Library, Advanced sections including app info and maintenance
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Settings menu accessible via Cog icon or Cmd-,
- [x] #2 All sections implemented (General, Appearance, Shortcuts, Now Playing, Library, Advanced)
- [x] #3 App info shows version, build, OS details
- [x] #4 Maintenance section allows resetting settings and capturing logs
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Phase 1: Entry Points
1. Add cog icon to sidebar (near bottom, after playlists section)
2. Add global `Cmd-,` keyboard handler to open settings
3. Both trigger `ui.setView('settings')`

### Phase 2: Settings View Scaffold
1. Create settings view HTML in index.html with `x-show="$store.ui.view === 'settings'"`
2. Two-column layout: left nav (section list) + right pane (section content)
3. Sections in left nav: General, Appearance, Shortcuts, Advanced
4. Track active section via `$persist` key `mt:settings:activeSection`

### Phase 3: Section Content

**General (stub)**
- Empty placeholder content

**Appearance (depends on task-162)**
- Theme preset selector (Light / Metro Teal)
- Calls `ui.setThemePreset()` from task-162

**Shortcuts (stub with placeholders)**
- Three rows: Queue next, Queue last, Stop after track
- Each row: name + info icon with tooltip "Not configurable yet"
- No actual keybinding functionality

**Advanced (real)**
- App Info panel: Version, Build, OS + Arch
- Maintenance: Reset settings button, Export logs button

### Phase 4: Tauri Commands
1. Add `app_get_info` command returning version/build/os/arch
2. Add `export_diagnostics` command for log/diagnostic bundle export

### Phase 5: Maintenance Actions
- Reset settings: confirm dialog → clear user-exposed `mt:*` keys → reload
- Export logs: save dialog → write diagnostic bundle to chosen path

### Notes
- All settings use Alpine `$persist` (not raw localStorage)
- Reset only clears user-exposed settings (theme preset, settings section, etc.), not internal state like column widths
- Changes apply immediately (no Save button)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## User-exposed settings keys (for reset)
- `mt:ui:themePreset` (from task-162)
- `mt:settings:activeSection`
- Future: any settings added to General/Appearance/etc.

## Keys NOT reset (internal/layout state)
- `mt:columns:*` (column widths/order/visibility)
- `mt:sidebar:*` (collapse state, active section)
- `mt:ui:sidebarWidth`
- `mt:ui:libraryViewMode`
<!-- SECTION:NOTES:END -->
