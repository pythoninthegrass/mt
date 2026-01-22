---
id: task-189
title: Migrate Last.fm integration to Rust (Phase 4)
status: In Progress
assignee: []
created_date: '2026-01-21 17:39'
updated_date: '2026-01-21 18:32'
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
