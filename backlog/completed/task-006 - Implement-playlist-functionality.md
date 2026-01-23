---
id: task-006
title: Implement playlist functionality
status: Done
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-11 00:11'
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
- [x] #1 Create playlist data structures and storage (playlists + playlist_items tables, PlaylistsManager, FK cascades)
- [x] #2 Add playlist UI components (sidebar restructure with nav tree + divider + pill button + playlists tree, inline rename, context menus, drag-drop to sidebar, reorder within playlist)
- [x] #3 Test playlist functionality and persistence (DB tests for CRUD/ordering/cascades, handler tests for playlist-specific delete behavior, identifier standardization tests)
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

## Phase 1: Database Layer Complete (2026-01-10)

### Identifier Standardization
Fixed `recent_added`/`recent_played` → `recently_added`/`recently_played` throughout codebase:
- core/gui/library_search.py: Sidebar tags
- core/player/ui.py: View routing and logging

### Database Schema
Added two new tables to DB_TABLES (both core/db/__init__.py and core/db.py):
- `playlists`: Stores custom playlists with unique names
- `playlist_items`: Stores playlist tracks with position ordering and FK cascades

### Foreign Key Enforcement
Enabled `PRAGMA foreign_keys = ON` in both:
- core/db/database.py (current facade)
- core/db.py (legacy module)

### PlaylistsManager Implementation
Created core/db/playlists.py with full CRUD and track management:
- CRUD: create_playlist, list_playlists, get_playlist_name, rename_playlist, delete_playlist
- Track Management: add_tracks_to_playlist, remove_tracks_from_playlist, reorder_playlist
- Utilities: get_track_id_by_filepath, generate_unique_name
- Auto-reindexing of positions after removals

### Database Facade Integration
Wired PlaylistsManager into core/db/database.py:
- Instantiated in __init__ as self._playlists
- Added delegation methods for all PlaylistsManager operations
- Updated docstring to include PlaylistsManager

### Comprehensive Test Coverage
Created tests/test_unit_playlists.py with 18 tests (all passing):
- TestPlaylistCRUD: 7 tests for create, list, get, rename, delete
- TestPlaylistTrackManagement: 5 tests for add, remove, reorder
- TestPlaylistCascadeAndConstraints: 1 test for FK cascade
- TestPlaylistUtilities: 4 tests for track_id lookup and unique name generation
- TestPlaylistItemMetadata: 1 test for metadata retrieval

### Commits
- 973cdef: refactor: standardize playlist view identifiers
- 0b8b52a: feat: add custom playlist database layer (task-006 Phase 1)

### Next Steps
Phase 1 complete! The database layer is now ready. Next phases:
- Phase 3: Playlist Loading & Selection (load_custom_playlist, view routing)
- Phase 4: Add to Playlist (context menu integration)
- Phase 5: Drag & Drop (sidebar and internal reorder)
- Phase 6: Delete Behavior (handle_delete for playlist view)
- Phase 7: Tests (handler tests, identifier tests)

Note: Phase 2 (Sidebar UI) was partially completed earlier but needs additional work:
- ✅ UI structure (nav tree, divider, button, playlists tree) - DONE
- ❌ Button functionality (create playlist + inline rename) - TODO
- ❌ Context menus (rename/delete) - TODO
- ❌ Drag-drop support - TODO

## Phase 2: Playlist UI Functionality Complete (2026-01-10)

### LibraryView Enhancements (core/gui/library_search.py)
**Playlist Loading**:
- Load custom playlists from database on startup via `_load_custom_playlists()`
- Map tree item IDs to playlist IDs in `_playlist_items` dict
- Add 'dynamic' and 'custom' tags for playlist type identification

**Playlist Creation**:
- "+ New playlist" button now fully functional
- Generates unique name via `db.generate_unique_name()`
- Creates playlist in database immediately
- Inserts into tree after dynamic playlists (before filler items)
- Automatically enters inline rename mode

