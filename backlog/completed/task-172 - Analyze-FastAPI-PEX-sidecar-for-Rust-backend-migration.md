---
id: task-172
title: Analyze FastAPI PEX sidecar for Rust backend migration
status: Done
assignee: []
created_date: '2026-01-19 06:16'
updated_date: '2026-01-24 22:28'
labels:
  - analysis
  - backend
  - rust
  - migration
  - fastapi
  - sidecar
dependencies: []
priority: medium
ordinal: 3382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze the current FastAPI PEX sidecar implementation to identify what functionality can be migrated to the refactored Rust backend. Examine the Python backend code and rank migration opportunities from highest to lowest impact, factoring in weighted complexity.

Focus areas:
- Database operations and schema
- API endpoints and business logic  
- WebSocket real-time events
- Library scanning and metadata extraction
- External service integrations (Last.fm)
- Queue management and playback logic

Rank findings by impact (high/medium/low) and complexity (high/medium/low), providing specific recommendations for phased migration. Consider dependencies, testing implications, and risk assessment.

Deliverable: Detailed report with prioritized migration phases and implementation roadmap.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Complete analysis of FastAPI sidecar functionality
- [x] #2 Rank migration opportunities by impact vs complexity
- [x] #3 Provide phased migration recommendations
- [x] #4 Assess dependencies and testing implications
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Analysis Complete

Detailed migration analysis report created at: `docs/fastapi-to-rust-migration-analysis.md`

### Key Findings

**Backend Structure Analyzed** (1,347 lines total):
- Database layer: 1,502 lines (SQLite with 9 tables)
- API routes: 1,347 lines across 9 route files
- Services: Scanner, Last.fm, artwork extraction

**Impact vs Complexity Rankings**:

| Component | Impact | Complexity | Phase |
|-----------|--------|------------|-------|
| Database Operations | HIGH | MEDIUM-HIGH | 1 |
| Library Management | HIGH | MEDIUM | 2 |
| Metadata Extraction | HIGH | MEDIUM-HIGH | 2 |
| Queue Management | HIGH | LOW-MEDIUM | 2 |
| WebSocket Events | MEDIUM | LOW-MEDIUM | 2 |
| Playlists | MEDIUM-HIGH | MEDIUM | 3 |
| Favorites | MEDIUM | LOW | 3 |
| Settings | LOW-MEDIUM | LOW | 3 |
| Watched Folders | MEDIUM | MEDIUM | 3 |
| Last.fm Integration | MEDIUM | HIGH | 4 |

**Phased Migration Roadmap** (10-14 weeks total):

1. Phase 1 (2-3 weeks): Foundation - Rust database layer
2. Phase 2 (3-4 weeks): Core Features - Library, queue, metadata
3. Phase 3 (2-3 weeks): Enhanced Features - Playlists, favorites, settings
4. Phase 4 (2-3 weeks): Optional Features - Last.fm
5. Phase 5 (1 week): Cleanup - Remove Python entirely

**Recommendation**: PROCEED WITH MIGRATION. Benefits outweigh effort.
<!-- SECTION:NOTES:END -->
