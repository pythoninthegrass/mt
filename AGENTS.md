# AGENTS.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

mt is a desktop music player designed for large music collections, built with Python and Tkinter. It uses VLC for audio playback and supports drag-and-drop functionality.

## MCP Servers

ALWAYS use these MCP servers:

- serena: when editing and searching for files
  - activate_project (MCP)(project: "mt")
- sequential-thinking: detailed, step-by-step thinking process for problem-solving and analysis.
- context7: when looking up library context outside the source code
  - oaubert/python-vlc
  - itamarst/eliot
  - hypothesisworks/hypothesis
  - spiraldb/ziggy-pydust
- screencap: for screenshots of front-end changes

## Common Development Commands

### Running the Application

```bash
# Standard run
uv run main.py

# Run main with auto-reload
uv run repeater

# Run with API server enabled (for LLM/automation control)
MT_API_SERVER_ENABLED=true uv run main.py

# Run with API server on custom port
MT_API_SERVER_ENABLED=true MT_API_SERVER_PORT=5555 uv run main.py
```

### Development Workflow

```bash
# Install dependencies
uv sync --frozen

# Update dependencies
uv lock --upgrade

# Run linting
uv run ruff check --fix --respect-gitignore

# Run formatting
uv run ruff format --respect-gitignore

# Run all tests (note: -v and -p no:pydust are configured by default)
uv run pytest tests/

# Run ONLY unit tests (fast, for development)
uv run pytest tests/test_unit_*.py

# Run ONLY property-based tests (fast, for invariant validation)
uv run pytest tests/test_props_*.py

# Run property tests with more examples (thorough)
uv run pytest tests/test_props_*.py --hypothesis-profile=thorough

# Run property tests with statistics
uv run pytest tests/test_props_*.py --hypothesis-show-statistics

# Run ONLY E2E tests (slower, for integration validation)
uv run pytest tests/test_e2e_*.py

# Run unit + property tests (fast development feedback)
uv run pytest tests/test_unit_*.py tests/test_props_*.py

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
   - Coordinates between GUI, database (`./mt.db`), and playback systems

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

7. **API Server** (`core/api.py`):
   - Socket-based API server for programmatic control
   - JSON command/response protocol with comprehensive error handling
   - Enables LLM and automation tool integration
   - Thread-safe command execution on main UI thread
   - Localhost-only security by default (port 5555)

### Key Design Patterns

- **Event-Driven Architecture**: Uses tkinter event system and callbacks for UI updates
- **Singleton Pattern**: Database and player instances managed as singletons
- **Observer Pattern**: File watcher for hot-reloading during development
- **MVC-like Structure**: Clear separation between data (models), UI (views), and logic (controllers)

### Configuration System

- Central configuration in `config.py` with environment variable support via python-decouple
- Theme configuration loaded from `themes.json`
- Hot-reload capability during development (MT_RELOAD=true)
- API server configuration:
  - `MT_API_SERVER_ENABLED`: Enable/disable API server (default: false)
  - `MT_API_SERVER_PORT`: Configure API server port (default: 5555)

### Platform Considerations

- Primary support for macOS with Linux compatibility
- macOS-specific features: media keys, window styling, drag-and-drop
- Requires Homebrew-installed Tcl/Tk on macOS for tkinterdnd2 compatibility

### Quick Visual Check

**IMMEDIATELY after implementing any front-end change:**

1. **Identify what changed** - Review the modified components/pages
2. **Navigate to affected pages** - Use `screencap` MCP to compare before and after changes
   - If an `"error": "No windows found for 'python3'"` occurs, relaunch the app via `nohup uv run repeater > /dev/null 2>&1` 
   - When pkill raises a non-zero exit code, assume that the app has been manually quit and restart it
   - Skip screencap calls if the front-end change isn't _visible_ (e.g., typing produces a bell sound)
3. **Validate feature implementation** - Ensure the change fulfills the user's specific request
4. **Check acceptance criteria** - Review any provided context files or requirements
5. **Capture evidence** - Take a screenshot of each changed view. Save to `/tmp` if writeable; otherwise, `.claude/screenshots`
6. **Check for errors** - Look for any errors in stdout or Eliot logging

### Dependencies

- **VLC**: Audio playback engine
- **tkinterdnd2**: Drag-and-drop functionality
- **python-decouple**: Environment variable configuration
- **eliot/eliot-tree**: Structured logging system
- **watchdog**: File system monitoring for development tools
- **ziggy-pydust**: Zig extension module framework for Python

### Dependency Management

**ALWAYS use `uv` for Python dependency management. NEVER install packages at the system level with `pip`.**

```bash
# Install dependencies
uv sync --frozen

