---
id: task-006
title: Implement playlist functionality
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-10 08:56'
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
- [x] #2 Add playlist UI components (sidebar restructure with nav tree + divider + pill button + playlists tree, inline rename, context menus, drag-drop to sidebar, reorder within playlist)
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Phase 2: Sidebar UI Structure (2026-01-10)

### Sidebar Restructure - PARTIAL IMPLEMENTATION
Restructured `core/gui/library_search.py` LibraryView with YouTube Music-inspired layout:
- Navigation tree (Library → Music, Now Playing) - fixed height with visual spacing
- Horizontal divider (ttk.Separator)
- Pill-shaped "+ New playlist" button (CTkButton) - **STUB ONLY, NO FUNCTIONALITY**
- Playlists tree (dynamic playlists: Liked Songs, Recently Added, Recently Played, Top 25 Most Played)

**IMPORTANT**: The "+ New playlist" button is a placeholder stub. Clicking it does nothing. The following Phase 2 features are NOT implemented:
- ❌ Custom playlist creation
- ❌ Inline rename functionality
- ❌ Context menus for playlists
- ❌ Drag-drop to sidebar
- ❌ Playlist loading/routing
- ❌ Database integration for custom playlists

### Dual-Tree Selection Handling
- Split sidebar into two separate Treeview widgets (nav_tree and playlists_tree)
- Implemented `_on_nav_select()` and `_on_playlist_select()` handlers
- Handlers temporarily swap `library_tree` reference to maintain backwards compatibility
- Filler items and spacer rows are non-interactive (ignored in selection handlers)

### Files Modified
- `core/gui/library_search.py` - Complete rewrite with dual-tree structure and filler workaround

## Sidebar Background Color Investigation (2026-01-10)

### Issue
The sidebar background is rendering as `#323232` instead of the expected `#202020` from the metro-teal theme. Despite multiple attempts to fix:

1. Changed `left_panel` from `ttk.Frame` to `tk.Frame(bg=THEME_CONFIG['colors']['bg'])` in `core/player/__init__.py`
2. Changed `container` in `LibraryView` from `ttk.Frame` to `tk.Frame(bg=sidebar_bg)` in `core/gui/library_search.py`
3. Added `Sidebar.Treeview` style with borderless layout in `core/theme.py`
4. Set `bg_color=sidebar_bg` on CTkButton to eliminate halo around rounded corners
5. Applied `style='Sidebar.Treeview'` to both nav_tree and playlists_tree

### Current State
The `#323232` background persists. The style changes are not being applied to the container. The source of the wrong color is unclear - it may be:
- PanedWindow sash/background bleeding through
- ttk theme defaults overriding explicit settings on macOS
- Some parent widget not respecting the background color
- CustomTkinter or ttk Treeview drawing its own background layer

### Files Modified (with bug)
- `core/player/__init__.py` - left_panel changed to tk.Frame
- `core/gui/library_search.py` - container changed to tk.Frame, theme colors used
- `core/theme.py` - added Sidebar.Treeview style

### Next Steps
- Debug which widget is actually rendering the `#323232` background
- May need to inspect widget hierarchy at runtime
- Consider if PanedWindow itself needs background configuration
- Check if ttk.Treeview ignores parent background on macOS

## Sidebar Background Fix (2026-01-10)

### Root Cause
On macOS, the ttk 'aqua' theme ignores `fieldbackground` style configurations for Treeview widgets. The Treeview draws a light gray background (`#323232`) in empty space below items, regardless of style settings.

### Failed Approaches
1. **`style.configure('Treeview', fieldbackground=...)`** - Ignored by aqua theme
2. **`root.option_add('*Treeview*fieldBackground', ...)`** - Ignored by aqua theme
3. **Wrapping Treeview in tk.Frame with bg color** - Treeview still draws its own background on top
4. **Using tk.Canvas as background layer** - Complex, caused sizing issues
5. **Using 'clam' theme** - Fixed sidebar but broke scrollbars (rectangular with arrows instead of native pill-shaped)

### Working Solution: Dynamic Filler Items
Keep the default aqua theme for native macOS scrollbars, but fill empty space with dummy items:

1. **nav_tree**: Set `height=3` to match exact number of visible rows (Library, Music, Now Playing)
2. **playlists_tree**: Dynamically calculate and insert filler items to fill all visible space
3. **tag_configure**: Apply `sidebar_item` tag with `background=sidebar_bg` to color all item rows (including fillers)
4. **Resize handling**: Bind to `<Configure>` event to update filler count when widget resizes

Implementation details:
- `_update_filler_items()`: Calculates visible rows based on widget height, adds/removes fillers as needed
- `_on_tree_configure()`: Debounced event handler to trigger filler updates on resize
- Filler items have `('filler', 'sidebar_item')` tags and are ignored in selection handlers
- Item height estimated at 20px with +2 safety margin

### Key Files Modified
- `core/gui/library_search.py` - Dual-tree structure, filler workaround, selection handling

### Visual Result
- ✅ Sidebar: Uniform dark background (#202020) throughout
- ✅ Scrollbar: Native macOS pill-shaped, no arrows
- ✅ No #323232 background visible in empty space
- ✅ Visual spacing between Library and Playlists sections
- ✅ Dynamic playlists (Liked Songs, etc.) are clickable and functional
<!-- SECTION:NOTES:END -->
