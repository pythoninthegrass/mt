---
id: task-006
title: Implement playlist functionality
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-10 07:14'
labels: []
dependencies: []
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add playlist management with recently added, recently played, and top 25 most played features
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create playlist data structures and storage (playlists + playlist_items tables, PlaylistsManager)
- [ ] #2 Add playlist UI components (sidebar restructure, + New playlist button, context menus, drag-drop)
- [ ] #3 Test playlist functionality and persistence (DB tests, handler tests)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

See [docs/custom-playlists.md](../docs/custom-playlists.md) for full technical specification.

### Phase 1: Database Layer
1. Add `playlists` and `playlist_items` tables to `DB_TABLES` (both `core/db/__init__.py` and `core/db.py`)
2. Enable `PRAGMA foreign_keys = ON` in `core/db/database.py`
3. Create `core/db/playlists.py` with `PlaylistsManager` class
4. Wire `PlaylistsManager` into `core/db/database.py` facade

### Phase 2: Sidebar UI (YouTube Music-inspired)
5. Restructure `core/gui/library_search.py` `LibraryView`:
   - Top navigation tree (Library → Music / Now Playing)
   - 1px divider line (theme color)
   - Pill-shaped "+ New playlist" button (CTkButton)
   - Playlists tree (dynamic playlists first, then custom)
6. Implement playlist name auto-suffix: "New playlist", "New playlist (2)", etc.

### Phase 3: Playlist Loading & Selection
7. Add `load_custom_playlist(playlist_id)` to `core/player/library.py`
8. Update `on_section_select()` in `core/player/ui.py` for new sidebar structure
9. Use view identifier `playlist:<id>` for custom playlist views

### Phase 4: Add to Playlist
10. Add "Add to playlist" submenu to `core/gui/queue_view.py` context menu
11. Replace disabled "Save to Playlist" stub in `core/now_playing/view.py` with working submenu

### Phase 5: Drag & Drop
12. Implement internal drag from main list to sidebar playlist names
13. Implement drag-reorder within playlist view (persists via `reorder_playlist()`)

### Phase 6: Delete Behavior
14. Update `handle_delete()` in `core/player/handlers.py`:
    - In playlist view: remove from playlist only (not library)
    - Add "Remove from playlist" context menu option
15. Implement right-click Rename/Delete on custom playlist names in sidebar

### Phase 7: Tests
16. Add `tests/test_unit_playlists.py` for DB operations
17. Add handler tests for playlist-specific delete behavior

### Key Design Decisions
- No duplicate tracks per playlist (enforced by `UNIQUE(playlist_id, track_id)`)
- Dynamic playlists are non-editable (no right-click menu)
- Playlist order persisted via `position` column
- Foreign key cascades handle cleanup on library/playlist deletion
<!-- SECTION:PLAN:END -->
