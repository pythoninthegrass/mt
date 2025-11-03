# AGENTS.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

mt is a desktop music player designed for large music collections, built with Python and Tkinter. It uses VLC for audio playback and supports drag-and-drop functionality.

## General Guidelines

- ALWAYS use atomic commits throughout development
  - Each commit should represent a single, complete, and coherent unit of work
  - "Don't mix your apples with your toaster" - keep changes distinct and focused
  - Commit frequently after completing subtasks or reaching meaningful progress points
  - Write clear commit messages explaining both what changed and why
  - Use `git add -i` (interactive mode) or `git add -p` (patch mode) to stage specific changes
  - Break files with multiple changes into smaller hunks using patch mode's split feature
  - Verify each commit is not broken - ensure all necessary files/chunks are included
  - After user confirms changes are ready to push, offer to squash related atomic commits using `git rebase -i`
- NEVER use playwright for anything. This is a tkinter desktop app.
- NEVER create *.backup files. This is a version controlled repo

## MCP Servers

ALWAYS use these MCP servers:

- sequential-thinking: detailed, step-by-step thinking process for problem-solving and analysis.
- context7: when looking up library context outside the source code
  - oaubert/python-vlc
  - quodlibet/mutagen
  - itamarst/eliot
  - hypothesisworks/hypothesis
  - spiraldb/ziggy-pydust
  - ludo-technologies/pyscn
  - johnwmillr/lyricsgenius
- screencap: for screenshots of front-end changes

## Atomic Commit Workflow

### Why Atomic Commits

Atomic commits make code reviews easier, improve history browsing, and simplify reverting changes. Each commit should contain a single, complete, and coherent unit of work that stands independently.

### Benefits

- **Debugging**: Use `git bisect` to rapidly identify problems
- **Code History**: Create organized, understandable histories with clear stories
- **Collaboration**: Streamline code reviews by focusing on single changes
- **Safe Operations**: Revert or cherry-pick individual changes without side effects

### Creating Atomic Commits

**Keep changes small and simple** - The more complex your changes, the harder it is to break them into atomic commits without mistakes.

**Use Interactive Staging** - Stage specific files and parts of files:

```bash
# Interactive mode - select which files/hunks to stage
git add -i

# Patch mode - directly choose hunks to stage
git add -p <file>

# Other patch commands
git reset --patch        # Unstage specific hunks
git checkout --patch     # Discard specific hunks
git stash save --patch   # Stash specific hunks
```

**Interactive Mode Commands** (`git add -i`):
- `s` or `1`: View status (staged vs unstaged changes)
- `u` or `2`: Stage files (equivalent to `git add <file>`)
- `r` or `3`: Unstage files (equivalent to `git rm --cached <file>`)
- `a` or `4`: Add untracked files
- `p` or `5`: Patch mode - select parts of files (hunks) to stage
- `d` or `6`: View diff of staged files

**Patch Mode Commands** (after selecting `p` or using `git add -p`):
- `y`: Stage this hunk
- `n`: Don't stage this hunk
- `s`: Split the hunk into smaller hunks ⭐ (most useful!)
- `e`: Manually edit the hunk
- `q`: Quit without staging remaining hunks
- `a`: Stage this hunk and all later hunks in the file
- `d`: Don't stage this or any later hunks
- `g`: Jump to a specific hunk
- `/`: Search for hunks matching regex
- `?`: Show help

### Workflow Example

1. **Check what changed**: `git status` and `git diff`
2. **Start interactive mode**: `git add -i`
3. **Stage related files**: Use `u` to stage complete files that belong together
4. **Handle mixed changes**: Use `p` to enter patch mode for files with multiple unrelated changes
5. **Split hunks**: Use `s` to break large hunks into smaller pieces
6. **Stage relevant hunks**: Use `y` to stage only the hunks for this commit
7. **Review staged changes**: Use `d` to review what will be committed
8. **Commit**: Exit with `q` and run `git commit -m "descriptive message"`
9. **Repeat**: Continue staging and committing remaining changes

### Before Pushing

After completing development with multiple atomic commits:

1. Review your commit history: `git log --oneline`
2. Review what changed: `git status` and `git diff`
3. When user confirms readiness to push, ask: "Would you like me to squash these related atomic commits into a single commit using `git rebase -i`?"
4. If yes, use `git rebase -i HEAD~N` (where N = number of commits to review)

### Important Warnings

⚠️ **Verify each commit is not broken** - Ensure all necessary files and code chunks are included before committing. A broken commit defeats the purpose of atomic commits.

