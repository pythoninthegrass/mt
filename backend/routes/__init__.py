"""API routes for the mt music player backend."""

from backend.routes.favorites import router as favorites_router
from backend.routes.library import router as library_router
from backend.routes.playlists import router as playlists_router
from backend.routes.queue import router as queue_router
from backend.routes.settings import router as settings_router
from backend.routes.watched_folders import router as watched_folders_router
from backend.routes.websocket import router as websocket_router

__all__ = [
    "library_router",
    "queue_router",
    "playlists_router",
    "favorites_router",
    "settings_router",
    "watched_folders_router",
    "websocket_router",
]
