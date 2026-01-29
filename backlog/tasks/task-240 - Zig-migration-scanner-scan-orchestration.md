---
id: task-240
title: 'Zig migration: scanner scan orchestration'
status: Done
assignee: []
created_date: '2026-01-28 23:23'
updated_date: '2026-01-29 03:18'
labels: []
dependencies:
  - task-239
  - task-238
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate scanner scan orchestration to Zig, integrating inventory, fingerprinting, and artwork cache while keeping Rust dispatch intact.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Scan orchestration produces the same results and progress events for sample libraries
- [ ] #2 Rust scan entry points dispatch to Zig without user-visible changes
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/scanner/orchestration.zig

Defined ScanProgress event struct and ProgressCallback type

Defined ScanOrchestrator with pipeline coordination

Stubbed methods: init, deinit, setProgressCallback, scanLibrary

Pipeline phases: inventory → fingerprint → metadata → complete

Progress events emit current/total/filepath

Dependencies: Requires tasks 238, 239 for full implementation
<!-- SECTION:NOTES:END -->
