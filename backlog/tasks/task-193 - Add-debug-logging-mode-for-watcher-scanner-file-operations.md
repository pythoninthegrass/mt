---
id: task-193
title: Add debug logging mode for watcher/scanner file operations
status: Done
assignee: []
created_date: '2026-01-22 21:34'
updated_date: '2026-01-24 22:28'
labels:
  - debugging
  - logging
  - scanner
  - watcher
  - dx
dependencies: []
priority: medium
ordinal: 27382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Currently the watcher and scanner only log high-level counts and status messages. There is no per-file traceability for debugging move detection, reconciliation, or missing track issues.

### Problem
When troubleshooting file move detection or duplicate track issues, there's no way to see:
- Which files were classified as added/deleted/modified
- Which files triggered inode or content hash reconciliation
- Which files were marked as missing
- Which files were treated as truly new vs reconciled

### Requested Feature
Add a debug logging mode that outputs per-file operations:
- `[scan] added: /path/to/file.mp3`
- `[scan] deleted: /path/to/file.mp3`
- `[scan] modified: /path/to/file.mp3`
- `[scan] reconciled(inode=12345): /old/path.mp3 -> /new/path.mp3`
- `[scan] reconciled(hash=sha256:abc...): /old/path.mp3 -> /new/path.mp3`
- `[scan] missing: /path/to/file.mp3`
- `[scan] new: /path/to/file.mp3 (inode=X, hash=Y)`

### Implementation Notes
- Could be controlled via environment variable (e.g., `MT_DEBUG_SCAN=1`)
- Or a settings toggle in the app
- Should use Rust `log` crate with `debug!` or `trace!` level
- Affects: `src-tauri/src/watcher.rs`, `src-tauri/src/scanner/commands.rs`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Debug logging can be enabled via environment variable or setting
- [x] #2 Each file operation (add/delete/modify/reconcile/missing) is logged with full filepath
- [x] #3 Reconciliation logs include which method matched (inode vs content hash)
- [x] #4 Reconciliation logs include old path -> new path mapping
- [x] #5 New track logs include captured inode and content hash values
- [x] #6 Logging does not impact performance when disabled
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Could be controlled via environment variable (e.g., `MT_DEBUG_SCAN=1`)
- Or a settings toggle in the app
- Should use Rust `log` crate with `debug!` or `trace!` level
- Affects: `src-tauri/src/watcher.rs`, `src-tauri/src/scanner/commands.rs`
<!-- SECTION:DESCRIPTION:END -->
<!-- SECTION:NOTES:END -->
