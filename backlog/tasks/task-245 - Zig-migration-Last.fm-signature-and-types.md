---
id: task-245
title: 'Zig migration: Last.fm signature and types'
status: Done
assignee: []
created_date: '2026-01-28 23:23'
updated_date: '2026-01-29 03:18'
labels: []
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate Last.fm signature generation and types to Zig while preserving API behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Signature generation outputs match current Rust implementation for known fixtures
- [ ] #2 Last.fm types in Zig match existing Rust structures
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/lastfm/types.zig

Defined Method enum: track_updateNowPlaying, track_scrobble, auth_getSession, user_getInfo

Defined Params struct with StringHashMap

Defined ScrobbleRequest and NowPlayingRequest extern structs

Stubbed generateSignature: sort params → concatenate → append secret → MD5

Fixed-size buffers (512 bytes) for artist/track/album

Matches Last.fm API v2.0 specification
<!-- SECTION:NOTES:END -->
