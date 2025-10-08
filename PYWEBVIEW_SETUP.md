# PyWebView Development Environment Setup

## Overview

This document describes the PyWebView + FastAPI development environment setup for the MT Music Player web migration.

## Installation

The following packages have been installed via `uv`:

- **pywebview**: Native webview wrapper for displaying HTML content
- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for FastAPI

```bash
uv add pywebview fastapi uvicorn
```

## Test Files Created

### 1. Basic PyWebView Test (`test_pywebview.py`)
- Simple standalone PyWebView window test
- Verifies PyWebView installation and functionality
- Run with: `uv run python test_pywebview.py`

### 2. FastAPI Server (`test_fastapi_server.py`)
- Standalone FastAPI server with background thread support
- Includes CORS middleware for development
- Test endpoints at `/` and `/api/test`
- Can run standalone: `uv run python test_fastapi_server.py`

### 3. Integrated Example (`test_pywebview_fastapi.py`)
- Combined PyWebView + FastAPI setup
- FastAPI runs in background thread
- PyWebView window loads FastAPI server content
- Includes Python-JavaScript API bridge
- Run with: `uv run python test_pywebview_fastapi.py`

### 4. Server (`server.py`)
- General-purpose server supporting both development and production modes
- Environment-based configuration for flexible deployment
- Optional hot-reload for development (when `HOT_RELOAD=True`)
- File watcher for Python, HTML, CSS, JS changes (dev mode)
- Debug mode controlled via `DEBUG` environment variable
- Configurable port and host via environment variables
- Run with: `uv run python server.py`

## Key Features Implemented

✅ **PyWebView Package Installed**: Native webview wrapper installed and working
✅ **Basic Window Creation**: Can create and display PyWebView windows
✅ **FastAPI Server**: Background thread server implementation
✅ **Server Integration**: PyWebView loads content from localhost FastAPI
✅ **Hot-Reload**: Development server with automatic browser refresh
✅ **Modular Configuration**: Port and host configurable via environment variables
✅ **Debug Mode**: Developer tools accessible (F12 in window)
✅ **CORS Configuration**: Enabled for development flexibility
✅ **API Bridge**: Python-JavaScript communication established

## Architecture

```
┌─────────────────┐
│   PyWebView     │
│  (Native Window)│
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│    FastAPI      │
│  (Backend API)  │
└─────────────────┘
```

## Configuration

The server uses `python-decouple` for environment-based configuration:

### Core Settings
- **SERVER_PORT**: Port number (default: 3000)
- **SERVER_HOST**: Host address (default: 127.0.0.1)
- **APP_TITLE**: Application title (default: "mt music player")

### Mode Settings
- **DEBUG**: Enable debug mode (default: False)
- **HOT_RELOAD**: Enable file watcher and auto-reload (default: False)
- **CORS_ENABLED**: Enable CORS middleware (defaults to DEBUG value)

### Quick Setup

For development:
```bash
cp .env.dev .env  # Pre-configured for development
```

For production:
```bash
cp .env.example .env  # Pre-configured for production
```

Or set directly:
```bash
DEBUG=True HOT_RELOAD=True uv run python server.py  # Development
DEBUG=False uv run python server.py                 # Production
```

## Development Workflow

1. **Start Development Server**:
   ```bash
   uv run python server.py
   ```

2. **Access Application**: 
   - Window opens automatically
   - FastAPI server at http://localhost:3000
   - Developer tools with F12

3. **Hot-Reload**: 
   - Edit any `.py`, `.html`, `.css`, or `.js` file
   - Browser automatically reloads

## Next Steps

With this foundation in place, the next phases of the migration can proceed:

1. **Zig Module Enhancement** (Task 23): Update scanning module for web architecture
2. **FastAPI Backend** (Task 24): Build comprehensive API framework
3. **Audio Streaming** (Task 25): Implement streaming service
4. **HTMX Frontend** (Task 26-29): Create UI with HTMX and Alpine.js
5. **Native Integration** (Task 31-32): File system and keyboard shortcuts

## Testing

Run all test files to verify setup:

```bash
# Test PyWebView alone
uv run python test_pywebview.py

# Test FastAPI server
uv run python test_fastapi_server.py

# Test integrated setup
uv run python test_pywebview_fastapi.py

# Run development server
uv run python server.py
```

All components are working and ready for the web migration implementation.