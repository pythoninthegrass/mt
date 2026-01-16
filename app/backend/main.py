from __future__ import annotations

import os
import signal
import sys
import uvicorn
from contextlib import asynccontextmanager
from core.db import DB_TABLES, MusicDatabase
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

HOST = os.getenv("MT_SIDECAR_HOST", "127.0.0.1")
# MT_API_PORT is set by Tauri sidecar, MT_SIDECAR_PORT is legacy/dev fallback
PORT = int(os.getenv("MT_API_PORT", os.getenv("MT_SIDECAR_PORT", "5556")))
DB_PATH = os.getenv("MT_DB_PATH", os.path.expanduser("~/.mt/mt.db"))

# Database instance (initialized in lifespan)
db: MusicDatabase | None = None


# Pydantic models for request/response
class PlaylistCreate(BaseModel):
    name: str


class PlaylistRename(BaseModel):
    name: str


class PlaylistAddTracks(BaseModel):
    track_ids: list[int]


class PlaylistRemoveTracks(BaseModel):
    track_ids: list[int]


class PlaylistReorder(BaseModel):
    track_ids: list[int]


shutdown_event: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global db
    print(f"MT Sidecar starting on {HOST}:{PORT}", file=sys.stderr)
    db = MusicDatabase(DB_PATH, DB_TABLES)
    yield
    print("MT Sidecar shutting down", file=sys.stderr)
    if db:
        db.close()


app = FastAPI(title="MT Sidecar", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/shutdown")
async def shutdown() -> dict[str, str]:
    global shutdown_event
    shutdown_event = True
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting_down"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "mt-sidecar", "version": "0.1.0"}


@app.get("/api/playlists")
async def list_playlists() -> list[dict]:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    playlists = db.list_playlists()
    return [{"id": pid, "name": name} for pid, name in playlists]


@app.post("/api/playlists")
async def create_playlist(data: PlaylistCreate) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        playlist_id = db.create_playlist(data.name)
        return {"id": playlist_id, "name": data.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/playlists/generate-name")
async def generate_playlist_name(base: str = "New playlist") -> dict:
    """Generate a unique playlist name with auto-suffix if needed."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    name = db.generate_unique_name(base)
    return {"name": name}


@app.get("/api/playlists/{playlist_id}")
async def get_playlist(playlist_id: int) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    name = db.get_playlist_name(playlist_id)
    if not name:
        raise HTTPException(status_code=404, detail="Playlist not found")
    items = db.get_playlist_items(playlist_id)
    tracks = [
        {
            "id": track_id,
            "filepath": filepath,
            "artist": artist,
            "title": title,
            "album": album,
            "track_number": track_number,
            "date": date,
        }
        for filepath, artist, title, album, track_number, date, track_id in items
    ]
    return {"id": playlist_id, "name": name, "tracks": tracks}


@app.put("/api/playlists/{playlist_id}")
async def rename_playlist(playlist_id: int, data: PlaylistRename) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        success = db.rename_playlist(playlist_id, data.name)
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return {"id": playlist_id, "name": data.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.delete("/api/playlists/{playlist_id}")
async def delete_playlist(playlist_id: int) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    success = db.delete_playlist(playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"success": True}


@app.post("/api/playlists/{playlist_id}/tracks")
async def add_tracks_to_playlist(playlist_id: int, data: PlaylistAddTracks) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    name = db.get_playlist_name(playlist_id)
    if not name:
        raise HTTPException(status_code=404, detail="Playlist not found")
    added = db.add_tracks_to_playlist(playlist_id, data.track_ids)
    return {"added": added}


@app.delete("/api/playlists/{playlist_id}/tracks")
async def remove_tracks_from_playlist(playlist_id: int, data: PlaylistRemoveTracks) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    name = db.get_playlist_name(playlist_id)
    if not name:
        raise HTTPException(status_code=404, detail="Playlist not found")
    removed = db.remove_tracks_from_playlist(playlist_id, data.track_ids)
    return {"removed": removed}


@app.post("/api/playlists/{playlist_id}/reorder")
async def reorder_playlist(playlist_id: int, data: PlaylistReorder) -> dict:
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    name = db.get_playlist_name(playlist_id)
    if not name:
        raise HTTPException(status_code=404, detail="Playlist not found")
    db.reorder_playlist(playlist_id, data.track_ids)
    return {"success": True}


def main() -> None:
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
