"""Player control API endpoints."""

from app.core.database import get_async_session
from app.models.queue import PlaybackState
from app.models.track import Track
from app.schemas.queue import PlaybackStateResponse, PlaybackStateUpdate
from app.services.player import PlayerService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/player", tags=["player"])


@router.get("/state", response_model=PlaybackStateResponse)
async def get_playback_state(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Get current playback state."""
    player_service = PlayerService(db)
    state = await player_service.get_state(queue_name)
    
    if not state:
        # Return default state
        return PlaybackStateResponse(
            queue_name=queue_name,
            current_track_id=None,
            current_position=0,
            seek_position=0,
            volume=70,
            is_playing=False,
            repeat_mode="none",
            shuffle=False,
            current_track=None,
            updated_at=None
        )
    
    return state


@router.put("/state", response_model=PlaybackStateResponse)
async def update_playback_state(
    state_update: PlaybackStateUpdate,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Update playback state."""
    player_service = PlayerService(db)
    state = await player_service.update_state(queue_name, state_update)
    
    return state


@router.post("/play")
async def play(
    track_id: int = None,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Start or resume playback."""
    player_service = PlayerService(db)
    
    if track_id:
        # Play specific track
        query = select(Track).where(Track.id == track_id)
        result = await db.execute(query)
        track = result.scalar_one_or_none()
        
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        await player_service.play_track(track_id, queue_name)
    else:
        # Resume playback
        await player_service.resume(queue_name)
    
    return {"message": "Playback started"}


@router.post("/pause")
async def pause(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Pause playback."""
    player_service = PlayerService(db)
    await player_service.pause(queue_name)
    
    return {"message": "Playback paused"}


@router.post("/stop")
async def stop(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Stop playback."""
    player_service = PlayerService(db)
    await player_service.stop(queue_name)
    
    return {"message": "Playback stopped"}


@router.post("/next")
async def next_track(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Skip to next track."""
    player_service = PlayerService(db)
    next_track = await player_service.next_track(queue_name)
    
    if not next_track:
        return {"message": "No next track available"}
    
    return {
        "message": "Skipped to next track",
        "track": next_track.to_dict() if next_track else None
    }


@router.post("/previous")
async def previous_track(
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Go to previous track."""
    player_service = PlayerService(db)
    prev_track = await player_service.previous_track(queue_name)
    
    if not prev_track:
        return {"message": "No previous track available"}
    
    return {
        "message": "Went to previous track",
        "track": prev_track.to_dict() if prev_track else None
    }


@router.post("/seek")
async def seek(
    position: int,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Seek to position in current track (in seconds)."""
    player_service = PlayerService(db)
    await player_service.seek(position, queue_name)
    
    return {"message": f"Seeked to {position} seconds"}


@router.put("/volume")
async def set_volume(
    volume: int,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Set volume (0-100)."""
    if volume < 0 or volume > 100:
        raise HTTPException(status_code=400, detail="Volume must be between 0 and 100")
    
    player_service = PlayerService(db)
    await player_service.set_volume(volume, queue_name)
    
    return {"message": f"Volume set to {volume}"}


@router.put("/repeat")
async def set_repeat_mode(
    mode: str,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Set repeat mode (none, one, all)."""
    if mode not in ["none", "one", "all"]:
        raise HTTPException(status_code=400, detail="Invalid repeat mode")
    
    player_service = PlayerService(db)
    await player_service.set_repeat_mode(mode, queue_name)
    
    return {"message": f"Repeat mode set to {mode}"}


@router.put("/shuffle")
async def toggle_shuffle(
    enabled: bool,
    queue_name: str = "default",
    db: AsyncSession = Depends(get_async_session),
):
    """Enable or disable shuffle mode."""
    player_service = PlayerService(db)
    await player_service.set_shuffle(enabled, queue_name)
    
    return {"message": f"Shuffle {'enabled' if enabled else 'disabled'}"}