# AGENTS.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

MT is a desktop music player designed for large music collections, built with Python and Tkinter. It uses VLC for audio playback and supports drag-and-drop functionality.

## macOS-Specific Environment Setup

On macOS, the application requires specific environment variables to run correctly due to Tcl/Tk dependencies:

```bash
export TCL_LIBRARY=/opt/homebrew/opt/tcl-tk/lib/tcl8.6
export TK_LIBRARY=/opt/homebrew/opt/tcl-tk/lib/tk8.6
```

The project includes a `run.sh` wrapper script that sets these automatically.

## Common Development Commands

### Running the Application
```bash
# Using the wrapper script (recommended on macOS)
./run.sh

# Or directly with environment variables
TCL_LIBRARY=/opt/homebrew/opt/tcl-tk/lib/tcl8.6 TK_LIBRARY=/opt/homebrew/opt/tcl-tk/lib/tk8.6 uv run main.py

# Standard run (may fail on macOS without env vars)
uv run main.py
```

### Development Workflow
```bash
# Install dependencies
uv sync --frozen

# Update dependencies
uv lock --upgrade

# Run linting
ruff check --fix --respect-gitignore

# Run formatting
ruff format --respect-gitignore

# Run tests
pytest

# Run pre-commit hooks
pre-commit run --all-files

# Clean Python cache files
task pyclean
```

### Task Runner Commands
The project uses Taskfile for common operations:
```bash
task lint       # Run linters
task format     # Run formatters
task test       # Run tests
task pre-commit # Run pre-commit hooks
task uv:sync    # Sync dependencies
task uv:lock    # Update lockfile
```

## Architecture Overview

### Core Components

The application follows a modular architecture with clear separation of concerns:

1. **Player Engine** (`core/player.py`): Central MusicPlayer class that orchestrates all components
   - Manages VLC media player instance
   - Handles file loading and playback control
   - Coordinates between GUI, database, and playback systems

2. **GUI Components** (`core/gui.py`): 
   - MainFrame: Primary interface with left panel (library) and right panel (queue)
   - PlayerControls: Transport controls (play/pause, prev/next, loop, add)
   - Uses tkinter/ttk with custom theming

3. **Library Management** (`core/library.py`):
   - LibraryManager: Handles music collection scanning and database operations
   - Supports recursive directory scanning with configurable depth
   - Deduplication based on file content hashes

4. **Queue System** (`core/queue.py`):
   - QueueManager: Manages playback queue with SQLite backend
   - QueueView: Tree-based UI for queue visualization
   - Supports drag-and-drop reordering

5. **Database Layer** (`core/db.py`):
   - DatabaseManager: SQLite interface for library and queue persistence
   - Schema includes library tracks and queue entries with metadata

6. **Media Controls**:
   - Progress tracking (`core/progress.py`): Custom canvas-based progress bar
   - Volume control (`core/volume.py`): Slider-based volume adjustment
   - Media key support (`utils/mediakeys.py`): macOS-specific media key integration

### Key Design Patterns

- **Event-Driven Architecture**: Uses tkinter event system and callbacks for UI updates
- **Singleton Pattern**: Database and player instances managed as singletons
- **Observer Pattern**: File watcher for hot-reloading during development
- **MVC-like Structure**: Clear separation between data (models), UI (views), and logic (controllers)

### Configuration System

- Central configuration in `config.py` with environment variable support via python-decouple
- Theme configuration loaded from `themes.json`
- Hot-reload capability during development (MT_RELOAD=true)

### Platform Considerations

- Primary support for macOS with Linux compatibility
- macOS-specific features: media keys, window styling, drag-and-drop
- Requires Homebrew-installed Tcl/Tk on macOS for tkinterdnd2 compatibility

## Important Implementation Notes

1. **Tcl/Tk Compatibility**: The project originally used ttkbootstrap but was refactored to use standard tkinter.ttk due to PIL/ImageTk compatibility issues on macOS

2. **Theme Setup**: `setup_theme()` should be called once before creating MusicPlayer instance to avoid duplicate initialization

3. **File Organization**: Follow the 500 LOC limit per file as specified in .cursorrules

4. **Testing**: Use pytest exclusively (no unittest module) with full type annotations

5. **Code Style**: Maintained by Ruff with specific configuration in pyproject.toml