**Inline Rename Mode**:
- Entry overlay positioned via `tree.bbox()` for pixel-perfect placement
- Pre-fills with generated unique name, selects all text
- Commit on Enter or FocusOut
- Cancel on Escape (keeps playlist with generated name)
- Validates empty names and duplicate names
- Shows error message for duplicates, keeps editor open for correction
- Dark themed Entry widget (#2B2B2B bg, #FFFFFF fg)

**Context Menus**:
- Right-click on custom playlists shows Rename/Delete menu
- Dynamic playlists ignore right-click (no menu)
- Filler items ignore right-click
- Rename: Re-enters inline rename mode with current name
- Delete: Confirmation dialog + cascade cleanup from database
- If deleted playlist is active, switches to Music view

**Playlist Selection**:
- Custom playlists call `load_custom_playlist(playlist_id)` callback
- Dynamic playlists use existing `on_section_select` routing
- Clear opposite tree selection for UX consistency

### MusicPlayer Integration (core/player/__init__.py)
**New Callbacks**:
- `get_database`: Lambda returning `self.db` for LibraryView database access
- `load_custom_playlist`: Delegates to `library_handler.load_custom_playlist()`
- `on_playlist_deleted`: Switches to Music view if deleted playlist was active

**Methods Added**:
- `load_custom_playlist(playlist_id)`: Delegation to library handler
- `on_playlist_deleted(playlist_id)`: Active view detection and fallback

### PlayerLibraryManager (core/player/library.py)
**New Method: `load_custom_playlist(playlist_id)`**:
- Resets to standard 5-column layout
- Clears view and both mapping dicts (`_item_filepath_map`, `_item_track_id_map`)
- Sets view identifier to `playlist:<id>`
- Fetches playlist items: `(filepath, artist, title, album, track_number, date, track_id)`
- Populates tree with formatted track numbers and metadata
- Maps both filepath and track_id for each item (enables delete and add operations)
- Structured logging with playlist_id and playlist_name
- Status bar update with playlist name and track count

**Mapping Enhancement**:
- Added `_item_track_id_map` dict to track library IDs for playlist operations
- Critical for Phase 6 (delete from playlist only, not library)
- Critical for Phase 4 (add to playlist from selection)

### Features Implemented
✅ Create playlist with auto-unique naming ("New playlist", "New playlist (2)", etc.)
✅ Inline rename with Entry overlay and validation
✅ Delete playlist with confirmation and cascade cleanup
✅ Load and display custom playlists
✅ Context menus (Rename/Delete) on custom playlists only
✅ Playlist selection routing (custom vs dynamic)
✅ Database integration via callbacks
✅ Active playlist deletion handling (fallback to Music view)
✅ Structured logging for all playlist operations

### Technical Improvements
- Import `sqlite3` for IntegrityError handling
- Import `messagebox` for user dialogs
- Added `_rename_entry`, `_rename_item`, `_playlist_items` instance variables
- Right-click bindings for both macOS (Button-2) and Linux/Windows (Button-3)
- Proper cleanup of Entry widget on commit/cancel

### Commits
- 6f60468: feat: complete Phase 2 playlist UI functionality (task-006)

### Status
Phase 2 complete! Custom playlists can now be:
- Created with auto-unique names
- Renamed inline with validation
- Deleted with confirmation
- Loaded and displayed

Next phases:
- Phase 3: Custom selection already working! (loads via `load_custom_playlist`)
- Phase 4: Add to Playlist (context menu integration)
- Phase 5: Drag & Drop (sidebar and internal reorder)
- Phase 6: Delete Behavior (handle_delete for playlist view)
- Phase 7: Tests (handler tests, identifier tests)

## Post-Implementation Improvements Needed (2026-01-10)

After testing the completed implementation, two UX issues were identified:

### 1. No Visual Feedback During Drag-to-Playlist
**Current behavior**: When dragging tracks to sidebar playlists, there's no visual indication that the drop target is valid. Users must:
1. Click and hold track(s)
2. Drag to playlist name (no hover highlight)
3. Drop blindly
4. Check popup message to confirm
5. Navigate to playlist to verify

**Desired behavior**: Add visual feedback during drag operation:
- Highlight playlist row when hovering with dragged tracks
- Change cursor to indicate valid drop target
- Possible implementations:
  - Background color change on hover (e.g., primary color highlight)
  - Border/outline around playlist name
  - Cursor change (e.g., copy cursor with +)

**Implementation approach**:
- Track drag state in QueueView (`_drag_data['dragging']`)
- During drag motion, use `winfo_containing()` to check if cursor is over playlists_tree
- If over custom playlist, highlight that row via tag_configure or direct item configuration
- Clear highlight on drag end or when leaving playlist bounds

### 2. Playlist View Column Sizing and Track Numbers
**Current behavior**: 
- Playlist views use default column widths, ignoring user's music library customizations
- Track number column shows album track numbers (meaningless in playlist context)

**Desired behavior**:
- **Column widths**: Inherit from music library view when loading playlist
  - User's column width preferences in Music view should apply to playlist views
  - Preserves user's workflow/layout preferences
- **Track numbers**: Show playlist position (1, 2, 3...) instead of album track numbers
  - Makes sense in playlist context (reorderable list)
  - Clear visual indicator of playlist order

**Implementation approach**:
- Modify `load_custom_playlist()` in `core/player/library.py`:
  - Load column widths from Music view preferences before populating
  - Apply those widths to playlist view
  - Replace track_num with enumerate index (1-based) when populating tree
- Database consideration: Playlist items already have `position` field for reordering
  - Use position for display, or use enumerate for simpler 1-based numbering

### Files to Modify
**For drag feedback**:
- `core/gui/queue_view.py`: Add hover detection in `on_drag_motion()`
- `core/gui/library_search.py`: Add `highlight_playlist()` and `clear_highlight()` methods
- `core/player/__init__.py`: Wire up highlight callbacks

**For column sizing & track numbers**:
- `core/player/library.py`: Update `load_custom_playlist()` to:
  - Load music view column widths
  - Apply to playlist columns
  - Use enumerate for track numbers instead of album track_num

### Priority
Medium - UX improvements that make the feature more discoverable and intuitive, but functionality is complete.

## UX Improvements Completed (2026-01-11)

### Visual Drag-to-Playlist Feedback
- Added `highlight_playlist_at()` and `clear_playlist_highlight()` methods to LibraryView
- Integrated with QueueView's internal drag system via callbacks
- Playlist rows highlight with primary color when tracks are dragged over them
- Highlight clears automatically on drag release

### Playlist View Column Sizing and Track Numbers
- Updated `load_custom_playlist()` to show 1-based playlist position instead of album track numbers
- Added `_apply_music_view_column_widths()` to inherit user's column width preferences from Music view
- Playlist views now respect the user's customized column layout

### Files Modified
- `core/gui/library_search.py`: Added highlight/clear methods for drag feedback
- `core/gui/queue_view.py`: Added highlight callbacks to drag motion/release handlers
- `core/player/__init__.py`: Wired up highlight_playlist_at and clear_playlist_highlight callbacks
- `core/player/library.py`: Updated load_custom_playlist for position numbers and column widths

### Tests
- All 547 unit/property tests pass
- 25 playlist-specific tests (DB, identifiers, handler) all pass
<!-- SECTION:NOTES:END -->
