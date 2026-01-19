---
id: task-007
title: Implement Last.fm scrobbling
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-19 06:12'
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
- [ ] #12 Validate scrobbling threshold enforcement (default 90%)
<!-- AC:END -->
