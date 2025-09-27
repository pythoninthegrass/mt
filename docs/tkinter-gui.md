# Tkinter GUI Implementation

## Overview

MT music player uses a custom Tkinter-based user interface built on the `tkinter.ttk` framework with TkinterDnD2 for drag-and-drop support. The GUI follows a modular component-based architecture with careful attention to platform integration, particularly macOS.

## Architecture Overview

### Window Hierarchy

```
Root Window (TkinterDnD.Tk)
├── Main Container (ttk.PanedWindow, horizontal)
│   ├── Left Panel (ttk.Frame) - Library Views
│   │   └── LibraryView Component
│   └── Right Panel (ttk.Frame) - Queue Display
│       └── QueueView Component
└── Progress Frame (ttk.Frame) - Bottom Controls
    ├── Progress Canvas (tk.Canvas)
    ├── PlayerControls Component
    ├── ProgressControl Component
    └── VolumeControl Component
```

## Core GUI Components (`core/gui.py`)

### LibraryView Component

**Purpose**: Left panel navigation for music library sections

**Implementation**:
```python
class LibraryView:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.setup_library_view()
```

**Features**:
- **Tree Structure**: ttk.Treeview with expandable sections
- **Dynamic Content**: Sections for Artists, Albums, Genres, Recently Added
- **Minimum Width Calculation**: Auto-sizing based on content
- **Selection Callbacks**: Event-driven communication with main application

**Sections**:
- All Music
- Recently Added 
- Recently Played
- Artists (expandable tree)
- Albums (expandable tree)
- Genres (expandable tree)

### QueueView Component

**Purpose**: Right panel display of current playback queue

**Implementation**:
```python
class QueueView:
    def __init__(self, parent, callbacks):
        self.queue = ttk.Treeview(
            columns=('track', 'title', 'artist', 'album', 'year'),
            show='headings'
        )
```

**Features**:
- **Multi-Column Display**: Track number, title, artist, album, year
- **Drag-and-Drop Support**: TkinterDnD2 integration for reordering
- **Extended Selection**: Multiple track selection with Cmd/Ctrl+A
- **Persistent Column Widths**: Database-stored user preferences
- **Context Operations**: Double-click play, Delete key removal
- **Alternating Row Colors**: Visual distinction with theme integration

**Column Management**:
- **Dynamic Resizing**: User-adjustable column widths
- **Preference Persistence**: Column widths saved to database
- **Minimum Width Constraints**: Prevents columns from becoming unusable
- **Auto-restore**: Saved preferences applied on application startup

### PlayerControls Component

**Purpose**: Transport controls embedded in progress canvas

**Design Philosophy**:
- **Canvas-based**: Direct drawing on tk.Canvas for precise positioning
- **Event-driven**: Callback-based communication pattern
- **Responsive Layout**: Dynamic positioning based on window size
- **Visual Feedback**: Hover effects and state indication

**Control Groups**:

#### Playback Controls (Left Side)
- **Previous Track**: `◀◀` symbol with click handler
- **Play/Pause Toggle**: `▶` / `⏸` dynamic symbol switching  
- **Next Track**: `▶▶` symbol with click handler

#### Utility Controls (Right Side)
- **Loop Toggle**: `↻` symbol with active state coloring
- **Shuffle Toggle**: `🔀` symbol with active state indication
- **Add Files**: `+` symbol for library addition

**Implementation Details**:
```python
def setup_playback_controls(self):
    for action, symbol in [
        ('previous', BUTTON_SYMBOLS['prev']),
        ('play', BUTTON_SYMBOLS['play']),
        ('next', BUTTON_SYMBOLS['next']),
    ]:
        button = tk.Label(self.canvas, text=symbol, ...)
        button.bind('<Button-1>', lambda e, a=action: self.callbacks[a]())
```

### ProgressBar Component

**Purpose**: Custom progress visualization and seeking control

