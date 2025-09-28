# AGENTS.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

mt is a desktop music player designed for large music collections. The application is currently migrating from a Tkinter-based GUI to a modern web-based architecture using PyWebView + FastAPI. It uses VLC for audio playback and supports drag-and-drop functionality.

## Common Development Commands

### Running the Application

#### Development Mode (Recommended)
```bash
# Run with PyWebView + FastAPI (development mode with hot-reload)
DEBUG=True HOT_RELOAD=True uv run python main.py

# Or using task runner
task dev
```

#### Production Mode
```bash
# Run with PyWebView + FastAPI (production mode)
uv run python main.py

# Or using task runner
task prod
```

#### Standalone FastAPI Server (Development)
```bash
# Run FastAPI server only (for API development/testing)
uv run python main.py --api-only

# With custom host/port
uv run python main.py --api-only --host 0.0.0.0 --port 8000
```

#### Legacy Tkinter Version (Deprecated)
```bash
# Old Tkinter-based version (still available)
uv run tkreload main.py

# Alternative auto-reload with repeater utility
uv run python utils/repeater.py
```

### Development Workflow

```bash
# Install dependencies (always use uv, never pip)
uv sync --frozen

# Update dependencies
uv lock --upgrade

# Run linting
uv run ruff check --fix --respect-gitignore

# Run formatting
uv run ruff format --respect-gitignore

# Run tests
uv run pytest -v

# Run pre-commit hooks
pre-commit run --all-files

# Clean Python cache files
task pyclean
```

### Environment Configuration

Create `.env` file for configuration:

```bash
# Development
cp .env.example .env
# Edit .env with DEBUG=True, HOT_RELOAD=True, etc.

# Production
# Edit .env with DEBUG=False, HOT_RELOAD=False
```

### Task Runner Commands

The project uses Taskfile for common operations:
```bash
# Core tasks
task lint           # Run linters
task format         # Run formatters
task test           # Run tests
task pre-commit     # Run pre-commit hooks
task pyclean        # Clean Python cache files

# UV dependency management
task uv:sync        # Sync dependencies with lockfile
task uv:lock        # Update lockfile
task uv:update-deps # Update dependencies to latest versions
task uv:export-reqs # Export requirements.txt

# Application running (add these convenience tasks)
task dev            # Run in development mode (DEBUG=True HOT_RELOAD=True)
task prod           # Run in production mode
task api            # Run FastAPI server only (--api-only)
```

## Architecture Overview

### Current Architecture (Web Migration)

The application is transitioning to a modern web-based architecture:

#### Frontend Layer (Web UI)
- **PyWebView**: Native desktop window hosting web content
- **HTMX + Alpine.js**: Dynamic web interface with minimal JavaScript
- **Basecoat UI**: Design system and theming
- **Templates**: Jinja2-based HTML templates (`templates/`)

#### Backend Layer (FastAPI)
- **FastAPI Application** (`main.py`): Main API server and desktop application
- **API Routers** (`app/api/v1/`): RESTful endpoints for library, player, queue
- **WebSocket Support** (`app/websocket/`): Real-time updates
- **Background Services** (`app/services/`): Business logic (library, player, streaming)

#### Data Layer
- **SQLAlchemy Models** (`app/models/`): Database schemas
- **Async Database** (`app/core/database.py`): Connection management
- **Alembic Migrations**: Database schema versioning

### Legacy Architecture (Tkinter - Deprecated)

The original Tkinter-based implementation remains available:

1. **Player Engine** (`core/player.py`): Central MusicPlayer class
2. **GUI Components** (`core/gui.py`): Tkinter-based interface
3. **Library Management** (`core/library.py`): Music collection scanning
4. **Queue System** (`core/queue.py`): Playback queue management
5. **Database Layer** (`core/db.py`): SQLite persistence
6. **Media Controls**: Progress bars, volume, media keys

### Key Design Patterns

#### Web Architecture Patterns
- **RESTful API Design**: FastAPI with Pydantic models for type safety
- **WebSocket Communication**: Real-time updates between frontend and backend
- **Async/Await**: Asynchronous operations for database and I/O
- **Dependency Injection**: FastAPI's dependency system for service management
- **HTMX-Driven UI**: Server-rendered HTML with minimal JavaScript

#### Legacy Patterns (Tkinter)
- **Event-Driven Architecture**: Tkinter event system and callbacks
- **Singleton Pattern**: Database and player instances
- **Observer Pattern**: File watcher for development hot-reload
- **MVC-like Structure**: Separation of data, UI, and logic

### Configuration System

#### Web Architecture Configuration
- **Pydantic Settings** (`app/core/config.py`): Type-safe configuration with validation
- **Environment Variables**: `.env` file support with `python-decouple` fallback
- **Dynamic Settings**: Hot-reload capable configuration system

#### Key Configuration Options
```python
# Application
APP_NAME: str = "MT Music Player"
APP_VERSION: str = "0.1.0"
DEBUG: bool = False

# Server
SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = 3000

# Database
DATABASE_URL: str = "sqlite:///./mt_music.db"

# Development Features
HOT_RELOAD: bool = False  # File watching and auto-reload
CORS_ENABLED: bool = True  # Cross-origin requests
```

#### Legacy Configuration (Tkinter)
- Central configuration in `config.py` with `python-decouple`
- Theme configuration loaded from `themes.json`
- Hot-reload capability during development

### Platform Considerations

- **Cross-Platform Support**: PyWebView provides native windows on macOS, Windows, and Linux
- **macOS-Specific Features**: Media keys, native file dialogs, drag-and-drop
- **Web-Based UI**: Consistent interface across platforms using web technologies
- **Native Integration**: PyWebView exposes native OS APIs to JavaScript

