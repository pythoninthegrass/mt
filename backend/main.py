"""FastAPI backend for the mt music player.

This is the main entry point for the Python backend sidecar.
It provides REST API endpoints for library, queue, playlists,
favorites, and settings management.
"""

import os
import time
from backend.routes.favorites import router as favorites_router
from backend.routes.lastfm import router as lastfm_router
from backend.routes.library import router as library_router
from backend.routes.playlists import router as playlists_router
from backend.routes.queue import router as queue_router
from backend.routes.settings import router as settings_router
from backend.routes.websocket import router as websocket_router
from backend.services.database import init_db
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Version
__version__ = "1.0.0"

# Track startup time for health check
_start_time: float = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _start_time
    _start_time = time.time()

    # Initialize database
    # Use environment variable or default to mt.db in current directory
    db_path = os.environ.get("MT_DB_PATH", "mt.db")
    init_db(db_path)

    print(f"mt backend v{__version__} started")
    print(f"Database: {db_path}")

    yield

    print("mt backend shutting down")


# Create FastAPI app
app = FastAPI(
    title="mt Music Player API",
    description="REST API for the mt music player",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS for Tauri webview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(library_router, prefix="/api")
app.include_router(queue_router, prefix="/api")
app.include_router(playlists_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(lastfm_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(websocket_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from backend.services.database import get_db

    try:
        db = get_db()
        # Quick database check
        with db.get_connection() as conn:
            conn.cursor().execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "error"

    uptime = int(time.time() - _start_time) if _start_time else 0

    return {
        "status": "healthy",
        "version": __version__,
        "database": db_status,
        "uptime_seconds": uptime,
    }


def run():
    """Entry point for running the server (used by PEX)."""
    import uvicorn

    port = int(os.environ.get("MT_API_PORT", "8765"))
    host = os.environ.get("MT_API_HOST", "127.0.0.1")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    run()
