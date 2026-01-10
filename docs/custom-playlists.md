# Custom Playlists Implementation Plan

This document describes the implementation plan for user-created custom playlists (backlog task-006, acceptance criteria #1, #5, #6).

## Overview

Custom playlists allow users to create, manage, and organize their own track collections. This feature complements the existing dynamic playlists (Liked Songs, Recently Added, Recently Played, Top 25 Most Played) with user-defined collections.

## Requirements Summary

### Core Features
- Create/rename/delete custom playlists
- Add tracks to playlists (no duplicates allowed)
- Remove tracks from playlists (without deleting from library)
- Reorder tracks within a playlist via drag-and-drop
- Persist playlists and track order across restarts

### UI Requirements (YouTube Music-inspired)
- Left sidebar restructured:
  1. Top navigation tree (Library → Music / Now Playing)
  2. Horizontal divider line (theme-matching)
  3. Pill-shaped "+ New playlist" button
  4. Playlists section: dynamic playlists first, then custom playlists
- Right-click on custom playlist name: Rename / Delete
- Right-click on tracks: "Add to playlist" submenu with all playlists
- Delete key in playlist view removes from playlist only (not library)

### Playlist Creation
- Default name: "New playlist"
- Auto-suffix if exists: "New playlist (2)", "New playlist (3)", etc.
- Dynamic playlists are non-editable (no rename/delete, no right-click menu)

---

## Implementation Details

### A. Database Schema (AC #1)

Add two new tables to `DB_TABLES` in both:
- `core/db/__init__.py`
- `core/db.py`

#### Table: `playlists`
```sql
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Table: `playlist_items`
```sql
CREATE TABLE IF NOT EXISTS playlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(playlist_id, track_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES library(id) ON DELETE CASCADE
)
```

**Notes:**
- `UNIQUE(playlist_id, track_id)` enforces no duplicate tracks per playlist
- Foreign key cascades ensure cleanup when playlists or library tracks are deleted
- `position` column enables stable ordering and drag-reorder persistence

#### Enable Foreign Keys
SQLite requires explicit enabling of foreign key enforcement. Add to `core/db/database.py` after connection:
```python
self.db_cursor.execute("PRAGMA foreign_keys = ON")
```

---

### B. Database Manager (AC #1)

Create new file: `core/db/playlists.py`

#### Class: `PlaylistsManager`

```python
class PlaylistsManager:
    def __init__(self, db_conn, db_cursor):
        self.db_conn = db_conn
        self.db_cursor = db_cursor

    def create_playlist(self, name: str) -> int:
        """Create a new playlist. Returns playlist ID."""

    def list_playlists(self) -> list[tuple[int, str]]:
        """Return list of (id, name) for all custom playlists."""

    def rename_playlist(self, playlist_id: int, new_name: str) -> bool:
        """Rename a playlist. Returns success."""

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist and all its items. Returns success."""

    def get_playlist_items(self, playlist_id: int) -> list[tuple]:
        """Get playlist tracks joined with library metadata, ordered by position.
        Returns: [(filepath, artist, title, album, track_number, date, position), ...]
        """

    def add_tracks_to_playlist(self, playlist_id: int, track_ids: list[int]) -> int:
        """Add tracks to playlist. Ignores duplicates. Returns count added."""

    def remove_tracks_from_playlist(self, playlist_id: int, track_ids: list[int]) -> int:
        """Remove tracks from playlist. Returns count removed."""

    def reorder_playlist(self, playlist_id: int, ordered_track_ids: list[int]) -> bool:
        """Update positions based on new order. Returns success."""

    def get_track_id_by_filepath(self, filepath: str) -> int | None:
        """Resolve filepath to library.id for playlist operations."""

    def generate_unique_name(self, base_name: str = "New playlist") -> str:
        """Generate unique playlist name with auto-suffix if needed."""
```

#### Wire into Database Facade
Update `core/db/database.py`:
1. Import `PlaylistsManager`
2. Instantiate in `__init__`: `self._playlists = PlaylistsManager(self.db_conn, self.db_cursor)`
3. Add delegation methods for all `PlaylistsManager` operations

---

### C. Sidebar UI Restructure (AC #5)

Modify: `core/gui/library_search.py`

#### New Layout Structure
Replace single `library_tree` with vertical stack:

```
┌─────────────────────────┐
│  Navigation Tree        │  ← Library / Music / Now Playing
│  (ttk.Treeview)         │
├─────────────────────────┤
│  ─────────────────────  │  ← 1px divider (theme color)
├─────────────────────────┤
│  [+ New playlist]       │  ← CTkButton, pill-shaped
├─────────────────────────┤
│  Playlists Tree         │  ← Dynamic + Custom playlists
│  (ttk.Treeview)         │
│  - Liked Songs          │
│  - Recently Added       │
│  - Recently Played      │
│  - Top 25 Most Played   │
│  - My Playlist 1        │  ← Custom (right-click enabled)
│  - My Playlist 2        │
└─────────────────────────┘
```

#### Component Details

**Navigation Tree**
- Contains: Library (parent) → Music, Now Playing
- Selection triggers existing view loading

**Divider**
- `ttk.Separator` or `tk.Frame` with height=1
- Background color from `THEME_CONFIG['colors']['border']` or similar

**New Playlist Button**
- `customtkinter.CTkButton` with:
  - Text: "+ New playlist"
  - Corner radius: high (pill shape)
  - Background: slightly lighter than sidebar bg
  - Hover effect
- On click: prompt for name (prefilled "New playlist" with auto-suffix)

**Playlists Tree**
- Single flat list (no parent nodes)
- Dynamic playlists first (tagged `dynamic`)
- Custom playlists after (tagged `custom`)
- Selection triggers playlist loading
- Right-click on `custom` items shows Rename/Delete menu
- Right-click on `dynamic` items: disabled/no menu

#### Callbacks Required
```python
callbacks = {
    'on_nav_select': ...,           # Library/Music/Now Playing selection
    'on_playlist_select': ...,      # Playlist selection (dynamic or custom)
    'on_new_playlist': ...,         # Create new playlist
    'on_playlist_rename': ...,      # Rename custom playlist
    'on_playlist_delete': ...,      # Delete custom playlist
}
```

---

### D. Loading Playlist Contents (AC #5)

Modify: `core/player/library.py`

#### New Method: `load_custom_playlist(playlist_id: int)`
```python
def load_custom_playlist(self, playlist_id: int):
    """Load and display a custom playlist's tracks."""
    # Clear current view
    # Set queue_view.current_view = f"playlist:{playlist_id}"
    # Configure standard 5 columns
    # Fetch rows from db.get_playlist_items(playlist_id)
    # Populate treeview with rows
    # Maintain _item_filepath_map and new _item_track_id_map
```

#### View Identification
Use `queue_view.current_view` string to identify active view:
- `"music"` - Library
- `"now_playing"` - Queue
- `"liked_songs"` - Liked Songs
- `"recently_added"` - Recently Added
- `"recently_played"` - Recently Played
- `"top_played"` - Top 25
- `"playlist:<id>"` - Custom playlist (e.g., `"playlist:3"`)

---

### E. Add to Playlist (AC #5)

#### Main List Context Menu
Modify: `core/gui/queue_view.py`

Add submenu to `setup_context_menu()`:
```python
self.add_to_playlist_menu = tk.Menu(self.context_menu, tearoff=0)
self.context_menu.add_cascade(label="Add to playlist", menu=self.add_to_playlist_menu)
```

Populate submenu dynamically in `show_context_menu()`:
```python
def show_context_menu(self, event):
    # ... existing selection logic ...
    
    # Refresh playlist submenu
    self.add_to_playlist_menu.delete(0, 'end')
    playlists = self.callbacks.get('get_playlists', lambda: [])()
    for playlist_id, name in playlists:
        self.add_to_playlist_menu.add_command(
            label=name,
            command=lambda pid=playlist_id: self.on_add_to_playlist(pid)
        )
    
    # Show menu
    self.context_menu.tk_popup(event.x_root, event.y_root)
```

#### Now Playing Context Menu
Modify: `core/now_playing/view.py`

Replace disabled "Save to Playlist" with enabled submenu:
```python
self.add_to_playlist_menu = tk.Menu(self.context_menu, tearoff=0)
self.context_menu.add_cascade(label="Add to playlist", menu=self.add_to_playlist_menu)
```

Populate dynamically when showing menu, similar to main list.

---

### F. Drag and Drop (AC #5)

#### Drag from Main List to Sidebar Playlist
Implement internal drag tracking in `core/gui/queue_view.py`:

```python
def setup_internal_drag(self):
    self._drag_data = {'items': [], 'dragging': False, 'start_x': 0, 'start_y': 0}
    self.queue.bind('<ButtonPress-1>', self._on_drag_start)
    self.queue.bind('<B1-Motion>', self._on_drag_motion)
    self.queue.bind('<ButtonRelease-1>', self._on_drag_end)

def _on_drag_start(self, event):
    self._drag_data['items'] = list(self.queue.selection())
    self._drag_data['start_x'] = event.x
    self._drag_data['start_y'] = event.y
    self._drag_data['dragging'] = False

def _on_drag_motion(self, event):
    if not self._drag_data['items']:
        return
    # Check if moved beyond threshold (e.g., 5 pixels)
    dx = abs(event.x - self._drag_data['start_x'])
    dy = abs(event.y - self._drag_data['start_y'])
    if dx > 5 or dy > 5:
        self._drag_data['dragging'] = True

def _on_drag_end(self, event):
    if not self._drag_data['dragging']:
        self._drag_data = {'items': [], 'dragging': False, 'start_x': 0, 'start_y': 0}
        return
    
    # Find widget under cursor
    widget = self.queue.winfo_containing(event.x_root, event.y_root)
    
    # Check if it's the playlist tree and identify target playlist
    if self.callbacks.get('on_drag_to_playlist'):
        playlist_id = self.callbacks['on_drag_to_playlist'](widget, event.x_root, event.y_root)
        if playlist_id:
            self.callbacks['add_tracks_to_playlist'](playlist_id, self._drag_data['items'])
    
    self._drag_data = {'items': [], 'dragging': False, 'start_x': 0, 'start_y': 0}
```

#### Reorder Within Playlist
When `current_view.startswith("playlist:")`:

```python
def _on_drag_end(self, event):
    if self.current_view.startswith("playlist:") and self._drag_data['dragging']:
        # Check if drop is within the same treeview
        widget = self.queue.winfo_containing(event.x_root, event.y_root)
        if widget == self.queue:
            # Get drop target row
            target_item = self.queue.identify_row(event.y)
            if target_item and target_item not in self._drag_data['items']:
                # Reorder items
                self._reorder_items(self._drag_data['items'], target_item)
```

Persist reorder via callback to `db.reorder_playlist()`.

---

### G. Delete from Playlist (AC #5)

Modify: `core/player/handlers.py` → `handle_delete()`

```python
def handle_delete(self, event):
    current_view = self.queue_view.current_view
    
    if current_view.startswith("playlist:"):
        # Extract playlist_id
        playlist_id = int(current_view.split(":")[1])
        
        # Get selected track IDs
        selected_items = self.queue_view.queue.selection()
        track_ids = [self._item_track_id_map.get(item) for item in selected_items]
        track_ids = [tid for tid in track_ids if tid is not None]
        
        # Remove from playlist only (not library)
        self.db.remove_tracks_from_playlist(playlist_id, track_ids)
        
        # Remove from UI
        for item in selected_items:
            self.queue_view.queue.delete(item)
        
        return "break"
    
    # ... existing delete logic for other views ...
```

#### Context Menu in Playlist View
When in playlist view, show:
- "Remove from playlist" (removes from playlist only)
- "Remove from library" (existing destructive action)

---

### H. Rename/Delete Playlist (AC #5)

In sidebar playlist tree, bind right-click for custom playlists:

```python
def show_playlist_context_menu(self, event):
    item = self.playlists_tree.identify_row(event.y)
    if not item:
        return
    
    tags = self.playlists_tree.item(item)['tags']
    if 'custom' not in tags:
        return  # Dynamic playlists: no menu
    
    playlist_id = self._get_playlist_id_from_item(item)
    
    menu = tk.Menu(self.playlists_tree, tearoff=0)
    menu.add_command(label="Rename", command=lambda: self.rename_playlist(playlist_id))
    menu.add_command(label="Delete", command=lambda: self.delete_playlist(playlist_id))
    menu.tk_popup(event.x_root, event.y_root)

def rename_playlist(self, playlist_id):
    current_name = self.db.get_playlist_name(playlist_id)
    new_name = simpledialog.askstring("Rename Playlist", "New name:", initialvalue=current_name)
    if new_name and new_name != current_name:
        self.db.rename_playlist(playlist_id, new_name)
        self.refresh_playlists_tree()

def delete_playlist(self, playlist_id):
    if messagebox.askyesno("Delete Playlist", "Are you sure you want to delete this playlist?"):
        self.db.delete_playlist(playlist_id)
        self.refresh_playlists_tree()
        # If deleted playlist was active, switch to Music view
        if self.queue_view.current_view == f"playlist:{playlist_id}":
            self.load_library()
```

---

## Testing Plan (AC #6)

### Unit Tests: Database Layer
New file: `tests/test_unit_playlists.py`

```python
class TestPlaylistsManager:
    def test_create_playlist(self, in_memory_db):
        """Test creating a new playlist."""
    
    def test_create_playlist_unique_name(self, in_memory_db):
        """Test that duplicate names are rejected."""
    
    def test_generate_unique_name(self, in_memory_db):
        """Test auto-suffix generation for duplicate names."""
    
    def test_list_playlists(self, in_memory_db):
        """Test listing all playlists."""
    
    def test_rename_playlist(self, in_memory_db):
        """Test renaming a playlist."""
    
    def test_delete_playlist(self, in_memory_db):
        """Test deleting a playlist removes items too."""
    
    def test_add_tracks_to_playlist(self, in_memory_db):
        """Test adding tracks to a playlist."""
    
    def test_add_duplicate_track_ignored(self, in_memory_db):
        """Test that adding same track twice is idempotent."""
    
    def test_remove_tracks_from_playlist(self, in_memory_db):
        """Test removing tracks from playlist (not library)."""
    
    def test_get_playlist_items_ordered(self, in_memory_db):
        """Test that items are returned in position order."""
    
    def test_reorder_playlist(self, in_memory_db):
        """Test reordering tracks persists correctly."""
    
    def test_library_delete_cascades_to_playlist(self, in_memory_db):
        """Test that deleting from library removes from playlists."""
```

### Handler Tests
Extend existing test patterns:

```python
class TestPlaylistDeleteBehavior:
    def test_delete_in_playlist_view_removes_from_playlist_only(self):
        """Verify delete key in playlist view doesn't delete from library."""
    
    def test_delete_in_library_view_deletes_from_library(self):
        """Verify delete key in library view still deletes from library."""
```

---

## Implementation Order

Recommended atomic commit sequence:

1. **Schema**: Add `playlists` and `playlist_items` tables to `DB_TABLES`
2. **Foreign keys**: Enable `PRAGMA foreign_keys = ON` in database connection
3. **PlaylistsManager**: Create `core/db/playlists.py` with all methods
4. **Facade wiring**: Add delegation methods to `core/db/database.py`
5. **DB tests**: Add `tests/test_unit_playlists.py`
6. **Sidebar restructure**: Rework `LibraryView` layout with divider and button
7. **Playlist loading**: Add `load_custom_playlist()` to `PlayerLibraryManager`
8. **Selection routing**: Update `on_section_select` for new sidebar structure
9. **Add to playlist menu**: Implement submenu in main list context menu
10. **Add to playlist (Now Playing)**: Implement submenu in Now Playing context menu
11. **Drag to sidebar**: Implement internal drag from main list to playlist
12. **Reorder within playlist**: Implement drag-reorder in playlist view
13. **Delete from playlist**: Update `handle_delete()` for playlist view
14. **Rename/delete playlist**: Implement right-click menu on playlist names
15. **Handler tests**: Add tests for delete behavior in playlist view

---

## Files Modified

| File | Changes |
|------|---------|
| `core/db/__init__.py` | Add `playlists` and `playlist_items` to `DB_TABLES` |
| `core/db.py` | Add tables to `DB_TABLES` (duplicate schema location) |
| `core/db/playlists.py` | **New file**: `PlaylistsManager` class |
| `core/db/database.py` | Enable foreign keys, instantiate and delegate to `PlaylistsManager` |
| `core/gui/library_search.py` | Restructure `LibraryView` with divider, button, split trees |
| `core/player/library.py` | Add `load_custom_playlist()` method |
| `core/player/ui.py` | Update `on_section_select()` for new sidebar structure |
| `core/gui/queue_view.py` | Add "Add to playlist" submenu, internal drag support |
| `core/now_playing/view.py` | Replace disabled stub with working submenu |
| `core/player/handlers.py` | Update `handle_delete()` for playlist view behavior |
| `tests/test_unit_playlists.py` | **New file**: Playlist DB and handler tests |

---

## Related Documentation

- [Python Architecture](python-architecture.md) - Overall system design
- [GUI Implementation](tkinter-gui.md) - Tkinter UI patterns
- [Theming System](theming.md) - Theme colors for divider styling