⚠️ **Don't mix unrelated changes** - "Don't mix your apples with your toaster." Each commit should be focused on one logical change.

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
uv pip install -r pyproject.toml --all-extras

# Update dependencies
uv lock --upgrade

# Run linting
uv run ruff check --fix --respect-gitignore

# Run formatting
uv run ruff format --respect-gitignore

# Run all tests (note: -v and -p no:pydust are configured by default)
uv run pytest tests/

# Quick smoke tests (~11s) - critical E2E tests for development
uv run pytest tests/test_e2e_smoke.py

# Fast tests (~23s) - unit + property + smoke E2E
uv run pytest -m "not slow"

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

# Run comprehensive E2E tests (marked as slow)
uv run pytest tests/test_e2e_*.py -m slow

# Run unit + property tests (fast development feedback)
uv run pytest tests/test_unit_*.py tests/test_props_*.py

# Skip flaky tests when running full suite
uv run pytest tests/ -m "not flaky_in_suite"

# Run pre-commit hooks
pre-commit run --all-files

# Clean Python cache files
task pyclean
```

### Flaky Tests

Some tests are marked with `@pytest.mark.flaky_in_suite` because they pass reliably in isolation but experience timing issues when run in the full test suite due to persistent application state pollution:

**Known Flaky Tests:**
- `tests/test_e2e_smoke.py::test_next_previous_navigation` - Track navigation test that passes 100% in isolation but ~50% in full suite
- `tests/test_e2e_controls.py::test_media_key_next` - Media key next test that experiences timing issues with track changes in full suite

**Root Cause:**
These tests experience persistent application state pollution after running many other E2E tests. The application's internal state (VLC player, queue manager, event handlers) doesn't fully reset between tests, causing timing-dependent failures.

**To run flaky tests in isolation (reliable):**
```bash
# Single test
uv run pytest tests/test_e2e_smoke.py::test_next_previous_navigation -v

# Multiple flaky tests
uv run pytest tests/test_e2e_smoke.py::test_next_previous_navigation tests/test_e2e_controls.py::test_media_key_next -v
```

**To skip flaky tests in full suite:**
```bash
uv run pytest tests/ -m "not flaky_in_suite"
```

**Note:** The `flaky_in_suite` marker is defined in `pyproject.toml` and allows excluding these tests during CI/CD or full test suite runs while still maintaining them for isolation testing. If you need to verify these tests work, always run them in isolation.

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

The application follows a modular architecture with clear separation of concerns. Large files have been refactored into focused packages with clear responsibilities:

1. **Player Engine** (`core/player/`): Central MusicPlayer class that orchestrates all components
   - Split into focused modules: handlers, library, progress, queue, ui, window
   - Manages VLC media player instance
   - Handles file loading and playback control
   - Coordinates between GUI, database (`./mt.db`), and playback systems
     - ALWAYS respect the `DB_NAME` under `config.py`
     - NEVER create additional sqlite databases (e.g., `mt_test.db`)

2. **GUI Components** (`core/gui/`): Modular UI components
   - `music_player.py`: Main application window container
   - `player_controls.py`: Transport controls (play/pause, prev/next, loop, add)
   - `progress_status.py`: Progress bar and status display
   - `library_search.py`: Library search and filtering interface
   - `queue_view.py`: Tree-based queue visualization with drag-and-drop
   - Uses tkinter/ttk with custom theming

3. **Library Management** (`core/library.py`):
   - LibraryManager: Handles music collection scanning and database operations
   - Supports recursive directory scanning with configurable depth
   - Deduplication based on file content hashes

4. **Queue System** (`core/queue.py`):
   - QueueManager: Manages playback queue with SQLite backend
   - Supports drag-and-drop reordering

5. **Database Layer** (`core/db/`): Facade pattern for database operations
   - `database.py`: Core MusicDatabase facade
   - `preferences.py`: User preferences and settings persistence
   - `library.py`: Library track operations
   - `queue.py`: Queue management operations
   - `favorites.py`: Favorites and dynamic playlist views
   - SQLite interface for library and queue persistence

6. **Playback Controls** (`core/controls/`):
   - `player_core.py`: PlayerCore class for playback control logic
   - Handles play, pause, next, previous, shuffle, loop operations

7. **Now Playing View** (`core/now_playing/`):
   - `view.py`: NowPlayingView class for current playback display
   - Shows currently playing track with metadata

8. **Media Controls**:
   - Progress tracking (`core/progress.py`): Custom canvas-based progress bar
   - Volume control (`core/volume.py`): Slider-based volume adjustment
   - Media key support (`utils/mediakeys.py`): macOS-specific media key integration

9. **API Server** (`api/server.py`):
   - Socket-based API server for programmatic control
   - JSON command/response protocol with comprehensive error handling
   - Enables LLM and automation tool integration
   - Thread-safe command execution on main UI thread
   - Localhost-only security by default (port 5555)

### Key Design Patterns

- **Modular Package Structure**: Large files (>500 LOC) refactored into focused packages using facade pattern
- **Event-Driven Architecture**: Uses tkinter event system and callbacks for UI updates
- **Singleton Pattern**: Database and player instances managed as singletons
- **Observer Pattern**: File watcher for hot-reloading during development
- **MVC-like Structure**: Clear separation between data (models), UI (views), and logic (controllers)
- **Facade Pattern**: Database and API components use facade pattern for clean public interfaces

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
   - DO NOT take a screenshot until verifying that the app has reloaded with the end user; `sleep 2` isn't enough time to propagate the changes
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
uv pip install -r pyproject.toml --all-extras

# Add new dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Update dependencies
uv lock --upgrade
```

