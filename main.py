#!/usr/bin/env python

import argparse
import os
import signal
import sys
import threading
import time
import uvicorn
import webview
from decouple import config

from app.api.v1.library import router as library_router
from app.api.v1.player import router as player_router
from app.api.v1.queue import router as queue_router
from app.core.config import settings
from app.core.database import init_database
from app.models import Track, Playlist, PlaylistEntry, PlaybackState, QueueEntry
from app.websocket.manager import manager
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI app lifecycle."""
    # Startup
    await init_database()
    print("Database initialized")

    yield

    # Shutdown
    print("Application shutting down")


class MTServer:
    """Server for mt music player with PyWebView and FastAPI."""

    def __init__(self, host=None, port=None):
        self.host = host or config('SERVER_HOST', default='127.0.0.1')
        self.port = int(port or config('SERVER_PORT', default=3000, cast=int))

        # Environment configuration
        self.debug = config('DEBUG', default=False, cast=bool)
        self.hot_reload = config('HOT_RELOAD', default=False, cast=bool)
        self.cors_enabled = config('CORS_ENABLED', default=self.debug, cast=bool)
        self.app_title = str(config('APP_TITLE', default='mt music player'))

        # Server components
        self.app = self.create_app()
        self.server_thread = None
        self.window = None
        self.observer = None

    def create_app(self):
        """Create FastAPI application."""
        app = FastAPI(title=self.app_title, debug=self.debug, lifespan=lifespan)

        # Setup Jinja2 templates
        templates = Jinja2Templates(directory="templates")

        # Register custom filters
        from templates.filters import format_duration, format_file_size, pluralize

        templates.env.filters['format_duration'] = format_duration
        templates.env.filters['format_file_size'] = format_file_size
        templates.env.filters['pluralize'] = pluralize

        # Add CORS if enabled
        if self.cors_enabled:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        @app.get("/", response_class=HTMLResponse)
        async def root_redirect():
            """Redirect root to library."""
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/library")

        @app.get("/api/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": time.time(), "mode": "development" if self.debug else "production"}

        @app.get("/api/test")
        async def test():
            """Test API endpoint."""
            return {
                "message": "API is working",
                "timestamp": time.time(),
                "server": f"{self.host}:{self.port}",
                "debug": self.debug,
                "environment": "development" if self.debug else "production",
            }

        # Include API routers
        app.include_router(library_router, prefix="/api/v1")
        app.include_router(player_router, prefix="/api/v1")
        app.include_router(queue_router, prefix="/api/v1")

        # Web routes - Library page
        @app.get("/library", response_class=HTMLResponse)
        async def library_page(request: Request):
            """Library page."""
            # For now, pass placeholder stats - will be updated with real data later
            return templates.TemplateResponse(
                "pages/library.html",
                {
                    "request": request,
                    "total_tracks": 0,
                    "total_artists": 0,
                    "total_albums": 0,
                },
            )

        # Stub API endpoints to prevent 404 errors
        @app.get("/api/playlists")
        async def get_playlists():
            """Get playlists - stub endpoint."""
            return []

        @app.get("/api/library/stats")
        async def get_library_stats_stub():
            """Get library stats - stub endpoint."""
            return "0 MB"

        @app.get("/api/library/track-count")
        async def get_track_count_stub():
            """Get track count - stub endpoint."""
            return "0"

        @app.get("/api/queue/count")
        async def get_queue_count():
            """Get queue count - stub endpoint."""
            return "0 tracks"

        @app.get("/api/queue/tracks")
        async def get_queue_tracks():
            """Get queue tracks - stub endpoint."""
            return ""

        @app.get("/api/queue/now-playing")
        async def get_now_playing():
            """Get now playing - stub endpoint."""
            return ""

        @app.get("/api/queue/duration")
        async def get_queue_duration():
            """Get queue duration - stub endpoint."""
            return "0:00"

        @app.get("/api/player/current")
        async def get_player_current():
            """Get current player state - stub endpoint."""
            return ""

        @app.get("/api/player/time")
        async def get_player_time():
            """Get player time - stub endpoint."""
            return "0:00"

        @app.get("/api/player/progress")
        async def get_player_progress():
            """Get player progress - stub endpoint."""
            return '<input type="range" min="0" max="100" value="0" class="w-full h-1 bg-[var(--bg-tertiary)] rounded-lg appearance-none cursor-pointer">'

        # Mount static files if directory exists
        static_dir = Path("static")
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory="static"), name="static")

        return app

    def start_server(self):
        """Start FastAPI server in background thread."""
        log_level = "debug" if self.debug else "info"

        def run():
            uvicorn.run(self.app, host=str(self.host), port=int(self.port), log_level=log_level)

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        time.sleep(1)  # Give server time to start

        mode = "debug" if self.debug else "production"
        print(f"FastAPI server started on http://{self.host}:{self.port} ({mode} mode)")

    def reload_browser(self):
        """Reload the browser window."""
        if self.window:
            self.window.evaluate_js("location.reload()")
            if self.debug:
                print("Browser reloaded")

    def setup_file_watcher(self):
        """Setup file watcher for hot-reload in development."""
        if not self.hot_reload:
            return

        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            print("Warning: watchdog not installed, hot-reload disabled")
            return

        class ReloadHandler(FileSystemEventHandler):
            """Handle file changes for hot-reload."""

            def __init__(self, callback):
                self.callback = callback
                self.last_reload = time.time()

            def on_modified(self, event):
                if str(event.src_path).endswith(('.py', '.html', '.css', '.js')):
                    # Debounce rapid changes
                    current_time = time.time()
                    if current_time - self.last_reload > 1:
                        self.last_reload = current_time
                        if self.callback:
                            print(f"File changed: {event.src_path}")
                            self.callback()

        self.observer = Observer()
        handler = ReloadHandler(self.reload_browser)

        # Watch current directory and subdirectories
        watch_path = Path.cwd()
        self.observer.schedule(handler, str(watch_path), recursive=True)
        self.observer.start()
        print(f"Watching {watch_path} for changes...")

    def run(self):
        """Run the server with PyWebView."""
        # Start FastAPI server
        self.start_server()

        # Create PyWebView window
        window_title = f"{self.app_title} {'[DEBUG]' if self.debug else ''}"
        self.window = webview.create_window(
            title=window_title,
            url=f'http://{self.host}:{self.port}',
            width=1200,
            height=800,
            resizable=True,
            background_color='#1e1e1e',
        )

        # Setup file watcher if hot reload is enabled
        if self.hot_reload:
            self.setup_file_watcher()

        # Expose file system API to JavaScript
        if self.window:
            from app.services.filesystem import filesystem_api

            filesystem_api.set_window(self.window)

            # Expose API methods to JavaScript
            self.window.expose(filesystem_api.open_file_dialog)
            self.window.expose(filesystem_api.open_directory_dialog)
            self.window.expose(filesystem_api.save_file_dialog)
            self.window.expose(filesystem_api.validate_paths)
            self.window.expose(filesystem_api.get_path_info)
            self.window.expose(filesystem_api.list_directory)

        # Drag and drop is handled by JavaScript in the frontend
        # PyWebView automatically provides file information to DOM events

        # Start PyWebView
        mode_text = "debug" if self.debug else "production"
        print(f"Starting PyWebView in {mode_text} mode...")
        webview.start(debug=self.debug)

        # Cleanup
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()


# Create FastAPI app instance for direct API server usage
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
if settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routers
app.include_router(library_router, prefix="/api/v1")
app.include_router(player_router, prefix="/api/v1")
app.include_router(queue_router, prefix="/api/v1")


# Web routes for standalone app
@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    """Redirect root to library."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/library")