**Architecture**:
- **Canvas-based Rendering**: Precise control over visual elements
- **Interactive Elements**: Click-to-seek and drag-to-scrub
- **Multi-component**: Progress line, position circle, time display
- **Thread-safe Updates**: Proper main thread scheduling

**Visual Elements**:

#### Progress Line
- **Background Line**: Full track duration representation
- **Progress Line**: Current position indicator
- **Interactive Hitbox**: Larger clickable area for user interaction

#### Position Circle
- **Visual Indicator**: Current playback position marker
- **Drag Handle**: Mouse interaction for scrubbing
- **Hover Effects**: Visual feedback during interaction

#### Time Display
- **Current/Total Time**: "MM:SS / MM:SS" format
- **Dynamic Updates**: Real-time progress reflection
- **Font Consistency**: Theme-integrated typography

#### Track Information
- **Current Track Details**: Artist - Title display
- **Dynamic Content**: Updates with queue changes
- **Layout Aware**: Positioned to avoid control overlap

**Interaction Handling**:
```python
def click_progress(self, event):
    # Calculate position based on click location
    progress_percentage = (event.x - self.start_x) / self.line_width
    self.callbacks['click_progress'](progress_percentage)

def start_drag(self, event):
    self.dragging = True
    self.callbacks['start_drag']()
```

## Progress Control System (`core/progress.py`)

### ProgressControl Class

**Separation of Concerns**: Dedicated component for progress visualization

**Responsibilities**:
- **Visual Rendering**: Canvas drawing operations
- **Interaction Handling**: Mouse events and position calculation
- **State Management**: Drag state and position tracking
- **Layout Management**: Responsive positioning and sizing

**Key Methods**:
- `draw_progress_line()`: Renders background and progress lines
- `update_progress()`: Updates position based on playback state
- `handle_mouse_events()`: Processes user interaction
- `calculate_position()`: Converts coordinates to playback position

## Volume Control System (`core/volume.py`)

### VolumeControl Class

**Purpose**: Audio level control with visual feedback

**Components**:
- **Volume Icon**: Speaker symbol with visual state indication
- **Volume Slider**: Horizontal line with draggable control
- **Volume Circle**: Position indicator and drag handle
- **Background/Foreground Lines**: Visual progress representation

**Features**:
- **Interactive Slider**: Click and drag volume adjustment
- **Visual Feedback**: Icon changes based on volume level (mute, low, high)
- **Precise Control**: Fine-grained volume adjustment
- **State Persistence**: Volume level maintained across sessions

**Implementation Pattern**:
```python
class VolumeControl:
    def setup_volume_control(self, x_start, slider_length):
        self.create_volume_icon()
        self.create_volume_slider()
        self.bind_volume_events()
        
    def update_volume_display(self, volume):
        # Update icon based on volume level
        # Update slider position
        # Update visual feedback
```

## Platform Integration

### macOS Specific Features

**Window Styling**:
```python
# Document style with dark appearance
self.window.tk.call('::tk::unsupported::MacWindowStyle', 
                   'style', self.window._w, 'document')
self.window.tk.call('::tk::unsupported::MacWindowStyle', 
                   'appearance', self.window._w, 'dark')
```

**Application Menu Integration**:
```python
# Standard macOS quit behavior
self.window.createcommand('tk::mac::Quit', self.window.destroy)
```

**Media Key Support**: Integration with `utils/mediakeys.py` for native media key handling

### Drag and Drop Integration

**TkinterDnD2 Setup**:
```python
from tkinterdnd2 import TkinterDnD, DND_FILES

root = TkinterDnD.Tk()  # Enhanced root with DnD support

# Queue view drop target
self.queue.drop_target_register('DND_Files')
self.queue.dnd_bind('<<Drop>>', self.callbacks['handle_drop'])
```

**Supported Operations**:
- **File Drops**: Add audio files to queue or library
- **Queue Reordering**: Drag tracks within queue for reordering
- **Directory Drops**: Recursive audio file discovery and addition

## Layout and Responsive Design

### PanedWindow Layout

**Horizontal Split**: Library (left) and Queue (right) panels

