"""Queue API endpoints."""

from app.core.database import get_async_session
from app.models.queue import QueueEntry
from app.models.track import Track
from app.schemas.queue import (
    QueueEntryCreate,
    QueueEntryResponse,
    QueueResponse,
)
from app.services.queue import QueueService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/{queue_name}", response_model=QueueResponse)
async def get_queue(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Get all entries in a queue."""
    queue_service = QueueService(db)
    entries = await queue_service.get_queue(queue_name)
    
    return QueueResponse(
        queue_name=queue_name,
        entries=entries,
        total=len(entries)
    )


@router.post("/{queue_name}/add", response_model=list[QueueEntryResponse])
async def add_to_queue(
    queue_add: QueueEntryCreate,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Add tracks to queue."""
    queue_service = QueueService(db)
    
    # Verify tracks exist
    for track_id in queue_add.track_ids:
        query = select(Track).where(Track.id == track_id)
        result = await db.execute(query)
        track = result.scalar_one_or_none()
        if not track:
            raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    
    # Add tracks to queue
    entries = await queue_service.add_tracks(
        track_ids=queue_add.track_ids,
        queue_name=queue_name,
        insert_position=queue_add.insert_position
    )
    
    return entries


@router.delete("/{queue_name}/entry/{entry_id}")
async def remove_from_queue(
    entry_id: int,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Remove an entry from queue."""
    queue_service = QueueService(db)
    
    # Check if entry exists
    query = select(QueueEntry).where(
        QueueEntry.id == entry_id,
        QueueEntry.queue_name == queue_name
    )
    result = await db.execute(query)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Queue entry not found")
    
    await queue_service.remove_entry(entry_id)
    
    return {"message": "Entry removed from queue"}


@router.put("/{queue_name}/entry/{entry_id}/move")
async def move_queue_entry(
    entry_id: int,
    new_position: int,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Move an entry to a new position in the queue."""
    queue_service = QueueService(db)
    
    # Check if entry exists
    query = select(QueueEntry).where(
        QueueEntry.id == entry_id,
        QueueEntry.queue_name == queue_name
    )
    result = await db.execute(query)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Queue entry not found")
    
    await queue_service.move_entry(entry_id, new_position)
    
    return {"message": "Entry moved successfully"}


@router.delete("/{queue_name}/clear")
async def clear_queue(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Clear all entries from a queue."""
    queue_service = QueueService(db)
    await queue_service.clear_queue(queue_name)
    
    return {"message": f"Queue '{queue_name}' cleared"}


@router.post("/{queue_name}/shuffle")
async def shuffle_queue(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Shuffle the queue randomly."""
    queue_service = QueueService(db)
    await queue_service.shuffle_queue(queue_name)
    
    return {"message": f"Queue '{queue_name}' shuffled"}