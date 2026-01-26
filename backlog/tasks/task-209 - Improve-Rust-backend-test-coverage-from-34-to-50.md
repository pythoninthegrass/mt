---
id: task-209
title: Improve Rust backend test coverage from 34% to 50%
status: In Progress
assignee: []
created_date: '2026-01-26 07:27'
updated_date: '2026-01-26 07:47'
labels:
  - testing
  - coverage
  - rust
  - ci
dependencies: []
priority: high
ordinal: 14375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
Rust backend code coverage has dropped to 34.12% (1226/3593 lines), below the CI threshold of 50%, causing the rust-tests job to fail.

## Current Coverage by Module (Low Coverage Priority)
**0% coverage (critical):**
- src/audio/engine.rs: 0/108
- src/commands/audio.rs: 0/118
- src/library/commands.rs: 0/170
- src/scanner/commands.rs: 0/118
- src/watcher.rs: 0/348
- src/dialog.rs: 0/41
- src/media_keys.rs: 0/54
- src/metadata.rs: 0/86

**Low coverage (needs improvement):**
- src/commands/lastfm.rs: 17/327 (5%)
- src/commands/settings.rs: 9/109 (8%)

**Acceptable coverage (>50%):**
- src/db/favorites.rs: 73/129 (57%)
- src/db/library.rs: 135/290 (47% - close)
- src/db/playlists.rs: 126/182 (69%)
- src/db/queue.rs: 108/162 (67%)
- src/db/schema.rs: 56/72 (78%)
- src/db/settings.rs: 57/61 (93%)
- src/scanner/metadata.rs: 53/101 (52%)

## Target
Achieve 50%+ coverage to pass CI threshold.

## Context
- task-203 achieved ~56% coverage but coverage has regressed
- CI uses cargo-tarpaulin with `--fail-under 50` threshold
- `continue-on-error: true` currently allows failures but should be fixed
- Coverage report: `/home/runner/work/mt/mt/src-tauri/coverage/tarpaulin-report.html`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Rust backend coverage reaches 50% or higher
- [ ] #2 CI rust-tests job passes without continue-on-error
- [ ] #3 Priority: Test commands modules (audio, library, scanner) with 0% coverage
- [ ] #4 Add unit tests for watcher.rs event handling logic
- [ ] #5 Add integration tests for dialog.rs and media_keys.rs interaction
<!-- AC:END -->
