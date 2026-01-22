---
id: task-189
title: Migrate Last.fm integration to Rust (Phase 4)
status: In Progress
assignee:
  - Claude
created_date: '2026-01-21 17:39'
updated_date: '2026-01-22 22:42'
labels:
  - rust
  - migration
  - lastfm
  - phase-4
  - api
  - oauth
dependencies:
  - task-173
  - task-180
priority: low
ordinal: 4656.25
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate Last.fm API integration from Python to Rust, implementing OAuth 1.0a authentication, scrobbling, and loved tracks import.

**Endpoints to Migrate** (11 total):

**Authentication**:
- GET `/lastfm/auth-url` - Get Last.fm auth URL and token
- GET `/lastfm/auth-callback?token=` - Complete authentication
- DELETE `/lastfm/disconnect` - Disconnect from Last.fm

**Settings**:
- GET `/lastfm/settings` - Get Last.fm settings
- PUT `/lastfm/settings` - Update settings (enabled, scrobble_threshold)

**Scrobbling**:
- POST `/lastfm/now-playing` - Update "Now Playing" status
- POST `/lastfm/scrobble` - Scrobble a track

**Queue**:
- GET `/lastfm/queue/status` - Get queued scrobble count
- POST `/lastfm/queue/retry` - Manually retry queued scrobbles

**Loved Tracks**:
- POST `/lastfm/import-loved-tracks` - Import loved tracks from Last.fm

**Features**:
- OAuth 1.0a authentication flow
- API signature generation (MD5 hash)
- Now playing updates
- Scrobble submission with threshold (25-100%)
- Offline scrobble queue with retry logic
- Loved tracks import (paginated, case-insensitive matching)
- Rate limiting handling
- API error handling

**Database Operations**:
- scrobble_queue table (artist, track, album, timestamp, retry_count)
- Settings: lastfm_session_key, lastfm_username, lastfm_scrobbling_enabled, lastfm_scrobble_threshold
- library table: lastfm_loved column

**Complexity Factors**:
- OAuth 1.0a signature generation (requires careful implementation)
- API rate limiting (Last.fm has strict limits)
- Retry logic with exponential backoff
- Paginated API responses (1000+ loved tracks possible)
- Error handling for network failures

**Implementation**:
- Create Last.fm API client module
- Use `reqwest` for async HTTP requests
- Use `oauth1` crate for OAuth 1.0a
- Use `md5` for signature generation
- Implement exponential backoff for retries
- Store API keys in environment variables
- Emit Tauri events for scrobble status
- Background task for retry queue processing

**Rust Crates**:
- `reqwest` - HTTP client
- `oauth1` - OAuth 1.0a implementation
- `md5` or `sha256` - API signature
- `serde_json` - JSON parsing
- `tokio` - Async runtime

**Estimated Effort**: 2-3 weeks
**Files**: backend/routes/lastfm.py (360 lines), backend/services/lastfm.py

**Note**: This is optional and can be deferred. Core functionality should be prioritized first.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 11 endpoints migrated to Tauri commands
- [ ] #2 OAuth 1.0a flow working end-to-end
- [ ] #3 Scrobbling functional with threshold
- [ ] #4 Now playing updates working
- [ ] #5 Offline queue with retry logic functional
- [ ] #6 Loved tracks import working (paginated)
- [ ] #7 Rate limiting handled gracefully
- [ ] #8 API error handling comprehensive
- [ ] #9 Frontend updated and E2E tests passing
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan: Migrate Last.fm Integration to Rust

### Phase 1: Core Infrastructure ✓
1. Add dependencies to Cargo.toml (md5, hex, reqwest)
2. Create module structure: src-tauri/src/lastfm/ (mod.rs, client.rs, rate_limiter.rs, signature.rs, types.rs, config.rs)
3. Implement signature generation with test vectors from Python
4. Implement rate limiter with tokio::sync::Mutex

### Phase 2: Settings Commands
5. Implement lastfm_get_settings command
6. Implement lastfm_update_settings command (clamp 25-100%)
7. Add event types to events.rs (LastfmAuthEvent, ScrobbleStatusEvent)

### Phase 3: Authentication Commands
8. Implement lastfm_get_auth_url (auth.getToken)
9. Implement lastfm_auth_callback (auth.getSession)
10. Implement lastfm_disconnect

### Phase 4: Scrobbling Commands
11. Implement should_scrobble threshold logic (fraction + min_time + max_cap)
12. Implement lastfm_now_playing (non-critical, silent errors)
13. Implement lastfm_scrobble (queue on failure)

### Phase 5: Queue Commands + Background Task
14. Implement lastfm_queue_status
15. Implement lastfm_queue_retry (batch of 10, max 3 attempts)
16. Implement background retry task using tauri::async_runtime::spawn (every 5 minutes when authenticated)
17. Emit lastfm:queue-updated events

### Phase 6: Loved Tracks Import
18. Implement lastfm_import_loved_tracks (paginated, case-insensitive matching)

### Phase 7: Frontend Integration
19. Update app/frontend/js/api.js to use invoke() instead of HTTP

### Phase 8: Testing
20. Update E2E tests for Tauri invoke mocking
21. Add Rust unit tests (signature, rate limiter, threshold logic)

## API Key Security (Approved)
- Dev builds: .env file with LASTFM_API_KEY, LASTFM_API_SECRET
- Release builds: Salted hash (HMAC-SHA256) stored in settings

## Background Retry Task (Approved)
- Automatic: tauri::async_runtime::spawn task running every 5 minutes when authenticated
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Phase 1 Complete ✓

Successfully implemented core Last.fm infrastructure:

1. ✓ Added dependencies to Cargo.toml (md5 = "0.7", hex = "0.4")
2. ✓ Created module structure:
   - lastfm/mod.rs - Module exports
   - lastfm/types.rs - All request/response types with serde
   - lastfm/signature.rs - MD5 signature generation
   - lastfm/rate_limiter.rs - tokio::sync::Mutex rate limiting (5/sec, 333/day)
   - lastfm/config.rs - API key configuration (dev: .env, release: TODO salted hash)
   - lastfm/client.rs - reqwest-based HTTP client with error handling

3. ✓ Signature generation verified against Python:
   - Created test_signature_vectors.py to generate test vectors
   - All 4 test vectors pass (basic auth, format exclusion, scrobble, sorted order)
   - Signatures match Python's hashlib.md5 byte-for-byte

4. ✓ All 13 unit tests passing:
   - Config tests (4 tests)
   - Signature tests (4 tests)
   - Rate limiter tests (3 tests)
   - Client tests (2 tests)

Next: Phase 2 - Settings Commands

## Phase 2 Complete ✓

Successfully implemented Last.fm settings commands:

1. ✓ Created commands/lastfm.rs with Tauri commands
2. ✓ Implemented lastfm_get_settings:
   - Returns enabled, username, authenticated, configured, scrobble_threshold
   - Uses database settings (not Tauri Store)
   - Helper functions for parsing truthy values and threshold
3. ✓ Implemented lastfm_update_settings:
   - Updates enabled flag and scrobble_threshold
   - Clamps threshold to 25-100% range
   - Returns list of updated fields
4. ✓ Added Last.fm event types to events.rs:
   - LastfmAuthEvent (authenticated/disconnected/pending)
   - ScrobbleStatusEvent (success/queued/failed)
   - LastfmQueueUpdatedEvent (queue count changes)
5. ✓ Registered commands in lib.rs invoke_handler
6. ✓ All 15 tests passing (includes 2 new command helper tests)

Next: Phase 3 - Authentication Commands
<!-- SECTION:NOTES:END -->
