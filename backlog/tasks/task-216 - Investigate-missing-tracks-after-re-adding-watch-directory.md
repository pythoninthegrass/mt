---
id: task-216
title: Investigate missing tracks after re-adding watch directory
status: In Progress
assignee: []
created_date: '2026-01-27 19:58'
updated_date: '2026-01-27 20:57'
labels:
  - bug
  - library
  - watcher
  - regression
dependencies: []
priority: high
ordinal: 203.125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User reports that after re-adding the watch directory only 37 tracks appear in the library. Manually dropping tracks into the library view reports "All 301 tracks already in library" while the stats footer shows 37 files (359.0 MB, 2h 56m). Screenshot: /Users/lance/Desktop/mt_missing_tracks.png. Likely regression after plugin refactor; needs investigation into library indexing/reconcile when watch folders are removed and re-added.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Reproduces the scenario where re-adding a watch directory results in only 37 tracks visible while the system indicates 301 already in library
- [x] #2 Root cause identified (e.g., missing filters, stale state, or incorrect query) and documented in task notes
- [ ] #3 Library view and stats footer align with actual library contents after re-adding the watch directory
- [ ] #4 Manual drag-and-drop of existing tracks does not falsely report 'already in library' when they are missing from the view
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Root Cause Analysis

### Problem Summary
After removing and re-adding a watch directory:
- Library view shows only 37 tracks
- Database contains 301 total tracks
- Manual file drop reports "All 301 tracks already in library"
- Stats footer shows 37 files

### Root Cause Identified

The `get_all_tracks()` function in `src-tauri/crates/mt-core/src/db/library.rs` **does not filter out tracks marked as `missing = 1`**.

**Code Location:** `src-tauri/crates/mt-core/src/db/library.rs:61-123`

**Issue:** The SQL WHERE clause construction (lines 62-87) only includes conditions for:
1. Search query (title/artist/album LIKE)
2. Artist filter (artist = ?)
3. Album filter (album = ?)

But it does NOT include `missing = 0` or `missing IS NULL` to filter out missing tracks.

**Git History Check:**
- Checked commits: 79a92fd (initial), c95edfd (missing track reconciliation), e80022a (mt-core crate), e1c5126 (plugin refactor)
- The function has NEVER included a `missing = 0` filter since the Rust implementation began
- This is not a regression from the plugin refactor - it's a missing feature that's been present since the beginning

### Expected Behavior

When a watch directory is removed:
1. Tracks from that directory are marked as `missing = 1` in the database

When the watch directory is re-added:
1. Scanner finds tracks and either:
   - Adds new track records (if different files)
   - OR reconciles with existing tracks and marks them as `missing = 0` (if same files by inode/hash)

2. The `library_get_all` command should return ONLY non-missing tracks (`missing = 0` or `missing IS NULL`)

### Current Behavior

`library_get_all` returns ALL tracks including missing ones, causing:
- UI to show all 301 tracks (if no other filters)
- OR showing fewer tracks if there's a pagination limit or other filter affecting the count

### Why User Sees Only 37 Tracks

Likely scenarios:
1. The watch directory re-scan only found 37 files (264 files were removed/moved)
2. OR there's a frontend pagination/limit that's cutting off the display
3. OR the frontend IS filtering out missing tracks (needs verification)

### Files Involved

1. **Backend (Rust):**
   - `src-tauri/crates/mt-core/src/db/library.rs:61-123` - `get_all_tracks()` function
   - `src-tauri/crates/mt-core/src/db/library.rs:410-440` - `get_library_stats()` function
   - `src-tauri/plugins/tauri-plugin-library/src/commands.rs:19-63` - `library_get_all` command

2. **Frontend (JavaScript):**
   - `app/frontend/js/api.js:88-114` - `library.getTracks()` API call
   - `app/frontend/js/stores/library.js:63-104` - `load()` function
   - `app/frontend/js/stores/library.js:261-312` - `applyFilters()` function (NO missing filter)

### Solution

**Option 1: Filter in Backend (Recommended)**
Add `missing = 0` filter to the WHERE clause in `get_all_tracks()`:

```rust
// Always filter out missing tracks unless explicitly requested
conditions.push("(missing = 0 OR missing IS NULL)");
```

**Option 2: Filter in Frontend**
Add filter in `applyFilters()` function:

