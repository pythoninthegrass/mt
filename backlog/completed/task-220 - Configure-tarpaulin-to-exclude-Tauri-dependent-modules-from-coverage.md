---
id: task-220
title: Configure tarpaulin to exclude Tauri-dependent modules from coverage
status: Done
assignee: []
created_date: '2026-01-27 22:33'
updated_date: '2026-01-27 22:35'
labels:
  - ci
  - coverage
  - rust
dependencies:
  - task-209
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
~40% of the codebase requires Tauri runtime and cannot be unit tested. Including these modules in coverage calculation makes the 50% threshold unreachable and the metric meaningless.

## Modules to Exclude
- `src/commands/*` - Tauri command wrappers
- `src/lib.rs` - Tauri app setup
- `src/main.rs` - Entry point
- `src/watcher.rs` - Runtime event handlers
- `src/dialog.rs` - Tauri dialog plugin
- `src/media_keys.rs` - System media key integration

## Implementation

Update `.github/workflows/rust-tests.yml`:

```yaml
- name: Run coverage
  run: |
    cargo tarpaulin --out Html --output-dir coverage \
      --exclude-files "src/commands/*" \
      --exclude-files "src/lib.rs" \
      --exclude-files "src/main.rs" \
      --exclude-files "src/watcher.rs" \
      --exclude-files "src/dialog.rs" \
      --exclude-files "src/media_keys.rs" \
      --fail-under 50
```

## Rationale
- The `db::*` layer is where bugs actually live
- Command wrappers are 5-10 lines of `db.conn()` → `db_function()` → `app.emit()`
- Testing the data layer catches the same bugs as testing commands
- Makes coverage metric meaningful: "50% of testable code"
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tarpaulin excludes specified modules
- [ ] #2 Coverage threshold set to 50%
- [ ] #3 CI reports coverage of testable code only
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Completed 2026-01-27

Updated `.github/workflows/test.yml` to exclude Tauri-dependent modules from coverage:
- src/commands/*
- src/lib.rs
- src/main.rs
- src/watcher.rs
- src/dialog.rs
- src/media_keys.rs

Coverage with exclusions: **54.07%** (1202/2223 lines) - above 50% threshold.

The excluded modules require Tauri runtime and cannot be unit tested without mocking the entire Tauri context.
<!-- SECTION:NOTES:END -->
