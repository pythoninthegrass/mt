"""Last.fm API service for scrobbling and loved tracks integration."""

import asyncio
import hashlib
import requests
import time
from typing import Optional, Dict, List, Tuple
from backend.services.database import DatabaseService
from decouple import config


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

    def _sign_params(self, params: dict) -> str:
        """Generate API signature for authenticated calls."""
        if not self.api_secret:
            raise ValueError("Last.fm API secret not configured")
        sorted_items = sorted(params.items())
        signature_string = "".join(f"{k}{v}" for k, v in sorted_items) + self.api_secret
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest()

    async def _api_call(self, method: str, params: dict, authenticated: bool = False) -> dict:
        """Make authenticated API call with rate limiting."""
        if not self.api_key:
            raise ValueError("Last.fm API key not configured")

        await self.rate_limiter.wait_if_needed()

        params.update({'method': method, 'api_key': self.api_key, 'format': 'json'})

        if authenticated:
            session_key = self.db.get_setting('lastfm_session_key')
            if not session_key:
                raise ValueError("No Last.fm session key available")
            params['sk'] = session_key
            params['api_sig'] = self._sign_params(params)

        try:
            response = requests.get(self.base_url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response and e.response.status_code == 403:
                # Clear invalid session key
                self.db.set_setting('lastfm_session_key', None)
                self.db.set_setting('lastfm_username', None)
            raise e

    def should_scrobble(self, track_duration: int, played_time: int) -> bool:
        """Check if track should be scrobbled based on user settings."""
        enabled = self.db.get_setting('lastfm_scrobbling_enabled')
        if not enabled or enabled == "0" or enabled == "false":
            return False

        # Get user-configurable threshold (default 90%, range 25-100%)
        threshold_str = self.db.get_setting('lastfm_scrobble_threshold')
        threshold_percent = int(threshold_str) if threshold_str else 90
        threshold_percent = max(25, min(100, threshold_percent))  # Clamp to valid range

        # Calculate threshold time: min(duration * percentage, 4 minutes)
        threshold_time = min(track_duration * (threshold_percent / 100), 240)

        # Last.fm minimum: 30 seconds
        return played_time >= max(threshold_time, 30)

    async def get_auth_url(self) -> str:
        """Get Last.fm authentication URL for user."""
        token_response = await self._api_call('auth.getToken', {})
        token = token_response['token']
        return f"https://www.last.fm/api/auth/?api_key={self.api_key}&token={token}"

    async def get_session(self, token: str) -> dict:
        """Exchange authentication token for session key."""
        params = {'token': token}
        params['api_sig'] = self._sign_params(params)
        response = await self._api_call('auth.getSession', params, authenticated=False)
        return response['session']

    async def get_loved_tracks(self, user: str, limit: int = 50, page: int = 1) -> List[dict]:
        """Get user's loved tracks."""
        response = await self._api_call('user.getLovedTracks', {'user': user, 'limit': limit, 'page': page})
        return response.get('lovedtracks', {}).get('track', [])

    async def scrobble_track(
        self, artist: str, track: str, timestamp: int, album: Optional[str] = None, duration: int = 0, played_time: int = 0
    ) -> dict:
        """Scrobble a track if it meets threshold criteria."""
        if not self.should_scrobble(duration, played_time):
            return {"status": "threshold_not_met"}

        params = {'artist': artist, 'track': track, 'timestamp': timestamp}
        if album:
            params['album'] = album

        try:
            result = await self._api_call('track.scrobble', params, authenticated=True)
            return result
        except Exception as e:
            # Queue for offline retry
            await self._queue_scrobble(params)
            raise e

    async def _queue_scrobble(self, params: dict):
        """Queue failed scrobble for later retry."""
        self.db.queue_scrobble(
            artist=params.get('artist', ''),
            track=params.get('track', ''),
            album=params.get('album'),
            timestamp=params.get('timestamp', 0),
        )

    async def retry_queued_scrobbles(self):
        """Process queued scrobbles when back online."""
        queued = self.db.get_queued_scrobbles(limit=10)  # Process in small batches
        for item in queued:
            try:
                result = await self._api_call(
                    'track.scrobble',
                    {'artist': item['artist'], 'track': item['track'], 'album': item['album'], 'timestamp': item['timestamp']},
                    authenticated=True,
                )

                if result.get('scrobbles', {}).get('@attr', {}).get('accepted', 0) > 0:
                    self.db.remove_queued_scrobble(item['id'])
                else:
                    # Increment retry count, remove after 3 failures
                    retry_count = self.db.increment_scrobble_retry(item['id'])
                    if retry_count >= 3:
                        self.db.remove_queued_scrobble(item['id'])

            except Exception:
                # Increment retry count on failure
                retry_count = self.db.increment_scrobble_retry(item['id'])
                if retry_count >= 3:
                    self.db.remove_queued_scrobble(item['id'])