# Add new dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Update dependencies
uv lock --upgrade
```

All dependencies should be managed through `uv` to ensure proper virtual environment isolation and reproducible builds.

## Important Implementation Notes

1. **Tcl/Tk Compatibility**: The project originally used ttkbootstrap but was refactored to use standard tkinter.ttk due to PIL/ImageTk compatibility issues on macOS

2. **Theme Setup**: `setup_theme()` should be called once before creating MusicPlayer instance to avoid duplicate initialization

3. **File Organization**: Follow the 500 LOC limit per file as specified in .cursorrules

4. **Testing**: Use pytest exclusively (no unittest module) with full type annotations

5. **Code Style**: Maintained by Ruff with specific configuration in ruff.toml
    - Additional linter rules:
      - Use `contextlib.suppress(Exception)` instead of `try`-`except`-`pass`
      - Use ternary operator `indicator = ('▶' if is_currently_playing else '⏸') if is_current else ''` instead of `if`-`else`-block

## Development Tools

### Repeater Utility (`utils/repeater.py`)

- Auto-reloads Tkinter application when Python files are modified
- Respects .gitignore patterns for intelligent file watching
- Watches entire project directory recursively
- Provides better development experience than basic tkreload
- Usage: `uv run python utils/repeater.py [main_file]`

### Eliot Logging System

- Structured logging for debugging and monitoring
- Action tracking with `start_action()` context managers
- Error reporting and file operation logging
- Available through `eliot` and `eliot-tree` dependencies
- Gracefully degrades when eliot is not available
- ALWAYS couple functions and classes with Eliot logging (i.e., create/update methods with logging)

#### Logging Implementation Patterns

The codebase uses comprehensive structured logging for all user interactions and system events:

1. **Core Logging Module** (`core/logging.py`):
   - `log_player_action()`: Helper function for consistent player action logging
   - Separate loggers for different subsystems (player, controls, library, queue, media_keys)
   - Graceful fallback when Eliot is not available

2. **Common Logging Patterns**:
   ```python
   from core.logging import player_logger, log_player_action
   from eliot import start_action
   
   def some_action(self):
       with start_action(player_logger, "action_name"):
           # Capture before state
           old_state = self.get_current_state()
           
           # Perform action
           result = self.do_something()
           
           # Log with comprehensive metadata
           log_player_action(
               "action_name",
               trigger_source="gui",  # or "keyboard", "media_key", "drag_drop", etc.
               old_state=old_state,
               new_state=result,
               description="Human-readable description"
           )
   ```

3. **Trigger Sources**:
   - `"gui"`: User interface interactions (buttons, sliders, menus)
   - `"keyboard"`: Keyboard shortcuts
   - `"media_key"`: System media keys (play/pause, next/prev)
   - `"drag_drop"`: File drag-and-drop operations
   - `"user_resize"`: UI element resizing
   - `"periodic_check"`: Automatic system checks
   - `"automatic"`: System-initiated actions

4. **Instrumented Actions** (as of latest implementation):
   - **Playback Control**: play/pause, next/previous track, stop, seek operations
   - **Volume Control**: Volume changes with before/after values
   - **Loop/Shuffle**: Toggle states with mode tracking
   - **Track Management**: Track deletion with queue position and metadata
   - **File Operations**: Drag-and-drop with file analysis
   - **UI Navigation**: Library section switches with content counts
   - **Window Management**: Close, minimize, maximize with geometry tracking
   - **UI Preferences**: Column width changes, panel resizing
   - **Media Keys**: All media key interactions with key identification

5. **Logging Best Practices**:
   - Always capture before/after states when applicable
   - Include relevant metadata (file paths, track info, UI state)
   - Use descriptive action names and human-readable descriptions
   - Differentiate trigger sources for better analysis
   - Log both successful operations and failures/errors

### Zig Module Development

The project uses Zig for high-performance native extensions via ziggy-pydust. Zig modules are located in the `src/` directory and provide performance-critical functionality like music file scanning.

#### Building Zig Modules

```bash
# Build all Zig modules
uv run python build.py

