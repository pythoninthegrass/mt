"""Library API endpoints."""

from app.core.database import get_async_session
from app.models.track import Track
from app.schemas.track import TrackCreate, TrackResponse, TrackUpdate
from app.services.library import LibraryService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/tracks", response_model=list[TrackResponse])
async def get_tracks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    artist: str | None = None,
    album: str | None = None,
    genre: str | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    """Get all tracks with optional filtering."""
    query = select(Track)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Track.title.ilike(search_term),
                Track.artist.ilike(search_term),
                Track.album.ilike(search_term),
            )
        )
    
    if artist:
        query = query.where(Track.artist.ilike(f"%{artist}%"))
    
    if album:
        query = query.where(Track.album.ilike(f"%{album}%"))
    
    if genre:
        query = query.where(Track.genre.ilike(f"%{genre}%"))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    tracks = result.scalars().all()
    
    return tracks


@router.get("/tracks/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific track by ID."""
    query = select(Track).where(Track.id == track_id)
    result = await db.execute(query)
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return track


@router.put("/tracks/{track_id}", response_model=TrackResponse)
async def update_track(
    track_id: int,
    track_update: TrackUpdate,
    db: AsyncSession = Depends(get_async_session),
):
    """Update track metadata."""
    query = select(Track).where(Track.id == track_id)
    result = await db.execute(query)
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Update fields
    update_data = track_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(track, field, value)
    
    await db.commit()
    await db.refresh(track)
    
    return track


@router.delete("/tracks/{track_id}")
async def delete_track(
    track_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a track from the library."""
    query = select(Track).where(Track.id == track_id)
    result = await db.execute(query)
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    await db.delete(track)
    await db.commit()
    
    return {"message": "Track deleted successfully"}


@router.post("/scan")
async def scan_library(
    path: str | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_session),
):
    """Initiate a library scan."""
    library_service = LibraryService(db)
    
    # Start scan in background
    background_tasks.add_task(library_service.scan_directory, path)
    
    return {
        "message": "Library scan initiated",
        "path": path or "Default music library",
        "status": "scanning"
    }


@router.get("/stats")
async def get_library_stats(
    db: AsyncSession = Depends(get_async_session),
):
    """Get library statistics."""
    # Get total tracks
    total_query = select(func.count(Track.id))
    total_result = await db.execute(total_query)
    total_tracks = total_result.scalar() or 0
    
    # Get total duration
    duration_query = select(func.sum(Track.duration))
    duration_result = await db.execute(duration_query)
    total_duration = duration_result.scalar() or 0
    
    # Get unique artists
    artists_query = select(func.count(func.distinct(Track.artist)))
    artists_result = await db.execute(artists_query)
    unique_artists = artists_result.scalar() or 0
    
    # Get unique albums
    albums_query = select(func.count(func.distinct(Track.album)))
    albums_result = await db.execute(albums_query)
    unique_albums = albums_result.scalar() or 0
    
    # Get total file size
    size_query = select(func.sum(Track.file_size))
    size_result = await db.execute(size_query)
    total_size = size_result.scalar() or 0
    
    return {
        "total_tracks": total_tracks,
        "total_duration": total_duration,
        "unique_artists": unique_artists,
        "unique_albums": unique_albums,
        "total_size": total_size,
        "total_size_gb": round(total_size / (1024 ** 3), 2) if total_size else 0,
    }


@router.get("/artists")
async def get_artists(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    """Get all unique artists."""
    query = select(Track.artist, func.count(Track.id).label("track_count")).where(
        Track.artist.isnot(None)
    ).group_by(Track.artist)
    
    if search:
        query = query.where(Track.artist.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    artists = result.all()
    
    return [
        {"artist": artist, "track_count": count}
        for artist, count in artists
    ]


@router.get("/albums")
async def get_albums(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    artist: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    """Get all unique albums."""
    query = select(
        Track.album,
        Track.artist,
        Track.year,
        func.count(Track.id).label("track_count")
    ).where(Track.album.isnot(None)).group_by(Track.album, Track.artist, Track.year)
    
    if artist:
        query = query.where(Track.artist.ilike(f"%{artist}%"))
    
    if search:
        query = query.where(Track.album.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    albums = result.all()
    
    return [
        {
            "album": album,
            "artist": artist,
            "year": year,
            "track_count": count
        }
        for album, artist, year, count in albums
    ]