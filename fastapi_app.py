#!/usr/bin/env python3
"""FastAPI application for mt music player."""

from app.api.v1.library import router as library_router
from app.api.v1.player import router as player_router
from app.api.v1.queue import router as queue_router
from app.core.config import settings
from app.core.database import init_database
from app.websocket.manager import manager
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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


# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG, lifespan=lifespan)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_app:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
