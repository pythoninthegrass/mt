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
    parallel: bool = True  # Enable parallel metadata parsing
    max_workers: int | None = None  # Max parallel workers (None = CPU count)


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
    sort_by: Literal["title", "artist", "album", "added_date", "play_count", "last_played"] = "added_date",
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = Query(100, ge=1, le=10000),
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


@router.put("/{track_id}/rescan")
async def rescan_track(track_id: int, db: DatabaseService = Depends(get_db)):
    """Rescan a track's metadata from its file and update the database."""
    track = db.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")

    filepath = track.get("filepath")
    if not filepath:
        raise HTTPException(status_code=400, detail="Track has no filepath")

    from backend.services.scanner import extract_metadata

    metadata = extract_metadata(filepath)

    if not db.update_track_metadata(track_id, metadata):
        raise HTTPException(status_code=500, detail="Failed to update track metadata")

    return db.get_track_by_id(track_id)


@router.put("/{track_id}/play-count")
async def update_play_count(track_id: int, db: DatabaseService = Depends(get_db)):
    """Increment play count for a track."""
    result = db.update_play_count(track_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")
    return result


@router.post("/scan", response_model=ScanResult)
async def scan_library(request: ScanRequest, db: DatabaseService = Depends(get_db)):
    """Scan paths for audio files using 2-phase approach for optimal performance.

    Phase 1: Inventory - Walk filesystem + stat + fingerprint comparison (fast)
    Phase 2: Parse - Extract metadata only for changed files (slower but minimal)
    """
    print(f"[scan] Received request to scan {len(request.paths)} paths: {request.paths}")

    # Import 2-phase scanner
    from backend.services.scanner_2phase import parse_changed_files, scan_library_2phase

    # Phase 1: Inventory - Get DB fingerprints and classify files
    db_fingerprints = db.get_all_fingerprints()
    print(f"[scan] Database has {len(db_fingerprints)} existing tracks")

    changes, stats = scan_library_2phase(request.paths, db_fingerprints, recursive=request.recursive)

    print(
        f"[scan] Inventory complete: {stats.visited} files scanned, "
        f"{stats.added} added, {stats.modified} modified, "
        f"{stats.unchanged} unchanged, {stats.deleted} deleted"
    )

    # Phase 2: Parse metadata only for changed files (added + modified)
    files_to_parse = changes["added"] + changes["modified"]
    parsed_files = []

    if files_to_parse:
        parse_mode = "parallel" if request.parallel and len(files_to_parse) >= 20 else "serial"
        print(f"[scan] Parsing metadata for {len(files_to_parse)} changed files ({parse_mode})...")
        parsed_files = parse_changed_files(files_to_parse, parallel=request.parallel, max_workers=request.max_workers)
        print(f"[scan] Parsed {len(parsed_files)} files")

    # Split parsed files into added vs modified
    added_set = {fp for fp, _ in changes["added"]}
    files_to_add = [(fp, meta) for fp, meta in parsed_files if fp in added_set]
    files_to_update = [(fp, meta) for fp, meta in parsed_files if fp not in added_set]

    # Apply changes to database
    added = 0
    updated = 0
    deleted = 0
    errors = 0

    try:
        if files_to_add:
            added = db.add_tracks_bulk(files_to_add)
            print(f"[scan] Added {added} new tracks")

        if files_to_update:
            updated = db.update_tracks_bulk(files_to_update)
            print(f"[scan] Updated {updated} modified tracks")

        if changes["deleted"]:
            deleted = db.delete_tracks_bulk(changes["deleted"])
            print(f"[scan] Deleted {deleted} removed tracks")

    except Exception as e:
        print(f"[scan] Error during database operations: {e}")
        errors = len(files_to_parse)

    # Get recently added/updated tracks for response
    result_tracks = []
    if added > 0 or updated > 0:
        tracks, _ = db.get_all_tracks(sort_by="added_date", sort_order="desc", limit=min(added + updated, 100))
        result_tracks = tracks

    return ScanResult(
        added=added,
        skipped=stats.unchanged,
        errors=stats.errors + errors,
        tracks=result_tracks,
    )


# ==================== Missing Tracks Endpoints ====================


class LocateFileRequest(BaseModel):
    """Request body for locating a missing file."""

    new_path: str


class MissingTrackResponse(BaseModel):
    """Response for missing track operations."""

    id: int
    filepath: str
    title: str | None
    artist: str | None
    album: str | None
    missing: bool
    last_seen_at: int | None


@router.get("/missing")
async def get_missing_tracks(db: DatabaseService = Depends(get_db)):
    """Get all tracks marked as missing."""
    tracks = db.get_missing_tracks()
    return {"tracks": tracks, "total": len(tracks)}


@router.post("/{track_id}/locate")
async def locate_track(
    track_id: int,
    request: LocateFileRequest,
    db: DatabaseService = Depends(get_db),
):
    """Update a missing track's filepath after user locates the file.

    Returns the updated track if successful.
    """
    import os

    # Verify the track exists
    track = db.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")

    # Verify the new path exists
    if not os.path.exists(request.new_path):
        raise HTTPException(status_code=400, detail=f"File not found: {request.new_path}")

    # Update the filepath
    if not db.update_track_filepath(track_id, request.new_path):
        raise HTTPException(status_code=500, detail="Failed to update track filepath")

    return db.get_track_by_id(track_id)


@router.post("/{track_id}/check-status")
async def check_track_status(track_id: int, db: DatabaseService = Depends(get_db)):
    """Check if a track's file exists and update its missing status.

    Returns the updated track with current missing status.
    """
    track = db.check_and_update_track_status(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")
    return track


@router.post("/{track_id}/mark-missing")
async def mark_track_missing(track_id: int, db: DatabaseService = Depends(get_db)):
    """Manually mark a track as missing."""
    if not db.mark_track_missing(track_id):
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")
    return db.get_track_by_id(track_id)


@router.post("/{track_id}/mark-present")
async def mark_track_present(track_id: int, db: DatabaseService = Depends(get_db)):
    """Manually mark a track as present (not missing)."""
    if not db.mark_track_present(track_id):
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found")
    return db.get_track_by_id(track_id)
