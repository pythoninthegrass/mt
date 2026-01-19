"""Last.fm API routes for authentication, scrobbling, and loved tracks."""

from backend.services.database import get_db
from backend.services.lastfm import LastFmAPI
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["lastfm"])


# ============================================
# Request/Response Models
# ============================================


class LastfmSettingsUpdate(BaseModel):
    enabled: bool | None = None
    scrobble_threshold: int | None = None


class ScrobbleRequest(BaseModel):
    artist: str
    track: str
    album: str | None = None
    timestamp: int
    duration: int
    played_time: int


# ============================================
# Helper functions
# ============================================


def _get_lastfm_api() -> LastFmAPI:
    """Get LastFmAPI instance with database."""
    db = get_db()
    return LastFmAPI(db)


def _is_setting_truthy(value: str | None) -> bool:
    """Check if a setting value is truthy."""
    if value is None:
        return False
    return value.lower() in ("1", "true", "yes", "on")


# ============================================
# Settings endpoints
# ============================================


@router.get("/lastfm/settings")
async def get_lastfm_settings():
    """Get Last.fm settings."""
    db = get_db()
    api = _get_lastfm_api()

    enabled = _is_setting_truthy(db.get_setting("lastfm_scrobbling_enabled"))
    username = db.get_setting("lastfm_username")
    session_key = db.get_setting("lastfm_session_key")
    threshold_str = db.get_setting("lastfm_scrobble_threshold")
    threshold = int(threshold_str) if threshold_str else 90

    return {
        "enabled": enabled,
        "username": username,
        "authenticated": bool(session_key),
        "configured": api.is_configured(),
        "scrobble_threshold": threshold,
    }


@router.put("/lastfm/settings")
async def update_lastfm_settings(settings: LastfmSettingsUpdate):
    """Update Last.fm settings."""
    db = get_db()
    updated = []

    if settings.enabled is not None:
        db.set_setting("lastfm_scrobbling_enabled", settings.enabled)
        updated.append("enabled")

    if settings.scrobble_threshold is not None:
        # Clamp to valid range (25-100%)
        threshold = max(25, min(100, settings.scrobble_threshold))
        db.set_setting("lastfm_scrobble_threshold", threshold)
        updated.append("scrobble_threshold")

    return {"updated": updated}


# ============================================
# Authentication endpoints
# ============================================


@router.get("/lastfm/auth-url")
async def get_auth_url():
    """Get Last.fm authentication URL and token.

    Returns the auth URL to open in browser and the token needed to complete auth.
    The frontend should store the token and use it to call /lastfm/auth-callback after
    the user completes authorization on Last.fm.
    """
    api = _get_lastfm_api()

    if not api.is_configured():
        raise HTTPException(
            status_code=503, detail="Last.fm API keys not configured. Set LASTFM_API_KEY and LASTFM_API_SECRET."
        )

    try:
        auth_url, token = await api.get_auth_url()
        return {"auth_url": auth_url, "token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}") from e


@router.get("/lastfm/auth-callback")
async def auth_callback(token: str):
    """Complete Last.fm authentication with token."""
    db = get_db()
    api = _get_lastfm_api()

    if not api.is_configured():
        raise HTTPException(status_code=503, detail="Last.fm API not configured")

    try:
        session = await api.get_session(token)
        session_key = session.get("key")
        username = session.get("name")

        if not session_key:
            raise HTTPException(status_code=400, detail="Invalid session received from Last.fm")

        # Store session data
        db.set_setting("lastfm_session_key", session_key)
        db.set_setting("lastfm_username", username)
        db.set_setting("lastfm_scrobbling_enabled", True)

        return {"status": "success", "username": username, "message": f"Successfully connected as {username}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}") from e


@router.delete("/lastfm/disconnect")
async def disconnect():
    """Disconnect from Last.fm."""
    db = get_db()

    db.set_setting("lastfm_session_key", "")
    db.set_setting("lastfm_username", "")
    db.set_setting("lastfm_scrobbling_enabled", False)

    return {"status": "success", "message": "Disconnected from Last.fm"}


# ============================================
# Scrobbling endpoints
# ============================================


class NowPlayingRequest(BaseModel):
    artist: str
    track: str
    album: str | None = None
    duration: int = 0


