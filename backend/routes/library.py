"""Library routes for the mt music player API."""

from backend.services.database import DatabaseService, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Literal

router = APIRouter(prefix="/library", tags=["library"])


@router.get("")
async def get_library(
    search: str | None = None,
    artist: str | None = None,
    album: str | None = None,
    sort_by: Literal["title", "artist", "album", "added_date", "play_count"] = "added_date",
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseService = Depends(get_db),
):
    """Get all tracks in the library with optional filtering and pagination."""
    tracks, total = db.get_all_tracks(
        search=search,
        artist=artist,
        album=album,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return {
        "tracks": tracks,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_library_stats(db: DatabaseService = Depends(get_db)):
    """Get library statistics."""
    return db.get_library_stats()


@router.get("/{track_id}")
async def get_track(track_id: int, db: DatabaseService = Depends(get_db)):
    """Get a single track by ID."""
    track = db.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")
    return track


@router.delete("/{track_id}", status_code=204)
async def delete_track(track_id: int, db: DatabaseService = Depends(get_db)):
    """Remove a track from the library."""
    if not db.delete_track(track_id):
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")


@router.put("/{track_id}/play-count")
async def update_play_count(track_id: int, db: DatabaseService = Depends(get_db)):
    """Increment play count for a track."""
    result = db.update_play_count(track_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")
    return result
