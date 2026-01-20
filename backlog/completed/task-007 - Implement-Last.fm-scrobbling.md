---
id: task-007
title: Implement Last.fm scrobbling
status: Done
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-20 00:37'
labels: []
dependencies: []
priority: high
ordinal: 765.625
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add Last.fm integration for track scrobbling and music discovery, including importing liked tracks from Last.fm API under the settings menu, marking local tracks as favorites based on that import, and updating the DB schema to store Last.fm like status after a one-off import. No auto-sync of liked tracks is planned.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Set up Last.fm API integration
- [x] #2 Implement track scrobbling on play (frontend integration needed)
- [x] #3 Add Last.fm authentication flow
- [x] #4 Handle scrobbling edge cases (threshold validation, rate limiting, offline queuing)
- [x] #5 Test scrobbling with various track types (frontend integration needed)

- [x] #6 Add settings menu option to import liked tracks from Last.fm (frontend needed)
- [x] #7 Implement startup import of liked tracks from Last.fm API (frontend needed)
- [x] #8 Mark local tracks as favorites based on imported Last.fm likes (frontend needed)
- [x] #9 Update DB schema to store Last.fm like status
- [x] #10 Test the import and favorite marking functionality (backend tested)

- [ ] #11 Sync play count
- [x] #12 Validate scrobbling threshold enforcement (default 90%)

- [x] #13 Add diagnostic logging for scrobble queue operations (queue insertion, retry attempts, success/failure, removal after max retries)
- [x] #14 Fix frontend to handle queued scrobble response (currently treats 'queued' as success)
- [ ] #15 Implement automatic scrobble queue retry mechanism (see Implementation Notes for design options)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Scrobble Queue Debugging Analysis (2026-01-19)

### Problem
Queue IS implemented at DB level but lacks visibility:
1. No logging around queue operations
2. Frontend treats `{"status":"queued"}` as success
3. No automatic retry — manual only
4. Silent exception handling in retry logic

### Files Involved
- `backend/services/lastfm.py` — scrobble_track(), _queue_scrobble(), retry_queued_scrobbles()
- `backend/services/database.py` — queue_scrobble(), get/remove/increment_scrobble_retry()
- `backend/routes/lastfm.py` — /lastfm/scrobble, /lastfm/queue/*
- `app/frontend/js/stores/player.js` — _checkScrobble()

### Issue #13: Missing Logging
Add logs to:
- `LastFmAPI._queue_scrobble()`: Log queued id, artist, track
- `LastFmAPI.retry_queued_scrobbles()`: Log retry attempts, success/failure
- `LastFmAPI._api_call()`: Log 403 session invalidation
- `/lastfm/scrobble` route: Log when queued

### Issue #14: Frontend Bug
In `player.js` `_checkScrobble()` `.then()` handler, add explicit check:
```javascript
if (result.status === 'queued') {
  console.warn('[scrobble] Queued for retry:', result.message);
}
```
Currently logs "Successfully scrobbled" for queued responses.

## Issue #15: Automatic Retry Design Options

**Option A: Startup Retry (Simple)**
Call `retry_queued_scrobbles()` in `backend/main.py` lifespan after DB init.

**Option B: Periodic Background Task**
Asyncio task every 5min. More complex, handles network recovery.

**Option C: Frontend on Auth Success**
Call retry in `completeLastfmAuth()`. Already have queue status load there.

**Option D: Hybrid (Recommended)**
Combine A + C: Retry on startup AND after fresh auth.

### Quick Verification
```bash
sqlite3 mt.db "SELECT * FROM scrobble_queue LIMIT 10;"
curl http://127.0.0.1:8765/api/lastfm/queue/status
```

### Note
`_api_call()` uses blocking `requests` in async. Consider `httpx.AsyncClient`.

## Scrobble Threshold Fix (2026-01-19)

### Root Cause
Frontend was using `Math.floor` to convert ms→seconds for scrobble payloads, causing edge cases where the UI showed threshold met but the backend rejected (e.g., 85.839s → 85s failed when threshold required 85.6s).

### Solution
1. **Frontend** (`player.js`): Changed `Math.floor` → `Math.ceil` for duration/played_time
2. **Backend** (`lastfm.py`): Changed `should_scrobble()` to accept floats and use fraction-based comparison
3. **Tests**: Added 6 E2E tests covering threshold edge cases

### Commits
- `fcfb3fb` fix(scrobble): use Math.ceil for played_time/duration
- `85f3a64` fix(lastfm): use fraction-based threshold comparison
- `8bc0073` test(lastfm): add E2E tests for scrobble threshold behavior

## Status: COMPLETE (2026-01-19)

Core Last.fm scrobbling is now working consistently. Remaining nice-to-have items (#11 play count sync, #15 automatic retry) are deferred as future enhancements.
<!-- SECTION:NOTES:END -->