**Advantages**:
- **User Resizable**: Draggable splitter between panels
- **Proportional Scaling**: Weight-based expansion behavior
- **Preference Persistence**: Splitter position saved and restored

**Configuration**:
```python
self.main_container = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
self.main_container.add(self.left_panel, weight=0)   # Fixed size
self.main_container.add(self.right_panel, weight=1)  # Expandable
```

### Responsive Progress Bar

**Dynamic Sizing**: Canvas responds to window width changes

**Element Positioning**:
- **Controls**: Fixed positions relative to canvas edges
- **Progress Line**: Dynamic width based on available space
- **Volume Control**: Positioned between progress and controls

**Resize Handling**:
```python
def on_resize(self, event=None):
    # Recalculate all element positions
    # Update volume control placement
    # Redraw progress elements
    self.setup_volume_control()
    self.progress_control.redraw()
```

## State Management and Persistence

### UI Preferences

**Database Storage**: SQLite storage of user interface preferences

**Persisted Settings**:
- **Window Size and Position**: Geometry restoration
- **Panel Split Ratio**: PanedWindow sash position  
- **Column Widths**: QueueView column sizing
- **Volume Level**: Audio output level

**Preference Loading**:
```python
def load_ui_preferences(self):
    saved_size = self.db.get_window_size()
    saved_position = self.db.get_window_position()
    sash_position = self.db.get_sash_position()
    column_widths = self.db.get_queue_column_widths()
```

### Event-Driven Updates

**Callback Architecture**: Loose coupling between components

**Communication Pattern**:
```python
callbacks = {
    'play_selected': self.play_selected_song,
    'handle_delete': self.remove_selected_songs,
    'save_column_widths': self.save_queue_column_widths,
    'volume_change': self.player_core.set_volume,
}
```

## Theme Integration

### Style Configuration

**ttk.Style Integration**: Consistent theming across components

**Theme Application**:
- **Colors**: Centralized color scheme from `themes.json`
- **Fonts**: Typography consistency across all text elements
- **Widget Styles**: Custom ttk style definitions

**Component Theming**:
```python
# Treeview styling
self.queue.tag_configure('evenrow', background=THEME_CONFIG['colors']['bg'])
self.queue.tag_configure('oddrow', background=THEME_CONFIG['colors']['row_alt'])

# Custom control styling
button = tk.Label(
    fg=THEME_CONFIG['colors']['fg'],
    bg=THEME_CONFIG['colors']['bg'],
    font=BUTTON_STYLE['font']
)
```

## Error Handling and Resilience

### Graceful Degradation

**Component Failure Isolation**: Individual component failures don't crash application

**Error Recovery**:
- **Preference Loading**: Fallback to defaults on corruption
- **Column Sizing**: Minimum width enforcement
- **Event Handling**: Exception isolation in callbacks

### Threading Considerations

**Main Thread Safety**: All UI updates performed on main thread

**Thread-Safe Patterns**:
```python
# Safe UI updates from background threads
self.window.after(0, lambda: self.update_progress_display(position))
```

## Accessibility and Usability

### Keyboard Support

**Navigation Shortcuts**:
- **Cmd/Ctrl+A**: Select all queue items
- **Delete/Backspace**: Remove selected queue items
- **Space**: Play/pause toggle (via media keys)
- **Arrow Keys**: Queue navigation

### Visual Feedback

**Interactive Elements**: Hover effects and state indication
**Progress Indication**: Clear visual feedback for all operations
**Error States**: Visual indication of error conditions

## Performance Optimizations

### Rendering Efficiency

**Lazy Updates**: Only redraw changed elements
**Event Debouncing**: Rate-limited resize operations
**Minimal Redraws**: Targeted canvas updates rather than full refreshes

### Memory Management

**Component Cleanup**: Proper widget destruction on application exit
**Event Unbinding**: Preventing memory leaks from event handlers
**Resource Management**: Image and font resource cleanup

This GUI implementation provides a rich, responsive user experience while maintaining cross-platform compatibility and native platform integration where available.