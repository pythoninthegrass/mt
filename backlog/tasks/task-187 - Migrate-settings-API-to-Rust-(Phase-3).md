---
id: task-187
title: Migrate settings API to Rust (Phase 3)
status: In Progress
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-21 18:32'
labels:
  - rust
  - migration
  - settings
  - phase-3
  - api
dependencies:
  - task-173
priority: medium
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
- [ ] #1 Settings storage implemented (database or Tauri Store)
- [ ] #2 Get all settings working
- [ ] #3 Update settings working
- [ ] #4 Type coercion functional (booleans, integers)
- [ ] #5 Settings events emitted on changes
- [ ] #6 Default values handled correctly
- [ ] #7 Frontend updated and working
<!-- AC:END -->