### Dependencies

#### Core Dependencies
- **VLC**: Audio playback engine (python-vlc)
- **PyWebView**: Native webview wrapper for desktop windows
- **FastAPI**: Modern web framework for REST APIs
- **Uvicorn**: ASGI server for FastAPI
- **SQLAlchemy**: Database ORM with async support
- **Alembic**: Database migration tool

#### Web & UI Dependencies
- **HTMX**: Dynamic HTML without JavaScript complexity
- **Alpine.js**: Minimal JavaScript framework for reactive UI
- **Jinja2**: Template engine for server-side rendering
- **WebSockets**: Real-time communication (websockets library)

#### Development & Utilities
- **python-decouple**: Environment variable configuration
- **eliot/eliot-tree**: Structured logging system
- **watchdog**: File system monitoring for hot-reload
- **ziggy-pydust**: Zig extension module framework
- **ruff**: Fast Python linter and formatter

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

# Export requirements.txt (if needed for CI/CD)
uv export --format requirements-txt > requirements.txt
```

All dependencies should be managed through `uv` to ensure proper virtual environment isolation and reproducible builds. The project uses `pyproject.toml` for dependency declarations and `uv.lock` for reproducible builds.

## Important Implementation Notes

### Web Architecture Guidelines

1. **Async First**: Use async/await for all database operations and I/O
2. **Type Safety**: Full type annotations with Pydantic models for API validation
3. **HTMX Patterns**: Server-rendered HTML with HTMX for dynamic interactions
4. **WebSocket Updates**: Real-time UI updates via WebSocket connections
5. **Native Integration**: Use PyWebView APIs for file dialogs and system integration

### Development Practices

1. **File Organization**: Follow 500 LOC limit per file as specified in .cursorrules
2. **Testing**: Use pytest exclusively with full type annotations
3. **Code Style**: Maintained by Ruff with configuration in `pyproject.toml`
4. **Logging**: Use eliot for structured logging throughout the application

### Migration Notes

1. **Legacy Tkinter Code**: The original Tkinter implementation in `core/` is deprecated but maintained for reference
2. **Unified Entry Point**: `main.py` now serves as both the desktop application and API server
3. **API Design**: RESTful API design with WebSocket support for real-time features

## Development Tools

### Hot-Reload Development Server

The `main.py` provides integrated development with:
- **PyWebView Window**: Native desktop window with web content
- **FastAPI Backend**: Auto-reloading API server
- **File Watching**: Automatic browser refresh on file changes
- **Debug Mode**: Developer tools accessible (F12 in window)

```bash
# Enable hot-reload
DEBUG=True HOT_RELOAD=True uv run python main.py
```

### Eliot Logging System

- Structured logging for debugging and monitoring
- Action tracking with `start_action()` context managers
- Error reporting and file operation logging
- Available through `eliot` and `eliot-tree` dependencies
- Gracefully degrades when eliot is not available

### Legacy Repeater Utility (`utils/repeater.py`)

- Auto-reloads Tkinter application when Python files are modified
- Respects .gitignore patterns for intelligent file watching
- Still available for legacy Tkinter development
- Usage: `uv run python utils/repeater.py [main_file]`

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

# Development build with debug symbols
cd src && zig build

# Production build with optimizations
cd src && zig build -Doptimize=ReleaseSafe
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

## Running the Application

### Development Mode

Development mode provides hot-reload, debug tools, and development-friendly features:

```bash
# Method 1: Direct command
DEBUG=True HOT_RELOAD=True uv run python main.py

# Method 2: Using task runner (if configured)
task dev

# Method 3: Environment file
echo "DEBUG=True" > .env
echo "HOT_RELOAD=True" >> .env
uv run python main.py
```

**Development Features:**
- Hot-reload: Automatic browser refresh on file changes
- Debug tools: F12 opens developer console
- CORS enabled for API testing
- Detailed logging and error messages
- File watcher monitors `.py`, `.html`, `.css`, `.js` files

### Production Mode

Production mode is optimized for end users with minimal overhead:

```bash
# Method 1: Direct command
uv run python main.py

# Method 2: Using task runner (if configured)
task prod

# Method 3: Environment file
echo "DEBUG=False" > .env
echo "HOT_RELOAD=False" >> .env
uv run python main.py
```

**Production Features:**
- Optimized performance
- Minimal logging
- Secure configuration
- Native window integration
- No development tools exposed

### Alternative Running Methods

#### Standalone FastAPI Server (API Development)
```bash
# Run FastAPI server only (for API testing/development)
uv run python main.py --api-only

# Server available at: http://localhost:3000
# API docs at: http://localhost:3000/docs

# With custom host/port
uv run python main.py --api-only --host 0.0.0.0 --port 8000
```

#### Legacy Tkinter Version (Deprecated)
```bash
# Old desktop application (still functional)
uv run tkreload main.py

# Alternative auto-reload with repeater utility
uv run python utils/repeater.py
```

### Configuration Options

Key environment variables for running modes:

```bash
# Server Configuration
SERVER_HOST=127.0.0.1    # Default: 127.0.0.1
SERVER_PORT=3000         # Default: 3000

# Development Features
DEBUG=True               # Enable debug mode
HOT_RELOAD=True          # Enable file watching
CORS_ENABLED=True        # Allow cross-origin requests

# Database
DATABASE_URL=sqlite:///./mt_music.db  # Database connection

# Application
APP_NAME="MT Music Player"
APP_VERSION="0.1.0"
```

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
