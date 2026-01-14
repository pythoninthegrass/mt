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
- NEVER create *.backup files. This is a version controlled repo

## Context7

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

- hypothesisworks/hypothesis
- itamarst/eliot
- johnwmillr/lyricsgenius
- ludo-technologies/pyscn
- oaubert/python-vlc
- quodlibet/mutagen
- spiraldb/ziggy-pydust
- websites/rs_tauri_2_9_5

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

# Test execution tiers - run different tests based on workflow stage
uv run pytest tests/test_unit_*.py tests/test_props_*.py                      # TDD: unit+property only (~18s)
uv run pytest tests/test_unit_*.py tests/test_props_*.py tests/test_e2e_smoke.py  # Pre-commit: +smoke (~20s)
uv run pytest tests/ -m "not slow and not flaky_in_suite"                    # Pre-PR: fast suite (~22s)
uv run pytest tests/                                                          # CI/pre-push: everything (~60s)

# Specialized test commands (less common)
uv run pytest tests/test_e2e_smoke.py                                        # Quick smoke tests only
uv run pytest tests/test_props_*.py --hypothesis-profile=thorough            # Thorough property testing
uv run pytest tests/test_props_*.py --hypothesis-show-statistics             # Property test statistics
uv run pytest tests/test_e2e_*.py -m slow                                    # Comprehensive E2E tests

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

**To skip both slow and flaky tests (recommended for development):**
```bash
uv run pytest tests/ -m "not slow and not flaky_in_suite"
```

**Note:** The `flaky_in_suite` marker is defined in `pyproject.toml` and allows excluding these tests during CI/CD or full test suite runs while still maintaining them for isolation testing. If you need to verify these tests work, always run them in isolation.

**Pytest marker syntax clarification:**

- ❌ Wrong: `-m "not slow" -m "not flaky_in_suite"` (multiple flags don't combine correctly)
- ✅ Correct: `-m "not slow and not flaky_in_suite"` (boolean AND expression)
- ✅ Alternative: `-m "not (slow or flaky_in_suite)"` (boolean OR with negation)

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

### Git Worktree Management (worktrunk)

The project uses [worktrunk](https://github.com/max-sixty/worktrunk) (`wt`) for managing git worktrees, enabling parallel development and isolated migration work.

**Checking out worktrees on another computer:**

```bash
# If repository already exists, fetch latest branches
git fetch origin

# Create and switch to a worktree for a remote branch
wt switch tauri-migration

# Or if starting fresh:
git clone https://github.com/pythoninthegrass/mt.git
cd mt
wt switch tauri-migration
```

Worktrunk automatically detects remote branches and creates worktrees at computed paths based on your configured template (typically `../repo.branch-name`).

**Basic worktree operations:**

```bash
# Switch to existing worktree for a branch
wt switch feature

# Create new worktree and branch from current HEAD
wt switch --create feature

# Create from specific base branch
wt switch --create feature --base=main

# Create and execute command in new worktree
wt switch -c feature -x "cargo tauri dev"

# Switch to default branch's worktree
wt switch ^

# Switch to previous worktree
wt switch -
```

**Merge workflow:**
```bash
# Full merge workflow: squash, rebase, remove worktree
wt merge

# Merge to specific target branch
wt merge --target=develop

# Skip squashing (keep commit history)
wt merge --no-squash

# Merge without removing worktree
wt merge --no-remove
```

**Granular operations:**
```bash
# Squash all commits into one
wt step squash

# Rebase onto target branch
wt step rebase

# Push to remote
wt step push

# Run command in all worktrees
wt step for-each -- git status
wt step for-each -- uv run pytest
```

**Cleanup:**
```bash
# Remove current worktree (prompts for branch deletion)
wt remove

# Remove specific worktree by branch name
wt remove feature

# Remove worktree but keep branch
wt remove feature --no-delete-branch

# Force delete unmerged branch
wt remove feature -D
```

**Current worktrees:**

- `main` - Primary development (Tkinter app)
- `tauri-migration` - Tauri + Rust playback migration (when created)

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

<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools).

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:

- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and completion
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->

<!-- MANTIC SEARCH GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## SEARCH CAPABILITY (MANTIC v1.0.21)

This project uses Mantic for intelligent code search. Use it before resorting to grep/find commands.

**Basic Search:**
```bash
npx mantic.sh "your query here"
```

**Advanced Features:**

**Zero-Query Mode (Context Detection):**
```bash
npx mantic.sh ""  # Shows modified files, suggestions, impact
```

**Context Carryover (Session Mode):**
```bash
npx mantic.sh "query" --session "session-name"
```

**Output Formats:**
```bash
npx mantic.sh "query" --json        # Full metadata
npx mantic.sh "query" --files        # Paths only
npx mantic.sh "query" --markdown    # Pretty output
```

**Impact Analysis:**
```bash
npx mantic.sh "query" --impact      # Shows blast radius
```

**File Type Filters:**
```bash
npx mantic.sh "query" --code        # Code files only
npx mantic.sh "query" --test        # Test files only
npx mantic.sh "query" --config       # Config files only
```

### Search Quality (v1.0.21)

- CamelCase detection: "ScriptController" finds script_controller.h
- Exact filename matching: "download_manager.cc" returns exact file first
- Path sequence: "blink renderer core dom" matches directory structure
- Word boundaries: "script" won't match "javascript"
- Directory boosting: "gpu" prioritizes files in gpu/ directories

### Best Practices

**DO NOT use grep/find blindly. Use Mantic first.**

Mantic provides brain-inspired scoring that prioritizes business logic over boilerplate, making it more effective for finding relevant code than traditional text search tools.

</CRITICAL_INSTRUCTION>

<!-- MANTIC SEARCH GUIDELINES END -->
