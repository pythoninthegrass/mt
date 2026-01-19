"""Last.fm API routes for authentication, scrobbling, and loved tracks."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.services.database import DatabaseService, get_db
from backend.services.lastfm import LastFmAPI
from pydantic import BaseModel
from typing import Optional
from decouple import config

router = APIRouter(prefix="/lastfm", tags=["lastfm"])


def get_lastfm_api(db: DatabaseService = Depends(get_db)) -> LastFmAPI:
    return LastFmAPI(db)


class ScrobbleRequest(BaseModel):
    artist: str
    track: str
    album: Optional[str] = None
    timestamp: int
    duration: int = 0
    played_time: int = 0


class SettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    scrobble_threshold: Optional[int] = None


@router.get("/auth-url")
async def get_auth_url(api: LastFmAPI = Depends(get_lastfm_api)):
    """Get Last.fm authentication URL for user."""
    try:
        return {"auth_url": await api.get_auth_url()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")


@router.post("/auth-callback")
async def auth_callback(token: str, api: LastFmAPI = Depends(get_lastfm_api)):
    """Complete Last.fm authentication with token."""
    try:
        session = await api.get_session(token)
        # Store session key and username
        api.db.set_setting('lastfm_session_key', session['key'])
        api.db.set_setting('lastfm_username', session['name'])
        return {
            "status": "authenticated",
            "username": session['name'],
            "message": f"Successfully connected to Last.fm as {session['name']}",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/settings")
async def get_lastfm_settings(db: DatabaseService = Depends(get_db)):
    """Get Last.fm settings."""
    try:
        return {
            "enabled": db.get_setting('lastfm_scrobbling_enabled') or False,
            "username": db.get_setting('lastfm_username'),
            "authenticated": bool(db.get_setting('lastfm_session_key')),
            "scrobble_threshold": int(db.get_setting('lastfm_scrobble_threshold') or 90),
        }
    except Exception as e:
        return {"error": str(e)}


@router.put("/settings")
async def update_lastfm_settings(settings: SettingsUpdate, api: LastFmAPI = Depends(get_lastfm_api)):
    """Update Last.fm settings."""
    updates = {}
    if settings.enabled is not None:
        updates['lastfm_scrobbling_enabled'] = settings.enabled
    if settings.scrobble_threshold is not None:
        # Clamp to valid range
        threshold = max(25, min(100, settings.scrobble_threshold))
        updates['lastfm_scrobble_threshold'] = threshold

    updated_keys = api.db.update_settings(updates)
    return {"updated": updated_keys}


@router.post("/scrobble")
async def scrobble_track(request: ScrobbleRequest, background_tasks: BackgroundTasks, api: LastFmAPI = Depends(get_lastfm_api)):
    """Scrobble a track."""
    try:
        result = await api.scrobble_track(
            artist=request.artist,
            track=request.track,
            timestamp=request.timestamp,
            album=request.album,
            duration=request.duration,
            played_time=request.played_time,
        )

        # Process any queued scrobbles in background
        background_tasks.add_task(api.retry_queued_scrobbles)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrobbling failed: {str(e)}")


@router.post("/import-loved-tracks")
async def import_loved_tracks(api: LastFmAPI = Depends(get_lastfm_api)):
    """Import user's loved tracks from Last.fm."""
    username = api.db.get_setting('lastfm_username')
    if not username:
        raise HTTPException(status_code=400, detail="No Last.fm user authenticated")

    try:
        # Get all loved tracks (Last.fm API has pagination)
        all_loved_tracks = []
        page = 1
        limit = 1000  # Max per page

        while True:
            loved_tracks = await api.get_loved_tracks(username, limit=limit, page=page)
            if not loved_tracks:
                break
            all_loved_tracks.extend(loved_tracks)
            page += 1

        # Match against local library and mark as loved
        imported_count = 0
        with api.db.get_connection() as conn:
            cursor = conn.cursor()

            for loved_track in all_loved_tracks:
                artist = loved_track.get('artist', {}).get('name', '')
                track = loved_track.get('name', '')

                if artist and track:
                    # Find matching tracks in local library (case-insensitive match)
                    cursor.execute(
                        """
                        UPDATE library
                        SET lastfm_loved = 1
                        WHERE LOWER(TRIM(title)) = LOWER(TRIM(?))
                          AND LOWER(TRIM(artist)) = LOWER(TRIM(?))
                          AND (lastfm_loved = 0 OR lastfm_loved IS NULL)
                    """,
                        (track, artist),
                    )

                    if cursor.rowcount > 0:
                        imported_count += cursor.rowcount

            conn.commit()

        return {
            "status": "imported",
            "total_loved_tracks": len(all_loved_tracks),
            "imported_count": imported_count,
            "message": f"Imported {imported_count} loved tracks from Last.fm",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.delete("/disconnect")
async def disconnect_lastfm(api: LastFmAPI = Depends(get_lastfm_api)):
    """Disconnect from Last.fm."""
    api.db.set_setting('lastfm_session_key', None)
    api.db.set_setting('lastfm_username', None)
    api.db.set_setting('lastfm_scrobbling_enabled', False)
    return {"status": "disconnected", "message": "Disconnected from Last.fm"}


@router.get("/queue/status")
async def get_queue_status(api: LastFmAPI = Depends(get_lastfm_api)):
    """Get status of offline scrobble queue."""
    queued_count = len(api.db.get_queued_scrobbles(limit=1000))  # Get total count
    return {"queued_scrobbles": queued_count}


@router.post("/queue/retry")
async def retry_queued_scrobbles(api: LastFmAPI = Depends(get_lastfm_api)):
    """Manually retry queued scrobbles."""
    try:
        await api.retry_queued_scrobbles()
        remaining = len(api.db.get_queued_scrobbles(limit=1000))
        return {"status": "retry_completed", "remaining_queued": remaining}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")