@app.get("/library", response_class=HTMLResponse)
async def library_page(request: Request):
    """Library page."""
    return templates.TemplateResponse(
        "pages/library.html",
        {
            "request": request,
            "total_tracks": 0,
            "total_artists": 0,
            "total_albums": 0,
        }
    )

# Stub API endpoints for standalone app
@app.get("/api/playlists")
async def get_playlists_standalone():
    """Get playlists - stub endpoint."""
    return []

@app.get("/api/library/stats")
async def get_library_stats_standalone():
    """Get library stats - stub endpoint."""
    return "0 MB"

@app.get("/api/library/track-count")
async def get_track_count_standalone():
    """Get track count - stub endpoint."""
    return "0"

@app.get("/api/queue/count")
async def get_queue_count_standalone():
    """Get queue count - stub endpoint."""
    return "0 tracks"

@app.get("/api/queue/tracks")
async def get_queue_tracks_standalone():
    """Get queue tracks - stub endpoint."""
    return ""

@app.get("/api/queue/now-playing")
async def get_now_playing_standalone():
    """Get now playing - stub endpoint."""
    return ""

@app.get("/api/queue/duration")
async def get_queue_duration_standalone():
    """Get queue duration - stub endpoint."""
    return "0:00"

@app.get("/api/player/current")
async def get_player_current_standalone():
    """Get current player state - stub endpoint."""
    return ""

@app.get("/api/player/time")
async def get_player_time_standalone():
    """Get player time - stub endpoint."""
    return "0:00"

@app.get("/api/player/progress")
async def get_player_progress_standalone():
    """Get player progress - stub endpoint."""
    return '<input type="range" min="0" max="100" value="0" class="w-full h-1 bg-[var(--bg-tertiary)] rounded-lg appearance-none cursor-pointer">'


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, room: str | None = None):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can be extended for client commands
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except Exception:
        manager.disconnect(websocket, room)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Mount static files if directory exists
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MT Music Player")
    parser.add_argument('--api-only', action='store_true', help='Run FastAPI server only (no PyWebView window)')
    parser.add_argument('--host', default=None, help='Server host (default: from config)')
    parser.add_argument('--port', type=int, default=None, help='Server port (default: from config)')

    args = parser.parse_args()

    if args.api_only:
        # Run FastAPI server only
        print("Starting FastAPI server only...")
        uvicorn.run(
            "main:app",
            host=settings.SERVER_HOST if args.host is None else args.host,
            port=settings.SERVER_PORT if args.port is None else args.port,
            reload=settings.DEBUG,
            log_level="debug" if settings.DEBUG else "info",
        )
    else:
        # Run full desktop application
        server = MTServer(host=args.host, port=args.port)

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\nShutting down...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            server.run()
        except KeyboardInterrupt:
            print("\nInterrupted")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
