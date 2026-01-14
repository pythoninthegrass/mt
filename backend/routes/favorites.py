"""Favorites routes for the mt music player API."""

from backend.services.database import DatabaseService, get_db
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("")
async def get_favorites(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: DatabaseService = Depends(get_db),
):
    """Get all favorited tracks (Liked Songs)."""
    tracks, total = db.get_favorites(limit=limit, offset=offset)
    return {
        "tracks": tracks,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/top25")
async def get_top_25(db: DatabaseService = Depends(get_db)):
    """Get top 25 most played tracks."""
    tracks = db.get_top_25()
    return {"tracks": tracks}


@router.get("/recently-played")
async def get_recently_played(
    days: int = Query(14, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db: DatabaseService = Depends(get_db),
):
    """Get tracks played within the last N days."""
    tracks = db.get_recently_played(days=days, limit=limit)
    return {"tracks": tracks, "days": days}


@router.get("/recently-added")
async def get_recently_added(
    days: int = Query(14, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db: DatabaseService = Depends(get_db),
):
    """Get tracks added within the last N days."""
    tracks = db.get_recently_added(days=days, limit=limit)
    return {"tracks": tracks, "days": days}


@router.get("/{track_id}")
async def check_favorite(track_id: int, db: DatabaseService = Depends(get_db)):
    """Check if a track is favorited."""
    is_fav, favorited_date = db.is_favorite(track_id)
    return {
        "is_favorite": is_fav,
        "favorited_date": favorited_date,
    }


@router.post("/{track_id}", status_code=201)
async def add_favorite(track_id: int, db: DatabaseService = Depends(get_db)):
    """Add a track to favorites."""
    # Check track exists
    track = db.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")

    favorited_date = db.add_favorite(track_id)
    if not favorited_date:
        raise HTTPException(status_code=409, detail="Track is already favorited")

    return {
        "success": True,
        "favorited_date": favorited_date,
    }


@router.delete("/{track_id}", status_code=204)
async def remove_favorite(track_id: int, db: DatabaseService = Depends(get_db)):
    """Remove a track from favorites."""
    if not db.remove_favorite(track_id):
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not in favorites")
