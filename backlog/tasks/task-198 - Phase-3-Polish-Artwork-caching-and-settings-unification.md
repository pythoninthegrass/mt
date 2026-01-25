---
id: task-198
title: 'Phase 3: Polish - Artwork caching and settings unification'
status: To Do
assignee: []
created_date: '2026-01-24 22:30'
updated_date: '2026-01-25 07:12'
labels:
  - implementation
  - frontend
  - rust
  - migration
  - phase-3
  - polish
dependencies:
  - task-170
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the polish migrations identified in task-170 analysis:

1. **Artwork caching in Rust**
   - Add in-memory LRU cache for recently-played track artwork
   - Reduces IPC calls when navigating queue (prev/next)
   - Cache invalidation when track metadata changes

2. **Settings unification**
   - Migrate Alpine.$persist UI preferences to backend settings store
   - Already have `settings_get/set` Tauri commands
   - Keep local cache for instant UI response, sync to backend

3. **Time formatting cleanup** (optional)
   - Either: Add Tauri commands `format_duration_ms`, `format_bytes`
   - Or: Send pre-formatted strings from backend
   - Or: Consolidate frontend utilities to single module
   - Goal: Remove duplication across player.js and player-controls.js

These are lower priority polish items that improve performance and consistency.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 LRU artwork cache implemented in Rust
- [x] #2 Artwork cache reduces IPC calls for queue navigation
- [x] #3 UI preferences migrated from localStorage to backend settings
- [x] #4 Settings sync between frontend cache and backend store
- [x] #5 Time formatting utilities consolidated (one of the three approaches)
- [x] #6 All existing tests pass
- [ ] #7 Performance improvement measurable for large queues
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Progress

### 1. Artwork Caching ✅

**Implementation:**
- Created `src-tauri/src/scanner/artwork_cache.rs` with LRU cache (capacity: 100)
- Uses `lru` crate (v0.12) with thread-safe Mutex wrapper
- Cache stores `Option<Artwork>` keyed by track ID
- Added cache to Tauri app state in lib.rs

**Integration:**
- Updated `library_get_artwork` command to use cache (src-tauri/src/library/commands.rs:98)
- Updated `library_get_artwork_url` command to use cache (src-tauri/src/library/commands.rs:116)
- Added cache invalidation in `library_rescan_track` (line 192)

**Benefits:**
- Eliminates redundant IPC calls when navigating prev/next in queue
- Caches both successful artwork and "None" results to avoid repeated file I/O
- Thread-safe for concurrent access
- Automatic LRU eviction for memory management

### 2. Time Formatting Consolidation ✅

**Created shared utility module:** `app/frontend/js/utils/formatting.js`

**Functions:**
- `formatTime(ms)` - Format milliseconds as M:SS
- `formatDuration(seconds)` - Format seconds as M:SS
- `formatBytes(bytes)` - Human-readable file sizes
- `formatBitrate(bitrate)` - Format bitrate as kbps
- `formatSampleRate(sampleRate)` - Format sample rate as Hz

**Refactoring:**
- Removed duplicate `formatTime()` from `player.js` (was line 426)
- Removed duplicate `formatTime()` from `player-controls.js` (was line 142)
- Removed duplicate `formatBytes()` from `player-controls.js` (was line 324)
- Removed duplicate `formatDuration()` from `metadata-modal.js` (was line 463)
- Made formatting utilities globally available in `main.js` for HTML templates

**Impact:**
- Single source of truth for all formatting logic
- Easier to maintain and test
- Consistent formatting across all components
- Reduced code duplication by ~40 lines

### 3. Settings Unification ✅

**Created settings service:** `app/frontend/js/services/settings.js`

**Architecture:**
- Wraps Tauri `settings_get/set/get_all` commands
- Maintains local cache (Map) for instant reads
- Asynchronous initialization loads all settings from backend
- Listens for `settings://changed` events for cross-instance sync
- Provides watchers for reactive updates

**Migrated Components:**

1. **ui.js store** (`app/frontend/js/stores/ui.js`)
   - Removed Alpine.$persist for: sidebarOpen, sidebarWidth, libraryViewMode, theme, themePreset, settingsSection, sortIgnoreWords, sortIgnoreWordsList
   - Added `_initSettings()` to load from backend on startup
   - Uses `this.$watch()` to sync changes to backend
   - Settings keys prefixed with `ui:` (e.g., `ui:sidebarOpen`)

2. **sidebar.js component** (`app/frontend/js/components/sidebar.js`)
   - Removed Alpine.$persist for: activeSection, isCollapsed
   - Added `_initSettings()` to load from backend
   - Settings keys prefixed with `sidebar:` (e.g., `sidebar:activeSection`)

3. **library-browser.js component** (`app/frontend/js/components/library-browser.js`)
   - Removed Alpine.$persist for: columnVisibility, columnOrder, _persistedWidths
   - Updated `_initColumnSettings()` to load from backend
   - Debounced watchers (500ms) to avoid excessive IPC during column resizing
   - Settings keys prefixed with `library:` (e.g., `library:columnVisibility`)

**Initialization Flow:**
1. `main.js` initializes settings service before Alpine starts
2. Settings service loads all values from backend via `settings_get_all`
3. Each component/store loads its settings from the cache on init
4. Watchers sync any changes back to backend asynchronously
5. `settings://changed` events keep all instances in sync

**Benefits:**
- Settings persisted to disk (Tauri store API) instead of browser localStorage
- Works in both Tauri and browser modes (graceful fallback)
- Centralized settings management
- Real-time sync across app instances
- Type-safe backend validation
- Eliminates 13 Alpine.$persist calls

**Files Modified:**
- Created: `app/frontend/js/services/settings.js` (new settings service)
- Modified: `app/frontend/main.js` (async init, settings import)
- Modified: `app/frontend/js/stores/ui.js` (8 settings migrated)
- Modified: `app/frontend/js/components/sidebar.js` (2 settings migrated)
- Modified: `app/frontend/js/components/library-browser.js` (3 settings migrated)
<!-- SECTION:NOTES:END -->
