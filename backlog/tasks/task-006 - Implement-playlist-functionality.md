---
id: task-006
title: Implement playlist functionality
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-10 07:34'
labels: []
dependencies: []
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add custom playlist management with create, rename, delete, add/remove tracks, drag-drop reordering, and YouTube Music-inspired sidebar UI. Complements existing dynamic playlists (Liked Songs, Recently Added, Recently Played, Top 25).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create playlist data structures and storage (playlists + playlist_items tables, PlaylistsManager, FK cascades)
- [ ] #2 Add playlist UI components (sidebar restructure with nav tree + divider + pill button + playlists tree, inline rename, context menus, drag-drop to sidebar, reorder within playlist)
- [ ] #3 Test playlist functionality and persistence (DB tests for CRUD/ordering/cascades, handler tests for playlist-specific delete behavior, identifier standardization tests)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

See [docs/custom-playlists.md](../docs/custom-playlists.md) for full technical specification.

### Key Design Decisions
- **Single-line playlist rows** (name only) in sidebar
- **Standardized identifiers**: `recently_added`/`recently_played` everywhere (fix existing `recent_added`/`recent_played` mismatch)
- **Inline rename flow**: "+ New playlist" creates immediately with auto-suffix name, then inline Entry overlay for rename; commit on Enter/focus-out; duplicate name shows error + keeps editor open

### Phase 1: Identifier Standardization & Database Layer
1. Fix `recent_added`/`recent_played` → `recently_added`/`recently_played` in sidebar tags and routing
2. Add `playlists` and `playlist_items` tables to `DB_TABLES` (both `core/db/__init__.py` and `core/db.py`)
3. Enable `PRAGMA foreign_keys = ON` in both `core/db/database.py` and `core/db.py`
4. Create `core/db/playlists.py` with `PlaylistsManager` class
5. Wire `PlaylistsManager` into `core/db/database.py` facade
6. Add `tests/test_unit_playlists.py`

### Phase 2: Sidebar UI (YouTube Music-inspired)
7. Restructure `core/gui/library_search.py` `LibraryView`:
   - Top navigation tree (Library → Music / Now Playing)
   - 1px divider line (theme color)
   - Pill-shaped "+ New playlist" button (CTkButton)
   - Playlists tree (dynamic playlists first with standardized tags, then custom)
8. Implement inline rename: Entry overlay positioned via `tree.bbox()`, commit on Enter/FocusOut, error on duplicate name

### Phase 3: Playlist Loading & Selection
9. Add `load_custom_playlist(playlist_id)` to `core/player/library.py` with `_item_track_id_map`
10. Update `on_section_select()` in `core/player/ui.py` for new sidebar structure
11. Use view identifier `playlist:<id>` for custom playlist views

### Phase 4: Add to Playlist
12. Add "Add to playlist" submenu to `core/gui/queue_view.py` context menu (dynamically populated)
13. Replace disabled "Save to Playlist" stub in `core/now_playing/view.py` with working submenu

### Phase 5: Drag & Drop
14. Implement internal drag from main list to sidebar playlist names
15. Implement drag-reorder within playlist view (persists via `reorder_playlist()`)

### Phase 6: Delete Behavior & Playlist Management
16. Update `handle_delete()` in `core/player/handlers.py`:
    - In playlist view: remove from playlist only (not library)
    - Add "Remove from playlist" context menu option
17. Implement right-click Rename/Delete on custom playlist names in sidebar

### Phase 7: Tests
18. Add handler tests for playlist-specific delete behavior
19. Add identifier standardization tests
<!-- SECTION:PLAN:END -->