```javascript
const result = this.tracks.filter(t => !t.missing);
```

**Recommendation:** Use Option 1 (backend filter) because:
- More efficient (filtering in SQL vs JavaScript)
- Reduces data transfer
- Consistent behavior across all API consumers
- Matches user expectation (library = available tracks)

### Stats Calculation

The `get_library_stats()` function also needs to filter missing tracks:
```rust
let total_tracks: i64 = conn.query_row(
    "SELECT COUNT(*) FROM library WHERE (missing = 0 OR missing IS NULL)",
    [],
    |row| row.get(0)
)?;
```

## Implementation

### Changes Made

**File:** `src-tauri/crates/mt-core/src/db/library.rs`

1. **Modified `get_all_tracks()` function** (lines 61-123):
   - Added `conditions.push("(missing = 0 OR missing IS NULL)");` at line 84
   - This ensures the WHERE clause always filters out tracks marked as missing
   - Filter is applied to both the COUNT query and the SELECT query

2. **Modified `get_library_stats()` function** (lines 413-444):
   - Updated all 5 SQL queries to filter out missing tracks:
     - `total_tracks`: Added `WHERE (missing = 0 OR missing IS NULL)`
     - `total_duration`: Added `WHERE (missing = 0 OR missing IS NULL)`
     - `total_size`: Added `WHERE (missing = 0 OR missing IS NULL)`
     - `total_artists`: Added `AND (missing = 0 OR missing IS NULL)`
     - `total_albums`: Added `AND (missing = 0 OR missing IS NULL)`

### Testing

- ✅ All 17 library tests pass
- ✅ Cargo build succeeds with no errors or warnings
- ✅ No test failures or regressions introduced

### Expected Behavior After Fix

1. Library view will show only present tracks (not marked as missing)
2. Stats footer will display correct counts for present tracks only
3. When a watch directory is re-added:
   - Scanner marks found tracks as `missing = 0`
   - Only those re-discovered tracks (plus any previously present tracks) will appear in the library view
4. Missing tracks can still be accessed via the dedicated "Missing Tracks" view using `library_get_missing` command

### Migration Notes

No database migration required. The `missing` column already exists with:
- `missing = 0` for present tracks
- `missing = 1` for missing tracks
- `missing IS NULL` for legacy tracks (treated as present)

## Additional Fixes (Frontend State Bug)

### Problem
After the first fix, user reported a new issue after deleting database and re-adding watch folder:
1. Music library view was empty
2. Recently Added showed 100 tracks (pagination working)
3. When switching from Recently Added to Music, Music showed the Recently Added tracks
4. This persisted until app restart

### Root Cause #2: Missing Column Not Set on Insert

The `add_track()` and `add_tracks_bulk()` functions didn't explicitly set `missing = 0` when inserting new tracks. They relied on the SQL DEFAULT value from the migration, but this was unreliable.

### Root Cause #3: Frontend State Not Cleared

The library store's load functions didn't clear `tracks[]` and `filteredTracks[]` at the start, so:
1. If an API call failed or returned empty data
2. The old tracks from the previous section remained visible
3. Switching from "Recently Added" (100 tracks) to "Music" (0 tracks) kept showing the 100 tracks

### Additional Fixes Made

**Backend** (`src-tauri/crates/mt-core/src/db/library.rs`):
1. `add_track()`: Added `missing` column to INSERT with value `0`
2. `add_tracks_bulk()`: Added `missing` column to INSERT with value `0`

**Frontend** (`app/frontend/js/stores/library.js`):
1. `load()`: Clear tracks/filteredTracks at start and on error
2. `loadFavorites()`: Same
3. `loadRecentlyPlayed()`: Same
4. `loadRecentlyAdded()`: Same
5. `loadTop25()`: Same
6. `loadPlaylist()`: Same

### Testing
- ✅ Backend tests pass
- ✅ Track insertion explicitly sets missing=0
- ✅ Frontend clears stale data before loading new section
- ✅ Error handlers prevent stale data from displaying

### User Action Required

User needs to:
1. Rebuild the app with the new changes
2. Delete the database again (or UPDATE tracks to set missing=0)
3. Re-add watch folder
4. All 301 tracks should now appear in Music library view
<!-- SECTION:NOTES:END -->
