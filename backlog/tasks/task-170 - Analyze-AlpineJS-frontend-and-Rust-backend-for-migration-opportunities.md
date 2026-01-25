---
id: task-170
title: Analyze AlpineJS frontend and Rust backend for migration opportunities
status: In Progress
assignee: []
created_date: '2026-01-19 06:11'
updated_date: '2026-01-24 22:30'
labels:
  - analysis
  - architecture
  - frontend
  - rust
  - migration
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the current AlpineJS frontend components, stores, and logic alongside the existing Rust/Tauri backend to identify what can be safely migrated to Rust to simplify the frontend architecture. Focus on:

- AlpineJS stores and state management
- Frontend business logic that could be moved to backend
- UI components that are data-heavy and could benefit from server-side rendering or backend-driven updates
- API communication patterns that could be simplified with direct Tauri commands
- Performance bottlenecks in the frontend that Rust could solve

Report findings with specific recommendations for migration, including risk assessment and complexity estimates.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 AlpineJS stores analyzed for state management patterns
- [x] #2 Frontend business logic identified for migration candidates
- [x] #3 Rust backend command coverage reviewed
- [x] #4 Performance bottlenecks identified
- [x] #5 Migration recommendations documented with risk assessment
- [x] #6 Implementation phases outlined
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
# Analysis: AlpineJS Frontend to Rust Backend Migration Opportunities

## Current Architecture Summary

### Frontend (AlpineJS)
- **4 Stores**: `player.js`, `queue.js`, `library.js`, `ui.js`
- **7 Components**: player-controls, sidebar, library-browser, now-playing-view, settings-view, metadata-modal
- **API Layer**: `api.js` - Tauri command wrapper with HTTP fallback
- **Events**: `events.js` - Tauri event subscription system

### Backend (Rust/Tauri)
- **87 Tauri commands** fully implemented
- **Modules**: audio, commands, db, dialog, events, lastfm, library, media_keys, metadata, scanner, watcher
- **Database**: SQLite via rusqlite with full CRUD operations

---

## Migration Opportunities

### 1. **HIGHEST PRIORITY: Queue State Management** (Complexity: Medium, Risk: Low)

**Current State (Frontend):**
```javascript
// queue.js - Lines 11-29
items: [],           // Array of track objects in play order
currentIndex: -1,    // Currently playing index
shuffle: false,
loop: 'none',        // 'none', 'all', 'one'
_repeatOnePending: false,
_originalOrder: [],  // Preserved for unshuffle
```

**Problem:**
- Frontend maintains authoritative queue state
- Backend stores queue in SQLite but frontend doesn't trust it
- Race conditions between frontend state and backend events (events disabled at line 109-114 of events.js)
- Shuffle/unshuffle logic duplicated in both frontend and backend

**Recommendation:**
Move `currentIndex`, `shuffle`, `loop`, `_originalOrder` to Rust backend:
1. Create `queue_state` table: `current_index`, `shuffle_enabled`, `loop_mode`, `original_order_json`
2. Add Tauri commands: `queue_get_playback_state`, `queue_set_current_index`, `queue_set_shuffle`, `queue_set_loop`
3. Emit `queue:state-changed` events when state changes
4. Frontend becomes a thin reactive layer

**Benefits:**
- Single source of truth for playback state
- Fixes race conditions
- Enables future features (multi-device sync, remote control)

---

### 2. **HIGH PRIORITY: Search/Sort/Filter Logic** (Complexity: Low, Risk: Low)

**Current State (Frontend):**
```javascript
// library.js - Lines 250-334 - applyFilters()
// - Search across title/artist/album
// - Sort by multiple fields with tiebreakers
// - Strip ignored prefixes for sorting
```

**Problem:**
- 10,000 track limit hardcoded (`api.library.getTracks({ limit: 10000 })`)
- Client-side search scales poorly with large libraries
- Sorting logic reimplemented in JavaScript (already exists in Rust)

**Recommendation:**
1. Backend already has `library_get_all` with sort/search params - **use them**
2. Add `ignore_prefix_words` setting to backend sort
3. Remove client-side `applyFilters()` for search/sort
4. Keep only local filtering for instant UI feedback during typing

**Benefits:**
- Removes 10K track limit
- 10-100x faster for large libraries
- Reduces memory footprint

---

### 3. **MEDIUM PRIORITY: Scrobble Threshold Checking** (Complexity: Low, Risk: Low)

**Current State (Frontend):**
```javascript
// player.js - Lines 52-65, 101-155
// _checkScrobble() - Checks playback position against threshold
// Calls api.lastfm.scrobble() with calculated data
```

