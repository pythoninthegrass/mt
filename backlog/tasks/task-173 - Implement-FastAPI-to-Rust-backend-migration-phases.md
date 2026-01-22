---
id: task-173
title: Implement FastAPI to Rust backend migration phases
status: In Progress
assignee: []
created_date: '2026-01-19 06:16'
updated_date: '2026-01-21 17:25'
labels:
  - implementation
  - backend
  - rust
  - migration
  - fastapi
  - sidecar
dependencies:
  - task-172
priority: medium
ordinal: 656.25
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the migration findings from the FastAPI PEX sidecar analysis. Execute the phased migration plan, starting with highest impact, lowest complexity items.

Migration phases to implement:
1. **Phase 1 (Core Infrastructure)**: Database operations, settings management, basic queue operations
2. **Phase 2 (User Experience)**: WebSocket events, advanced queue operations, basic library queries  
3. **Phase 3 (Content Discovery)**: Library scanning, basic metadata extraction, artwork handling
4. **Phase 4 (Advanced Features)**: Full metadata extraction, Last.fm integration, embedded artwork

For each phase:
- Migrate identified functionality from Python to Rust
- Update Tauri commands and frontend integration
- Maintain backward compatibility during transition
- Update tests and verify functionality
- Remove migrated Python endpoints after validation

Ensure incremental progress with working functionality at each phase.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Complete Phase 1: Core infrastructure migration
- [ ] #2 Complete Phase 2: User experience features
- [ ] #3 Complete Phase 3: Content discovery
- [ ] #4 Complete Phase 4: Advanced features
- [ ] #5 Remove Python sidecar dependencies
- [ ] #6 Update all tests and validation
<!-- AC:END -->
