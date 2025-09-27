"""Queue service for managing playback queue."""

import random
from app.models.queue import QueueEntry
from app.schemas.queue import QueueEntryResponse
from app.websocket.manager import EventTypes, broadcast_queue_event
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional


class QueueService:
    """Service for managing playback queue."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_queue(self, queue_name: str = "default") -> list[QueueEntryResponse]:
        """Get all entries in a queue."""
        query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name
        ).options(
            selectinload(QueueEntry.track)
        ).order_by(QueueEntry.position)
        
        result = await self.db.execute(query)
        entries = result.scalars().all()
        
        return [
            QueueEntryResponse(
                id=entry.id,
                position=entry.position,
                queue_name=entry.queue_name,
                added_at=entry.added_at,
                track=entry.track
            )
            for entry in entries
        ]

    async def add_tracks(
        self,
        track_ids: list[int],
        queue_name: str = "default",
        insert_position: int | None = None
    ) -> list[QueueEntryResponse]:
        """Add tracks to the queue."""
        # Get current queue size
        count_query = select(QueueEntry).where(QueueEntry.queue_name == queue_name)
        count_result = await self.db.execute(count_query)
        current_entries = count_result.scalars().all()
        
        if insert_position is None:
            # Append to end
            start_position = len(current_entries)
        else:
            # Insert at specific position
            start_position = insert_position
            # Shift existing entries
            for entry in current_entries:
                if entry.position >= start_position:
                    entry.position += len(track_ids)
        
        # Create new entries
        new_entries = []
        for i, track_id in enumerate(track_ids):
            entry = QueueEntry(
                track_id=track_id,
                position=start_position + i,
                queue_name=queue_name
            )
            self.db.add(entry)
            new_entries.append(entry)
        
        await self.db.commit()
        
        # Reload with relationships
        for entry in new_entries:
            await self.db.refresh(entry)
        
        # Broadcast event
        await broadcast_queue_event(EventTypes.QUEUE_UPDATED, queue_name, {
            "added": len(track_ids)
        })
        
        return [
            QueueEntryResponse(
                id=entry.id,
                position=entry.position,
                queue_name=entry.queue_name,
                added_at=entry.added_at,
                track=entry.track
            )
            for entry in new_entries
        ]

    async def remove_entry(self, entry_id: int):
        """Remove an entry from the queue."""
        # Get the entry
        query = select(QueueEntry).where(QueueEntry.id == entry_id)
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            return
        
        queue_name = entry.queue_name
        position = entry.position
        
        # Delete the entry
        await self.db.delete(entry)
        
        # Shift positions of entries after the removed one
        update_query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name,
            QueueEntry.position > position
        )
        update_result = await self.db.execute(update_query)
        entries_to_update = update_result.scalars().all()
        
        for entry in entries_to_update:
            entry.position -= 1
        
        await self.db.commit()
        
        # Broadcast event
        await broadcast_queue_event(EventTypes.TRACK_REMOVED, queue_name, {
            "removed_position": position
        })

    async def move_entry(self, entry_id: int, new_position: int):
        """Move an entry to a new position in the queue."""
        # Get the entry
        query = select(QueueEntry).where(QueueEntry.id == entry_id)
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            return
        
        queue_name = entry.queue_name
        old_position = entry.position
        
        if old_position == new_position:
            return
        
        # Get all entries in the queue
        all_query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name
        ).order_by(QueueEntry.position)
        all_result = await self.db.execute(all_query)
        all_entries = all_result.scalars().all()
        
        # Reorder entries
        if old_position < new_position:
            # Moving down
            for e in all_entries:
                if old_position < e.position <= new_position:
                    e.position -= 1
        else:
            # Moving up
            for e in all_entries:
                if new_position <= e.position < old_position:
                    e.position += 1
        
        # Set the new position
        entry.position = new_position
        
        await self.db.commit()
        
        # Broadcast event
        await broadcast_queue_event(EventTypes.QUEUE_UPDATED, queue_name, {
            "moved": {"from": old_position, "to": new_position}
        })

    async def clear_queue(self, queue_name: str = "default"):
        """Clear all entries from a queue."""
        query = delete(QueueEntry).where(QueueEntry.queue_name == queue_name)
        await self.db.execute(query)
        await self.db.commit()
        
        # Broadcast event
        await broadcast_queue_event(EventTypes.QUEUE_CLEARED, queue_name, {})

    async def shuffle_queue(self, queue_name: str = "default"):
        """Shuffle the queue randomly."""
        # Get all entries
        query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name
        ).order_by(QueueEntry.position)
        result = await self.db.execute(query)
        entries = result.scalars().all()
        
        if not entries:
            return
        
        # Shuffle positions
        positions = list(range(len(entries)))
        random.shuffle(positions)
        
        for entry, new_pos in zip(entries, positions, strict=False):
            entry.position = new_pos
        
        await self.db.commit()
        
        # Broadcast event
        await broadcast_queue_event(EventTypes.QUEUE_UPDATED, queue_name, {
            "shuffled": True
        })