**Problem:**
- Scrobble decision made in frontend
- Backend re-validates (double work)
- If frontend crashes mid-song, scrobble is lost

**Recommendation:**
1. Move scrobble checking to Rust audio progress loop (`src-tauri/src/commands/audio.rs:111-115`)
2. Backend tracks playback position and auto-scrobbles
3. Frontend just displays scrobble status

**Benefits:**
- More reliable scrobbling
- Scrobbles even if UI is unresponsive
- Simplified frontend logic

---

### 4. **MEDIUM PRIORITY: Play Count Tracking** (Complexity: Low, Risk: Low)

**Current State (Frontend):**
```javascript
// player.js - Lines 52-57
// _updatePlayCount() called when playback >= 75%
```

**Problem:**
- Similar to scrobbling - frontend manages timing
- Could be lost if frontend state resets

**Recommendation:**
1. Backend audio thread already tracks progress
2. Add `check_play_count_threshold` to audio loop
3. Backend calls `library_update_play_count` automatically

---

### 5. **MEDIUM PRIORITY: Time Formatting Utilities** (Complexity: Trivial, Risk: None)

**Current State (Frontend):**
```javascript
// player.js - Lines 526-532, player-controls.js - Lines 140-146, 330-338
// formatTime(), formatDurationLong(), formatBytes() - duplicated
```

**Recommendation:**
1. Add Tauri commands: `format_duration_ms`, `format_bytes`
2. Or: send pre-formatted strings from backend where possible
3. Or: keep in frontend (trivial computation, but duplication is technical debt)

---

### 6. **LOW PRIORITY: Theme/Preference Persistence** (Complexity: Low, Risk: Low)

**Current State (Frontend):**
```javascript
// ui.js - Uses Alpine.$persist for localStorage
// Settings stored in browser, not shared across devices
```

**Recommendation:**
1. Already have `settings_get/set` Tauri commands
2. Migrate persisted UI preferences to backend settings store
3. Keep local cache for instant UI response

---

### 7. **LOW PRIORITY: Artwork Caching** (Complexity: Medium, Risk: Low)

**Current State (Frontend):**
```javascript
// player.js - Lines 441-456 - loadArtwork()
// Fetches artwork on each track change
```

**Recommendation:**
1. Backend already extracts artwork (`library_get_artwork`)
2. Add in-memory LRU cache in Rust for recently-played artwork
3. Reduces IPC calls for queue navigation

---

## NOT Recommended for Migration

### 1. **UI State (View, Modal, Toast, Context Menu)**
- Pure presentation state
- No benefit from backend management
- Would increase IPC latency

### 2. **Drag-and-Drop Interactions**
- Requires immediate visual feedback
- Backend roundtrip would feel laggy
- Current approach is correct

### 3. **Progress Bar / Volume Slider Visual State**
- High-frequency updates (250ms)
- Already optimized with local state + debounced backend sync

---

## Risk Assessment

| Migration Item | Complexity | Risk | Breaking Change | Priority |
|----------------|------------|------|-----------------|----------|
| Queue State Management | Medium | Low | No | Highest |
| Search/Sort Backend | Low | Low | No | High |
| Scrobble Checking | Low | Low | No | Medium |
| Play Count Tracking | Low | Low | No | Medium |
| Time Formatting | Trivial | None | No | Low |
| Theme Persistence | Low | Low | No | Low |
| Artwork Caching | Medium | Low | No | Low |

---

## Implementation Phases

### Phase 1: Quick Wins (1-2 days)
1. Enable backend search/sort (already implemented)
2. Remove 10K track limit
3. Backend play count tracking

### Phase 2: State Consolidation (3-5 days)
1. Queue state migration to Rust
2. Re-enable queue events with proper synchronization
3. Scrobble threshold in audio loop

### Phase 3: Polish (2-3 days)
1. Artwork caching
2. Settings unification
3. Time formatting cleanup
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Analysis Completed: 2026-01-24

Analyzed:
- 4 AlpineJS stores (player.js, queue.js, library.js, ui.js)
- 7 frontend components
- API layer and event system
- 87 Tauri commands in Rust backend
- Database layer and audio engine

Key findings:
1. Queue state is split between frontend (authoritative) and backend (persistence) - should consolidate
2. Client-side search/sort scales poorly - backend already has this capability
3. Scrobble/play-count timing logic in frontend should move to audio loop
4. UI presentation state correctly remains in frontend

No critical issues found. Migration opportunities are incremental improvements.
<!-- SECTION:NOTES:END -->
