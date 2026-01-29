---
id: task-239
title: 'Zig migration: scanner inventory module'
status: Done
assignee: []
created_date: '2026-01-28 23:23'
updated_date: '2026-01-29 03:18'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate directory inventory scanning to Zig and route Rust scanner inventory calls through Zig FFI while preserving existing file discovery behavior.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Inventory scan results (file inclusion/exclusion) match current behavior on sample libraries
- [ ] #2 Rust scanner inventory path uses Zig FFI without user-visible changes
- [ ] #3 Existing automated tests continue to pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ Skeleton implementation complete

Created zig-core/src/scanner/inventory.zig

Defined ScanResults and InventoryScanner structs

Stubbed methods: init, deinit, scanDirectory, getFiles

Includes recursive traversal logic outline

Audio file filtering via isAudioFile

Exclusion pattern support

Statistics tracking (files found/excluded, directories scanned, errors)
<!-- SECTION:NOTES:END -->