# Or build via hatch (used during package installation)
hatch build

# Clean build artifacts
rm -rf src/.zig-cache src/zig-out core/*.so
```

#### Zig Development Workflow

```bash
# Install/update Zig (if needed)
# On macOS with mise:
mise install zig@0.14.0

# Check Zig version
zig version

# Build in debug mode
cd src && zig build

# Build with optimizations
cd src && zig build -Doptimize=ReleaseSafe

# Run tests
cd src && zig build test
```

#### Zig Module Structure

- `src/build.zig`: Main build configuration
- `src/scan.zig`: Music file scanning module
- `core/_scan.so`: Generated Python extension (created during build)

#### Troubleshooting Zig Builds

**Common Issues:**

1. **Zig Version Compatibility**: Ensure Zig 0.14.x is installed
   ```bash
   zig version  # Should show 0.14.x
   ```

2. **Python Path Issues**: Build script uses virtual environment Python
   ```bash
   uv run python build.py  # Uses correct Python executable
   ```

3. **Missing Dependencies**: Ensure ziggy-pydust is installed
   ```bash
   uv sync
   uv run python -c "import pydust; print('OK')"
   ```

4. **Build Cache Issues**: Clear cache if builds fail
   ```bash
   rm -rf src/.zig-cache
   uv run python build.py
   ```

**Build Configuration:**

- Uses `self_managed = true` in `pyproject.toml` for custom build.zig
- Python extensions are built to `core/` directory
- Release-safe optimization for production builds

<!-- BACKLOG.MD GUIDELINES START -->

# ⚠️ CRITICAL: NEVER EDIT TASK FILES DIRECTLY

**ALL task operations MUST use the Backlog.md CLI commands**

- ✅ **DO**: Use `backlog task edit` and other CLI commands
- ✅ **DO**: Use `backlog task create` to create new tasks
- ✅ **DO**: Use `backlog task edit <id> --check-ac <index>` to mark acceptance criteria
- ❌ **DON'T**: Edit markdown files directly
- ❌ **DON'T**: Manually change checkboxes in files
- ❌ **DON'T**: Add or modify text in task files without using CLI

**Why?** Direct file editing breaks metadata synchronization, Git tracking, and task relationships.

## Essential CLI Commands

### Task Management

```bash
backlog task create "Title" -d "Description" --ac "Criterion 1" --ac "Criterion 2"
backlog task list --plain                    # List all tasks
backlog task 42 --plain                      # View specific task
backlog task edit 42 -s "In Progress" -a @myself  # Start working
backlog task edit 42 --check-ac 1            # Mark AC complete
backlog task edit 42 --notes "Implementation complete"  # Add notes
backlog task edit 42 -s Done                 # Mark as done
backlog task archive 42                      # Archive task
```

### Key Principles

- **Always use `--plain` flag** for AI-friendly output when viewing/listing
- **Never bypass the CLI** - It handles Git, metadata, file naming, and relationships
- **Tasks live in `backlog/tasks/`** as `task-<id> - <title>.md` files
- **Use CLI for both reading and writing** - `backlog task create`, `backlog task edit`, etc.

### Quick Reference: DO vs DON'T

| Action       | ✅ DO                                | ❌ DON'T                          |
|--------------|-------------------------------------|----------------------------------|
| View task    | `backlog task 42 --plain`           | Open and read .md file directly  |
| List tasks   | `backlog task list --plain`         | Browse backlog/tasks folder      |
| Check AC     | `backlog task edit 42 --check-ac 1` | Change `- [ ]` to `- [x]` in file|
| Add notes    | `backlog task edit 42 --notes "..."`| Type notes into .md file         |
| Change status| `backlog task edit 42 -s Done`      | Edit status in frontmatter       |

**🎯 Golden Rule: If you want to change ANYTHING in a task, use the `backlog task edit` command.**

Full help available: `backlog --help`

<!-- BACKLOG.MD GUIDELINES END -->
