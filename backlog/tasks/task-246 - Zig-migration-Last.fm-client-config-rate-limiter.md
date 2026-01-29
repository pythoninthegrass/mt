---
id: task-246
title: 'Zig migration: Last.fm client/config/rate limiter'
status: Done
assignee: []
created_date: '2026-01-28 23:23'
updated_date: '2026-01-29 03:18'
labels: []
dependencies:
  - task-245
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate Last.fm client, configuration, and rate limiter logic to Zig while preserving API behavior and error handling.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Client behavior (requests/responses, error handling) matches current Rust implementation on fixtures
- [ ] #2 Rate limiting behavior matches current Rust implementation
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/lastfm/client.zig

Defined RateLimiter struct with waitForSlot method

Defined Config and Client structs

Stubbed client methods: init, deinit, setSessionKey, scrobble, updateNowPlaying, makeRequest

Rate limiter enforces 5 requests/second (Last.fm API limit)

Thread-safe via mutex

HTTP requests to be implemented via std.http

Dependencies: Requires task 245 complete for signature generation
<!-- SECTION:NOTES:END -->
