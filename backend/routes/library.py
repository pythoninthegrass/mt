"""Library routes for the mt music player API."""

from backend.services.artwork import get_artwork
from backend.services.database import DatabaseService, get_db
from backend.services.scanner import scan_paths
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/library", tags=["library"])


class ScanRequest(BaseModel):
    """Request body for library scan."""

    paths: list[str]
    recursive: bool = True


class ScanResult(BaseModel):
    """Result of a library scan."""

    added: int
    skipped: int
    errors: int
    tracks: list[dict]


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
    db.update_file_sizes()
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


@router.get("/{track_id}/artwork")
async def get_track_artwork(track_id: int, db: DatabaseService = Depends(get_db)):
    """Get album artwork for a track.

    Returns base64-encoded image data with mime type.
    Tries embedded artwork first, then folder-based artwork.
    """
    track = db.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")

    filepath = track.get("filepath")
    if not filepath:
        raise HTTPException(status_code=404, detail="Track has no filepath")

    artwork = get_artwork(filepath)
    if not artwork:
        raise HTTPException(status_code=404, detail="No artwork found for this track")

    return artwork


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


@router.post("/scan", response_model=ScanResult)
async def scan_library(request: ScanRequest, db: DatabaseService = Depends(get_db)):
    """Scan paths for audio files and add them to the library."""
    print(f"[scan] Received request to scan {len(request.paths)} paths: {request.paths}")
    scanned = scan_paths(request.paths, recursive=request.recursive)
    print(f"[scan] Found {len(scanned)} audio files")

    added = 0
    skipped = 0
    errors = 0
    added_tracks = []

    for item in scanned:
        filepath = item["filepath"]
        metadata = item["metadata"]

        try:
            # Check if track already exists
            existing = db.get_track_by_filepath(filepath)
            if existing:
                skipped += 1
                continue

            # Add to library
            track_id = db.add_track(filepath, metadata)
            if track_id:
                added += 1
                track = db.get_track_by_id(track_id)
                if track:
                    added_tracks.append(track)
            else:
                errors += 1
        except Exception as e:
            print(f"Error adding track {filepath}: {e}")
            errors += 1

    return ScanResult(
        added=added,
        skipped=skipped,
        errors=errors,
        tracks=added_tracks,
    )