@router.post("/lastfm/now-playing")
async def update_now_playing(request: NowPlayingRequest):
    """Update 'Now Playing' status on Last.fm when a track starts."""
    db = get_db()
    api = _get_lastfm_api()

    # Check if scrobbling is enabled
    enabled = _is_setting_truthy(db.get_setting("lastfm_scrobbling_enabled"))
    if not enabled:
        return {"status": "disabled", "message": "Scrobbling is disabled"}

    # Check if authenticated
    session_key = db.get_setting("lastfm_session_key")
    if not session_key:
        return {"status": "not_authenticated", "message": "Not authenticated with Last.fm"}

    result = await api.update_now_playing(
        artist=request.artist,
        track=request.track,
        album=request.album,
        duration=request.duration,
    )
    return result


@router.post("/lastfm/scrobble")
async def scrobble_track(request: ScrobbleRequest):
    """Scrobble a track to Last.fm."""
    db = get_db()
    api = _get_lastfm_api()

    # Check if scrobbling is enabled
    enabled = _is_setting_truthy(db.get_setting("lastfm_scrobbling_enabled"))
    if not enabled:
        return {"status": "disabled", "message": "Scrobbling is disabled"}

    # Check if authenticated
    session_key = db.get_setting("lastfm_session_key")
    if not session_key:
        return {"status": "not_authenticated", "message": "Not authenticated with Last.fm"}

    try:
        result = await api.scrobble_track(
            artist=request.artist,
            track=request.track,
            timestamp=request.timestamp,
            album=request.album,
            duration=request.duration,
            played_time=request.played_time,
        )
        return result
    except Exception as e:
        # The service will queue the scrobble for retry
        return {"status": "queued", "message": f"Scrobble queued for retry: {str(e)}"}


# ============================================
# Queue endpoints
# ============================================


@router.get("/lastfm/queue/status")
async def get_queue_status():
    """Get scrobble queue status."""
    db = get_db()
    queued = db.get_queued_scrobbles(limit=1000)  # Get count of all queued
    return {"queued_scrobbles": len(queued)}


@router.post("/lastfm/queue/retry")
async def retry_queued_scrobbles():
    """Manually retry queued scrobbles."""
    db = get_db()
    api = _get_lastfm_api()

    # Check if authenticated
    session_key = db.get_setting("lastfm_session_key")
    if not session_key:
        raise HTTPException(status_code=401, detail="Not authenticated with Last.fm")

    try:
        await api.retry_queued_scrobbles()
        # Get remaining count
        remaining = db.get_queued_scrobbles(limit=1000)
        return {"status": "success", "remaining_queued": len(remaining)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry scrobbles: {str(e)}") from e


# ============================================
# Loved tracks import
# ============================================


@router.post("/lastfm/import-loved-tracks")
async def import_loved_tracks():
    """Import user's loved tracks from Last.fm and mark matching library tracks as favorites."""
    db = get_db()
    api = _get_lastfm_api()

    # Check authentication
    username = db.get_setting("lastfm_username")
    session_key = db.get_setting("lastfm_session_key")

    if not username or not session_key:
        raise HTTPException(status_code=401, detail="Not authenticated with Last.fm")

    try:
        # Fetch all loved tracks (paginated)
        all_loved_tracks = []
        page = 1
        max_pages = 100  # Safety limit

        while page <= max_pages:
            tracks = await api.get_loved_tracks(user=username, limit=200, page=page)
            if not tracks:
                break
            all_loved_tracks.extend(tracks)
            # Check if we got a full page (more to fetch)
            if len(tracks) < 200:
                break
            page += 1

        # Match loved tracks to library and mark as favorites
        imported_count = 0

        for loved_track in all_loved_tracks:
            artist = loved_track.get("artist", {})
            artist_name = artist.get("name", "") if isinstance(artist, dict) else str(artist)
            track_name = loved_track.get("name", "")

            if not artist_name or not track_name:
                continue

            # Find matching track in library (case-insensitive match)
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id FROM library
                    WHERE LOWER(artist) = LOWER(?) AND LOWER(title) = LOWER(?)
                    """,
                    (artist_name, track_name),
                )
                rows = cursor.fetchall()

                for row in rows:
                    track_id = row["id"]
                    # Add to favorites if not already
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO favorites (track_id) VALUES (?)",
                            (track_id,),
                        )
                        # Mark as Last.fm loved
                        cursor.execute(
                            "UPDATE library SET lastfm_loved = 1 WHERE id = ?",
                            (track_id,),
                        )
                        if cursor.rowcount > 0:
                            imported_count += 1
                    except Exception:
                        pass  # Skip duplicates

                conn.commit()

        return {
            "status": "success",
            "total_loved_tracks": len(all_loved_tracks),
            "imported_count": imported_count,
            "message": f"Imported {imported_count} tracks from {len(all_loved_tracks)} loved tracks",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import loved tracks: {str(e)}") from e
