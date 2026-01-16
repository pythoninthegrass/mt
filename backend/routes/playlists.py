"""Playlists routes for the mt music player API."""

from backend.services.database import DatabaseService, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/playlists", tags=["playlists"])


class PlaylistCreateRequest(BaseModel):
    """Request to create a new playlist."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class PlaylistUpdateRequest(BaseModel):
    """Request to update playlist metadata."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class PlaylistAddTracksRequest(BaseModel):
    """Request to add tracks to a playlist."""

    track_ids: list[int] = Field(min_length=1)
    position: int | None = None


class PlaylistReorderRequest(BaseModel):
    """Request to reorder tracks within a playlist."""

    from_position: int = Field(ge=0)
    to_position: int = Field(ge=0)


class PlaylistsReorderRequest(BaseModel):
    """Request to reorder playlists in the sidebar."""

    from_position: int = Field(ge=0)
    to_position: int = Field(ge=0)


@router.get("")
async def get_playlists(db: DatabaseService = Depends(get_db)):
    """Get all playlists."""
    playlists = db.get_playlists()
    return {"playlists": playlists}


@router.get("/generate-name")
async def generate_playlist_name(base: str = "New playlist", db: DatabaseService = Depends(get_db)):
    """Generate a unique playlist name."""
    name = db.generate_unique_playlist_name(base)
    return {"name": name}


@router.post("", status_code=201)
async def create_playlist(request: PlaylistCreateRequest, db: DatabaseService = Depends(get_db)):
    """Create a new playlist."""
    playlist = db.create_playlist(request.name, request.description)
    if not playlist:
        raise HTTPException(status_code=409, detail=f"Playlist with name '{request.name}' already exists")
    return playlist


@router.post("/reorder")
async def reorder_playlists(
    request: PlaylistsReorderRequest,
    db: DatabaseService = Depends(get_db),
):
    """Reorder playlists in the sidebar."""
    if not db.reorder_playlists(request.from_position, request.to_position):
        raise HTTPException(status_code=400, detail="Invalid positions")

    return {"success": True}


@router.get("/{playlist_id}")
async def get_playlist(playlist_id: int, db: DatabaseService = Depends(get_db)):
    """Get a playlist with its tracks."""
    playlist = db.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with id {playlist_id} not found")
    return playlist


@router.put("/{playlist_id}")
async def update_playlist(playlist_id: int, request: PlaylistUpdateRequest, db: DatabaseService = Depends(get_db)):
    """Update playlist metadata."""
    playlist = db.update_playlist(playlist_id, request.name)
    if not playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with id {playlist_id} not found or name conflict")
    return playlist


@router.delete("/{playlist_id}", status_code=204)
async def delete_playlist(playlist_id: int, db: DatabaseService = Depends(get_db)):
    """Delete a playlist."""
    if not db.delete_playlist(playlist_id):
        raise HTTPException(status_code=404, detail=f"Playlist with id {playlist_id} not found")


@router.post("/{playlist_id}/tracks", status_code=201)
async def add_tracks_to_playlist(
    playlist_id: int,
    request: PlaylistAddTracksRequest,
    db: DatabaseService = Depends(get_db),
):
    """Add tracks to a playlist."""
    # Check playlist exists
    playlist = db.get_playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with id {playlist_id} not found")

    added = db.add_tracks_to_playlist(playlist_id, request.track_ids, request.position)
    track_count = db.get_playlist_track_count(playlist_id)

    return {
        "added": added,
        "playlist_track_count": track_count,
    }


@router.delete("/{playlist_id}/tracks/{position}", status_code=204)
async def remove_track_from_playlist(
    playlist_id: int,
    position: int,
    db: DatabaseService = Depends(get_db),
):
    """Remove a track from a playlist by position."""
    if not db.remove_track_from_playlist(playlist_id, position):
        raise HTTPException(status_code=404, detail=f"Track at position {position} not found in playlist")


@router.post("/{playlist_id}/tracks/reorder")
async def reorder_playlist(
    playlist_id: int,
    request: PlaylistReorderRequest,
    db: DatabaseService = Depends(get_db),
):
    """Reorder tracks within a playlist."""
    if not db.reorder_playlist(playlist_id, request.from_position, request.to_position):
        raise HTTPException(status_code=400, detail="Invalid positions")

    return {
        "success": True,
        "playlist_track_count": db.get_playlist_track_count(playlist_id),
    }
