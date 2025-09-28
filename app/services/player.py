"""Player service for managing playback state."""

from app.models.queue import PlaybackState, QueueEntry
from app.models.track import Track
from app.schemas.queue import PlaybackStateResponse, PlaybackStateUpdate
from app.websocket.manager import EventTypes, broadcast_player_event
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional


class PlayerService:
    """Service for managing playback state."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_state(self, queue_name: str = "default") -> PlaybackStateResponse | None:
        """Get current playback state."""
        query = select(PlaybackState).where(
            PlaybackState.queue_name == queue_name
        ).options(
            selectinload(PlaybackState.current_track)
        )
        
        result = await self.db.execute(query)
        state = result.scalar_one_or_none()
        
        if not state:
            return None
        
        return PlaybackStateResponse(
            queue_name=state.queue_name,
            current_track_id=state.current_track_id,
            current_position=state.current_position,
            seek_position=state.seek_position,
            volume=state.volume,
            is_playing=bool(state.is_playing),
            repeat_mode=state.repeat_mode,
            shuffle=bool(state.shuffle),
            current_track=state.current_track,
            updated_at=state.updated_at
        )

    async def update_state(
        self,
        queue_name: str,
        update: PlaybackStateUpdate
    ) -> PlaybackStateResponse:
        """Update playback state."""
        # Get or create state
        query = select(PlaybackState).where(PlaybackState.queue_name == queue_name)
        result = await self.db.execute(query)
        state = result.scalar_one_or_none()
        
        if not state:
            state = PlaybackState(queue_name=queue_name)
            self.db.add(state)
        
        # Update fields
        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "is_playing" or field == "shuffle":
                # Convert boolean to integer for SQLite
                value = 1 if value else 0
            setattr(state, field, value)
        
        state.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(state)
        
        # Broadcast appropriate event
        if "is_playing" in update_data:
            event_type = EventTypes.PLAYBACK_STARTED if update.is_playing else EventTypes.PLAYBACK_PAUSED
            await broadcast_player_event(event_type, {
                "queue": queue_name,
                "track_id": state.current_track_id
            })
        
        if "volume" in update_data:
            await broadcast_player_event(EventTypes.VOLUME_CHANGED, {
                "volume": update.volume
            })
        
        return await self.get_state(queue_name)

    async def play_track(self, track_id: int, queue_name: str = "default"):
        """Play a specific track."""
        # Find track in queue
        query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name,
            QueueEntry.track_id == track_id
        )
        result = await self.db.execute(query)
        entry = result.scalar_one_or_none()
        
        if entry:
            position = entry.position
        else:
            # Add track to queue if not present
            position = await self._add_track_to_queue(track_id, queue_name)
        
        # Update playback state
        await self.update_state(queue_name, PlaybackStateUpdate(
            current_track_id=track_id,
            current_position=position,
            seek_position=0,
            is_playing=True
        ))
        
        # Update track statistics
        await self._update_track_stats(track_id, play=True)
        
        # Broadcast event
        await broadcast_player_event(EventTypes.TRACK_CHANGED, {
            "queue": queue_name,
            "track_id": track_id,
            "position": position
        })

    async def resume(self, queue_name: str = "default"):
        """Resume playback."""
        state = await self.get_state(queue_name)
        
        if not state or not state.current_track_id:
            # Try to play first track in queue
            query = select(QueueEntry).where(
                QueueEntry.queue_name == queue_name
            ).order_by(QueueEntry.position).limit(1)
            result = await self.db.execute(query)
            first_entry = result.scalar_one_or_none()
            
            if first_entry:
                await self.play_track(first_entry.track_id, queue_name)
            return
        
        await self.update_state(queue_name, PlaybackStateUpdate(is_playing=True))

    async def pause(self, queue_name: str = "default"):
        """Pause playback."""
        await self.update_state(queue_name, PlaybackStateUpdate(is_playing=False))

    async def stop(self, queue_name: str = "default"):
        """Stop playback."""
        await self.update_state(queue_name, PlaybackStateUpdate(
            is_playing=False,
            seek_position=0
        ))
        
        await broadcast_player_event(EventTypes.PLAYBACK_STOPPED, {
            "queue": queue_name
        })

    async def next_track(self, queue_name: str = "default") -> Track | None:
        """Skip to next track."""
        state = await self.get_state(queue_name)
        
        if not state:
            return None
        
        # Get next entry in queue
        query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name,
            QueueEntry.position > state.current_position
        ).options(
            selectinload(QueueEntry.track)
        ).order_by(QueueEntry.position).limit(1)
        
        result = await self.db.execute(query)
        next_entry = result.scalar_one_or_none()
        
        if not next_entry:
            # Check repeat mode
            if state.repeat_mode == "all":
                # Go to first track
                query = select(QueueEntry).where(
                    QueueEntry.queue_name == queue_name
                ).options(
                    selectinload(QueueEntry.track)
                ).order_by(QueueEntry.position).limit(1)
                
                result = await self.db.execute(query)
                next_entry = result.scalar_one_or_none()
            else:
                return None
        
        if next_entry:
            await self.play_track(next_entry.track_id, queue_name)
            return next_entry.track
        
        return None

    async def previous_track(self, queue_name: str = "default") -> Track | None:
        """Go to previous track."""
        state = await self.get_state(queue_name)
        
        if not state:
            return None
        
        # Get previous entry in queue
        query = select(QueueEntry).where(
            QueueEntry.queue_name == queue_name,
            QueueEntry.position < state.current_position
        ).options(
            selectinload(QueueEntry.track)
        ).order_by(QueueEntry.position.desc()).limit(1)
        
        result = await self.db.execute(query)
        prev_entry = result.scalar_one_or_none()
        
        if prev_entry:
            await self.play_track(prev_entry.track_id, queue_name)
            return prev_entry.track
        
        return None

    async def seek(self, position: int, queue_name: str = "default"):
        """Seek to position in current track."""
        await self.update_state(queue_name, PlaybackStateUpdate(seek_position=position))
        
        await broadcast_player_event(EventTypes.SEEK_UPDATED, {
            "queue": queue_name,
            "position": position
        })

    async def set_volume(self, volume: int, queue_name: str = "default"):
        """Set playback volume."""
        await self.update_state(queue_name, PlaybackStateUpdate(volume=volume))

    async def set_repeat_mode(self, mode: str, queue_name: str = "default"):
        """Set repeat mode."""
        await self.update_state(queue_name, PlaybackStateUpdate(repeat_mode=mode))

    async def set_shuffle(self, enabled: bool, queue_name: str = "default"):
        """Enable or disable shuffle."""
        await self.update_state(queue_name, PlaybackStateUpdate(shuffle=enabled))

    async def _add_track_to_queue(self, track_id: int, queue_name: str) -> int:
        """Add a track to the queue and return its position."""
        # Get current queue size
        query = select(QueueEntry).where(QueueEntry.queue_name == queue_name)
        result = await self.db.execute(query)
        entries = result.scalars().all()
        position = len(entries)
        
        # Add new entry
        entry = QueueEntry(
            track_id=track_id,
            position=position,
            queue_name=queue_name
        )
        self.db.add(entry)
        await self.db.commit()
        
        return position

    async def _update_track_stats(self, track_id: int, play: bool = False, skip: bool = False):
        """Update track statistics."""
        query = select(Track).where(Track.id == track_id)
        result = await self.db.execute(query)
        track = result.scalar_one_or_none()
        
        if track:
            if play:
                track.play_count += 1
                track.last_played_at = datetime.utcnow()
            if skip:
                track.skip_count += 1
            
            await self.db.commit()