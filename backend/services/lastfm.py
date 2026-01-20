"""Last.fm API service for scrobbling and loved tracks integration."""

import asyncio
import hashlib
import logging
import requests
import time
from backend.services.database import DatabaseService
from decouple import config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Last.fm API calls (5 requests/second, 333/day)."""

    def __init__(self):
        self.requests = []
        self.daily_limit = 333
        self.per_second_limit = 5
        self.lock = asyncio.Lock()

    async def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        async with self.lock:
            now = time.time()

            # Clean old requests (keep last 24 hours)
            self.requests = [req for req in self.requests if now - req < 86400]

            # Check daily limit
            if len(self.requests) >= self.daily_limit:
                # Wait until oldest request expires (24 hours)
                wait_time = 86400 - (now - self.requests[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return

            # Check per-second limit
            recent_requests = [req for req in self.requests if now - req < 1]
            if len(recent_requests) >= self.per_second_limit:
                wait_time = 1 - (now - recent_requests[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self.requests.append(now)


class LastFmAPI:
    """Last.fm API client for authentication, scrobbling, and loved tracks."""

    def __init__(self, db: DatabaseService):
        try:
            self.api_key = config('LASTFM_API_KEY')
            self.api_secret = config('LASTFM_API_SECRET')
        except Exception:
            # API keys not configured
            self.api_key = None
            self.api_secret = None

        self.base_url = "https://ws.audioscrobbler.com/2.0/"
        self.db = db
        self.rate_limiter = RateLimiter()

    def is_configured(self) -> bool:
        """Check if Last.fm API is properly configured."""
        return bool(self.api_key and self.api_secret)

    def _sign_params(self, params: dict) -> str:
        """Generate API signature for authenticated calls."""
        if not self.api_secret:
            raise ValueError("Last.fm API secret not configured")
        sorted_items = sorted(params.items())
        signature_string = "".join(f"{k}{v}" for k, v in sorted_items) + self.api_secret
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest()

    async def _api_call(self, method: str, params: dict, authenticated: bool = False, use_post: bool = False) -> dict:
        """Make authenticated API call with rate limiting.

        Args:
            method: Last.fm API method name
            params: Parameters to send
            authenticated: Whether to include session key and signature
            use_post: Whether to use POST instead of GET (required for scrobbling)
        """
        if not self.api_key:
            raise ValueError("Last.fm API key not configured")

        await self.rate_limiter.wait_if_needed()

        params.update({'method': method, 'api_key': self.api_key, 'format': 'json'})

        if authenticated:
            session_key = self.db.get_setting('lastfm_session_key')
            if not session_key:
                raise ValueError("No Last.fm session key available")
            params['sk'] = session_key
            # Signature should not include 'format' parameter
            sign_params = {k: v for k, v in params.items() if k != 'format'}
            params['api_sig'] = self._sign_params(sign_params)

        try:
            if use_post:
                response = requests.post(self.base_url, data=params, timeout=30.0)
            else:
                response = requests.get(self.base_url, params=params, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            logger.debug("[lastfm] API call %s succeeded: %s", method, result)
            return result
        except requests.HTTPError as e:
            logger.error(
                "[lastfm] API call %s failed: status=%s body=%s",
                method,
                e.response.status_code if e.response else 'N/A',
                e.response.text if e.response else 'N/A',
            )
            if e.response and e.response.status_code == 403:
                # Clear invalid session key
                logger.warning("[lastfm] Session invalidated (403), clearing session key")
                self.db.set_setting('lastfm_session_key', None)
                self.db.set_setting('lastfm_username', None)
            raise e

    def should_scrobble(self, track_duration: float, played_time: float) -> bool:
        """Check if track should be scrobbled based on user settings.

        Args:
            track_duration: Track duration in seconds (accepts int or float)
            played_time: Time played in seconds (accepts int or float)
        """
        enabled = self.db.get_setting('lastfm_scrobbling_enabled')
        if not enabled or enabled == "0" or enabled == "false":
            logger.debug("[lastfm] should_scrobble: disabled (enabled=%s)", enabled)
            return False

        # Get user-configurable threshold (default 90%, range 25-100%)
        threshold_str = self.db.get_setting('lastfm_scrobble_threshold')
        threshold_percent = int(threshold_str) if threshold_str else 90
        threshold_percent = max(25, min(100, threshold_percent))

        # Use fraction-based comparison for robustness against rounding differences
        # Last.fm rules: scrobble if played >= min(threshold%, 4 minutes) AND >= 30 seconds
        threshold_fraction = threshold_percent / 100.0
        fraction_played = played_time / track_duration if track_duration > 0 else 0.0

        # Check fraction threshold and absolute time requirements
        meets_fraction = fraction_played >= threshold_fraction
        meets_min_time = played_time >= 30
        meets_max_cap = played_time >= min(track_duration * threshold_fraction, 240)

        meets_threshold = meets_fraction and meets_min_time and meets_max_cap
        logger.info(
            "[lastfm] should_scrobble: duration=%.1fs played=%.1fs threshold_pct=%d%% "
            "fraction=%.3f meets_fraction=%s meets_min_time=%s meets_max_cap=%s result=%s",
            track_duration,
            played_time,
            threshold_percent,
            fraction_played,
            meets_fraction,
            meets_min_time,
            meets_max_cap,
            meets_threshold,
        )
        return meets_threshold

    async def get_auth_url(self) -> tuple[str, str]:
        """Get Last.fm authentication URL for user.

        Returns:
            Tuple of (auth_url, token) - the token is needed to complete authentication.
        """
        token_response = await self._api_call('auth.getToken', {})
        token = token_response['token']
        auth_url = f"https://www.last.fm/api/auth/?api_key={self.api_key}&token={token}"
        return auth_url, token

    async def get_session(self, token: str) -> dict:
        """Exchange authentication token for session key."""
        # Build params and signature before adding format (which shouldn't be signed)
        params = {
            'api_key': self.api_key,
            'method': 'auth.getSession',
            'token': token,
        }
        params['api_sig'] = self._sign_params(params)
        params['format'] = 'json'

        await self.rate_limiter.wait_if_needed()

        try:
            response = requests.get(self.base_url, params=params, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            if 'error' in result:
                raise ValueError(f"Last.fm API error: {result.get('message', 'Unknown error')}")
            return result['session']
        except requests.HTTPError as e:
            raise ValueError(f"HTTP error during session exchange: {e}") from e

    async def get_loved_tracks(self, user: str, limit: int = 50, page: int = 1) -> list[dict]:
        """Get user's loved tracks."""
        response = await self._api_call('user.getLovedTracks', {'user': user, 'limit': limit, 'page': page})
        return response.get('lovedtracks', {}).get('track', [])

    async def update_now_playing(self, artist: str, track: str, album: str | None = None, duration: int = 0) -> dict:
        """Update 'Now Playing' status on Last.fm.

        This should be called when a track starts playing.
        """
        enabled = self.db.get_setting('lastfm_scrobbling_enabled')
        if not enabled or enabled == "0" or enabled == "false":
            return {"status": "disabled"}

        params = {'artist': artist, 'track': track}
        if album:
            params['album'] = album
        if duration > 0:
            params['duration'] = str(duration)

        try:
            result = await self._api_call('track.updateNowPlaying', params, authenticated=True, use_post=True)
            return result
        except Exception as e:
            # Now Playing updates are not critical, just log and continue
            return {"status": "error", "message": str(e)}

    async def scrobble_track(
        self, artist: str, track: str, timestamp: int, album: str | None = None, duration: int = 0, played_time: int = 0
    ) -> dict:
        """Scrobble a track if it meets threshold criteria."""
        logger.info(
            "[lastfm] scrobble_track called: artist=%s track=%s duration=%ds played_time=%ds",
            artist,
            track,
            duration,
            played_time,
        )
        if not self.should_scrobble(duration, played_time):
            logger.info("[lastfm] scrobble_track: threshold not met, skipping")
            return {"status": "threshold_not_met"}

        params = {'artist': artist, 'track': track, 'timestamp': timestamp}
        if album:
            params['album'] = album

        try:
            result = await self._api_call('track.scrobble', params, authenticated=True, use_post=True)
            accepted = result.get('scrobbles', {}).get('@attr', {}).get('accepted', 0)
            logger.info("[lastfm] scrobble_track: API returned accepted=%s for track=%s", accepted, track)
            return result
        except Exception as e:
            # Queue for offline retry
            logger.warning("[lastfm] scrobble_track: API call failed (%s), queueing for retry", e)
            await self._queue_scrobble(params)
            raise e

    async def _queue_scrobble(self, params: dict):
        """Queue failed scrobble for later retry."""
        scrobble_id = self.db.queue_scrobble(
            artist=params.get('artist', ''),
            track=params.get('track', ''),
            album=params.get('album'),
            timestamp=params.get('timestamp', 0),
        )
        logger.info(
            "[lastfm] _queue_scrobble: queued id=%s artist=%s track=%s", scrobble_id, params.get('artist'), params.get('track')
        )

    async def retry_queued_scrobbles(self):
        """Process queued scrobbles when back online."""
        queued = self.db.get_queued_scrobbles(limit=10)  # Process in small batches
        logger.info("[lastfm] retry_queued_scrobbles: %d items to retry", len(queued))
        for item in queued:
            try:
                logger.debug(
                    "[lastfm] retry_queued_scrobbles: retrying id=%s artist=%s track=%s retry_count=%s",
                    item['id'],
                    item['artist'],
                    item['track'],
                    item.get('retry_count', 0),
                )
                result = await self._api_call(
                    'track.scrobble',
                    {'artist': item['artist'], 'track': item['track'], 'album': item['album'], 'timestamp': item['timestamp']},
                    authenticated=True,
                    use_post=True,
                )

                accepted = result.get('scrobbles', {}).get('@attr', {}).get('accepted', 0)
                if accepted > 0:
                    self.db.remove_queued_scrobble(item['id'])
                    logger.info("[lastfm] retry_queued_scrobbles: id=%s accepted, removed from queue", item['id'])
                else:
                    # Increment retry count, remove after 3 failures
                    retry_count = self.db.increment_scrobble_retry(item['id'])
                    logger.warning("[lastfm] retry_queued_scrobbles: id=%s accepted=0, retry_count=%d", item['id'], retry_count)
                    if retry_count >= 3:
                        self.db.remove_queued_scrobble(item['id'])
                        logger.warning("[lastfm] retry_queued_scrobbles: id=%s removed after max retries", item['id'])

            except Exception as e:
                # Increment retry count on failure
                retry_count = self.db.increment_scrobble_retry(item['id'])
                logger.error("[lastfm] retry_queued_scrobbles: id=%s failed (%s), retry_count=%d", item['id'], e, retry_count)
                if retry_count >= 3:
                    self.db.remove_queued_scrobble(item['id'])
                    logger.warning("[lastfm] retry_queued_scrobbles: id=%s removed after max retries", item['id'])
