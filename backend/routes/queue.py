"""Queue routes for the mt music player API."""

from backend.services.database import DatabaseService, get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/queue", tags=["queue"])


class QueueAddRequest(BaseModel):
    """Request to add tracks to the queue."""

    track_ids: list[int] = Field(min_length=1)
    position: int | None = None


class QueueAddFilesRequest(BaseModel):
    """Request to add files directly to the queue."""

    filepaths: list[str] = Field(min_length=1)
    position: int | None = None


class QueueReorderRequest(BaseModel):
    """Request to reorder tracks in the queue."""

    from_position: int = Field(ge=0)
    to_position: int = Field(ge=0)


class QueueShuffleRequest(BaseModel):
    """Request to shuffle the queue."""

    keep_current: bool = True


@router.get("")
async def get_queue(db: DatabaseService = Depends(get_db)):
    """Get the current playback queue."""
    items = db.get_queue()
    return {
        "items": items,
        "count": len(items),
    }


@router.post("/add", status_code=201)
async def add_to_queue(request: QueueAddRequest, db: DatabaseService = Depends(get_db)):
    """Add track(s) to the queue."""
    added = db.add_to_queue(request.track_ids, request.position)
    queue_length = db.get_queue_length()
    return {
        "added": added,
        "queue_length": queue_length,
    }


@router.post("/add-files", status_code=201)
async def add_files_to_queue(request: QueueAddFilesRequest, db: DatabaseService = Depends(get_db)):
    """Add files directly to the queue (for drag-and-drop)."""
    added, tracks = db.add_files_to_queue(request.filepaths, request.position)
    queue_length = db.get_queue_length()
    return {
        "added": added,
        "queue_length": queue_length,
        "tracks": tracks,
    }


@router.delete("/{position}", status_code=204)
async def remove_from_queue(position: int, db: DatabaseService = Depends(get_db)):
    """Remove a track from the queue by position."""
    if not db.remove_from_queue(position):
        raise HTTPException(status_code=404, detail=f"No track at position {position}")


@router.post("/clear", status_code=204)
async def clear_queue(db: DatabaseService = Depends(get_db)):
    """Clear the entire queue."""
    db.clear_queue()


@router.post("/reorder")
async def reorder_queue(request: QueueReorderRequest, db: DatabaseService = Depends(get_db)):
    """Reorder tracks in the queue."""
    if not db.reorder_queue(request.from_position, request.to_position):
        raise HTTPException(status_code=400, detail="Invalid positions")
    return {
        "success": True,
        "queue_length": db.get_queue_length(),
    }


@router.post("/shuffle")
async def shuffle_queue(request: QueueShuffleRequest, db: DatabaseService = Depends(get_db)):
    """Shuffle the queue."""
    import random

    items = db.get_queue()
    if not items:
        return {"success": True, "queue_length": 0}

    # Get filepaths
    filepaths = [item["track"]["filepath"] for item in items]

    if request.keep_current and filepaths:
        # Keep first item, shuffle rest
        first = filepaths[0]
        rest = filepaths[1:]
        random.shuffle(rest)
        filepaths = [first] + rest
    else:
        random.shuffle(filepaths)

    # Rebuild queue
    db.clear_queue()
    for filepath in filepaths:
        # Get track ID for filepath
        track = db.get_track_by_filepath(filepath)
        if track:
            db.add_to_queue([track["id"]])

    return {
        "success": True,
        "queue_length": db.get_queue_length(),
    }
