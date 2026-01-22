---
id: task-187
title: Migrate settings API to Rust (Phase 3)
status: Done
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-22 17:07'
labels:
  - rust
  - migration
  - settings
  - phase-3
  - api
dependencies:
  - task-173
priority: medium
ordinal: 2656.25
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate settings management from FastAPI to Rust Tauri commands, or replace with Tauri's built-in Store API.

**Endpoints to Migrate** (2 total):
- GET `/api/settings` - Get all settings
- PUT `/api/settings` - Update multiple settings

**Current Settings**:
- volume (integer)
- shuffle (boolean)
- loop_mode (string: "none", "all", "one")
- theme (string: "dark", "light")
- sidebar_width (integer)
- queue_panel_height (integer)
- lastfm_* (Last.fm integration settings)

**Implementation Options**:

**Option A: Migrate to Rust database layer**
- Use existing settings table (key-value pairs)
- Convert to Tauri commands
- Type coercion for booleans/integers
- Emit events on settings changes

**Option B: Use Tauri Store API (RECOMMENDED)**
- Use Tauri's built-in persistent key-value store
- Type-safe with serde
- Automatic persistence
- Simpler code
- No database table needed

**Recommended Approach**: Use Tauri Store API
```rust
use tauri_plugin_store::StoreBuilder;

// Initialize store
let store = StoreBuilder::new(app.handle(), "settings.json").build();

// Get setting
let volume = store.get("volume").and_then(|v| v.as_i64());

// Set setting
store.set("volume", json!(75));
store.save()?;
```

**Estimated Effort**: 1-2 days
**File**: backend/routes/settings.py (56 lines)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Settings storage implemented (database or Tauri Store)
- [x] #2 Get all settings working
- [x] #3 Update settings working
- [x] #4 Type coercion functional (booleans, integers)
- [x] #5 Settings events emitted on changes
- [x] #6 Default values handled correctly
- [x] #7 Frontend updated and working
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Implemented using Tauri Store API (Option B) as specified.

### Backend (Rust)
- Added `tauri-plugin-store` v2 dependency to Cargo.toml
- Registered store plugin in lib.rs builder
- Created `src-tauri/src/commands/settings.rs` with 5 Tauri commands:
  - `settings_get_all` - Get all settings with defaults
  - `settings_get` - Get single setting by key
  - `settings_set` - Set single setting
  - `settings_update` - Bulk update multiple settings
  - `settings_reset` - Reset to defaults
- Settings stored in `settings.json` file via Tauri Store
- Default values: volume=75, shuffle=false, loop_mode="none", theme="dark", sidebar_width=250, queue_panel_height=300
- Emits `settings://changed` event on any setting change
- Emits `settings://reset` event on reset

### Frontend
- Added `api.settings` namespace to api.js with all commands:
  - `getAll()`, `get(key)`, `set(key, value)`, `update(settings)`, `reset()`
- Updated events.js to handle settings events:
  - `settings://changed` applies changes to UI/player stores
  - `settings://reset` logs reset action

### Capabilities
- Added `store:default` permission to capabilities/default.json

### Notes
- UI store still uses Alpine.$persist() for its local UI preferences (sidebarOpen, libraryViewMode, themePreset, etc.)
- The Tauri Store provides persistent backend storage for settings that may need backend awareness
- shuffle/loop_mode are session-only in queue store by design (not persisted)
<!-- SECTION:NOTES:END -->