All dependencies should be managed through `uv` to ensure proper virtual environment isolation and reproducible builds.

## Important Implementation Notes

1. **Modular Refactoring**: The codebase has undergone comprehensive refactoring (Phases 1-6 completed Oct 2025)
   - Large files split into focused packages with facade pattern
   - Target: ~500 LOC per file for maintainability
   - All core components now use package structure (player, gui, db, controls, now_playing, api)
   - Note: Some files like `queue_view.py` (709 LOC) still exceed target and may be refactored further

2. **Tcl/Tk Compatibility**: The project originally used ttkbootstrap but was refactored to use standard tkinter.ttk due to PIL/ImageTk compatibility issues on macOS

3. **Theme Setup**: `setup_theme()` should be called once before creating MusicPlayer instance to avoid duplicate initialization

4. **File Organization**: Follow the 500 LOC limit per file as specified in .cursorrules
   - When adding new features, prefer extending existing packages over creating new files
   - Use facade pattern for complex components with multiple responsibilities

5. **Testing**: Use pytest exclusively (no unittest module) with full type annotations
   - All 467+ tests pass after refactoring phases
   - Unit, property-based, and E2E tests maintained

6. **Code Style**: Maintained by Ruff with specific configuration in ruff.toml
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
  - ALWAYS mark acceptance criteria before setting it to done via `backlog task edit <id> -s Done`
- ❌ **DON'T**: Edit markdown files directly
- ❌ **DON'T**: Manually change checkboxes in files
- ❌ **DON'T**: Add or modify text in task files without using CLI

**Why?** Direct file editing breaks metadata synchronization, Git tracking, and task relationships.

## Essential CLI Commands

### Task Creation Best Practices

**IMPORTANT: When creating new tasks, follow this two-step process:**

1. **Create the task with temporary filename** using `backlog task create`
2. **Manually rename file and update metadata** to match nomenclature

**Example Workflow:**
```bash
# Step 1: Create task (will generate task-<priority>.<number> filename)
backlog task create "Fix race condition in shuffle mode" \
  -d "Description here" \
  --ac "Criterion 1" \
  --ac "Criterion 2" \
  -p high --plain

# Step 2: Find highest task number
ls -1 backlog/tasks/task-*.md | grep -E "^task-[0-9]" | sort -V | tail -1

# Step 3: Rename file manually (e.g., if highest is task-076, use task-077)
mv "backlog/tasks/task-high.01 - Title.md" "backlog/tasks/task-077 - Title.md"

# Step 4: Edit frontmatter manually to update id and set priority
# Change: id: task-high.01 → id: task-077
# Add:    priority: high
# Add:    ordinal: 2000
# Remove: parent_task_id: task-high
```

**Standard Task File Format:**
```markdown
---
id: task-077
title: Fix race condition in shuffle mode
status: To Do
assignee: []
created_date: '2025-10-26 18:40'
updated_date: '2025-10-26 18:40'
labels: []
dependencies: []
priority: high
ordinal: 2000
---

## Description

Task description here.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 First criterion
- [ ] #2 Second criterion
<!-- AC:END -->
```

### Task Management

```bash
backlog task create "Title" -d "Description" --ac "Criterion 1" --ac "Criterion 2" -p high --plain
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
