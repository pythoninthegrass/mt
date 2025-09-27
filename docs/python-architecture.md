# Python Architecture

## Overview

The MT music player is built using a modular Python architecture centered around the `core/` package, with clear separation of concerns between data management, user interface, audio playback, and system integration.

## Core Architecture

### Entry Point (`main.py`)

The application entry point follows a structured initialization sequence:

1. **Logging Setup** - Eliot-based structured logging initialization
2. **Window Creation** - TkinterDnD-enabled root window with icon setup
3. **Theme Application** - Style configuration before component creation
4. **Player Instantiation** - Main `MusicPlayer` class initialization
5. **Component Setup** - All subsystem initialization and connection
6. **Event Loop** - Tkinter main loop with error handling

### Central Orchestrator (`core/player.py`)

The `MusicPlayer` class serves as the central orchestrator, managing:

- **Window Management**: Size, position, and platform-specific styling (macOS integration)
- **Component Lifecycle**: Initialization order and dependency injection
- **UI Layout**: PanedWindow-based two-panel design (library + content)
- **Event Coordination**: User interactions, media keys, and file system events
- **State Persistence**: Window preferences and application settings

#### Key Components Integration

```python
# Core subsystems initialized in setup_components()
self.db = MusicDatabase()                 # SQLite data layer
self.queue_manager = QueueManager()       # Queue operations
self.library_manager = LibraryManager()   # Library scanning/management
self.player_core = PlayerCore()           # Audio playback engine
```

#### UI Component Architecture

```python
# UI components with callback-based communication
self.library_view = LibraryView()         # Left panel library browser
self.queue_view = QueueView()             # Right panel queue display
self.progress_bar = ProgressBar()         # Bottom progress/controls
```

## Data Layer (`core/db.py`)

### Database Design

SQLite-based persistence with two main tables:

- **`library`**: Music file metadata and indexing
  - File paths, metadata (artist, album, title, duration)
  - Content hashing for deduplication
  - Last modified timestamps for incremental scanning

- **`queue`**: Current playback queue state
  - Track references, position, play order
  - Shuffle state and loop configuration
  - Session persistence across app restarts

### Database Operations

The `MusicDatabase` class provides:

- **Schema Management**: Automatic table creation and migration
- **Query Interface**: High-level operations for library and queue
- **Preference Storage**: JSON-serialized configuration data
- **Transaction Safety**: Atomic operations for data consistency

## Library Management (`core/library.py`)

### Scanning Engine

The `LibraryManager` handles:

- **Directory Traversal**: Configurable depth limits and exclusion patterns
- **Metadata Extraction**: Mutagen-based tag reading with fallbacks
- **Deduplication**: File content hashing to prevent duplicates
- **Incremental Updates**: Modified time tracking for efficient rescans

### Performance Optimizations

- **Zig Integration**: High-performance directory scanning via `core/_scan.py`
- **Batch Operations**: Bulk database insertions for large libraries
- **Background Processing**: Non-blocking UI during scan operations

## Queue System (`core/queue.py`)

### Queue Management

The `QueueManager` provides:

- **Playback Order**: Linear and shuffle modes with state persistence
- **Dynamic Operations**: Add, remove, reorder queue entries
- **Position Tracking**: Current song index and playback history
- **Loop Modes**: Single track and full queue repeat functionality

### UI Integration

- **Tree View**: Hierarchical display with drag-and-drop support
- **Real-time Updates**: Queue changes reflected immediately in UI
- **Context Actions**: Right-click operations for queue manipulation

## Audio Engine (`core/controls.py`)

### VLC Integration

The `PlayerCore` class wraps VLC functionality:

- **Media Player**: VLC instance management and event handling
- **Playback Control**: Play, pause, stop, seek operations
- **Volume Management**: Audio level control with UI synchronization
- **State Tracking**: Current position, duration, and playback status

### Threading Considerations

- **Background Updates**: Progress tracking in separate thread context
- **Thread Safety**: UI updates via `window.after()` for main thread execution
- **Event Handling**: VLC event callbacks with proper synchronization

## User Interface (`core/gui.py`)

### Component Structure

- **LibraryView**: Left panel with collapsible sections for different library views
- **QueueView**: Right panel tree display of current playback queue
- **PlayerControls**: Bottom panel transport controls and volume
- **ProgressBar**: Custom canvas-based progress indication with seeking

### Theming System (`core/theme.py`)

- **Style Configuration**: ttk.Style-based theming with JSON configuration
- **Platform Integration**: macOS-specific appearance settings
- **Dynamic Updates**: Runtime theme switching capability

## Configuration Management (`config.py`)

### Environment-Based Configuration

Uses `python-decouple` for environment variable integration:

- **Development Settings**: Hot reload, logging levels, debug modes
- **Path Configuration**: Database location, scan directories
- **UI Preferences**: Window size, panel positions, themes
- **Audio Settings**: Format support, output device selection

### Validation and Defaults

- **Input Sanitization**: Configuration value validation and cleanup
- **Fallback Values**: Sensible defaults for missing configuration
- **Type Coercion**: Automatic type conversion for environment variables

## Logging System (`core/logging.py`)

### Structured Logging

Eliot-based logging architecture:

- **Action Tracking**: Hierarchical operation logging with context
- **Error Reporting**: Exception capture with full stack traces
- **Performance Monitoring**: Operation timing and resource usage
- **Debug Support**: Development-time detailed event logging

### Log Categories

- **Application Lifecycle**: Startup, shutdown, component initialization
- **User Actions**: UI interactions, file operations, playback controls
- **System Events**: File system changes, database operations
- **Error Conditions**: Exceptions, validation failures, resource issues

## Platform Integration

### macOS Specific Features

- **Media Key Support**: Native play/pause/next/previous key handling
- **Window Styling**: Document-style windows with dark mode support
- **Drag and Drop**: Native file dropping with TkinterDnD2
- **App Menu Integration**: Standard macOS application menu behavior

### Cross-Platform Considerations

- **Conditional Imports**: Platform-specific feature detection
- **Fallback Behavior**: Graceful degradation on unsupported platforms
- **Path Handling**: Cross-platform file system operations

## Development Tools

### Hot Reload System (`utils/reload.py`)

- **File Watching**: Automatic application restart on code changes
- **Configuration Updates**: Dynamic theme and setting reloads
- **Development Workflow**: Seamless iteration without manual restarts

### Testing Infrastructure

- **pytest Integration**: Comprehensive test suite with fixtures
- **Mock Components**: Isolated testing of individual modules
- **Integration Tests**: End-to-end workflow validation

## Error Handling and Resilience

### Exception Management

- **Graceful Degradation**: Non-critical feature failures don't crash app
- **User Feedback**: Clear error messages for user-actionable issues
- **Recovery Mechanisms**: Automatic retry for transient failures
- **State Cleanup**: Proper resource cleanup on error conditions

### Data Integrity

- **Database Transactions**: Atomic operations prevent corruption
- **File Validation**: Media file integrity checking before operations
- **Backup Strategies**: Configuration and preference preservation
- **Migration Support**: Schema updates without data loss

## Future Architecture Considerations

### Web Migration Readiness

Current architecture decisions supporting future web migration:

- **Separation of Concerns**: Clear API boundaries between components
- **Data Layer Abstraction**: Database operations ready for HTTP API conversion
- **State Management**: Centralized state suitable for client-server architecture
- **Modular Design**: Components can be adapted to web service endpoints
