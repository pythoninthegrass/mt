---
id: task-201
title: Migrate to Rust 2024 edition
status: In Progress
assignee: []
created_date: '2026-01-25 05:26'
updated_date: '2026-01-25 23:04'
labels:
  - rust
  - migration
  - edition-2024
  - technical-debt
  - maintenance
dependencies: []
priority: low
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate the codebase from Rust 2021 edition to Rust 2024 edition to address future compatibility warnings and take advantage of new language features.

## Background

The project currently uses Rust 2021 edition with a forward-compatibility lint suppression (`#![allow(dependency_on_unit_never_type_fallback)]`). The compiler emits 13 warnings about relative drop order changes that will affect behavior in Rust 2024.

## Migration Approach

Use `cargo fix --edition` to automatically fix edition-incompatible code:

```bash
cargo fix --edition --allow-dirty --allow-staged
```

Then update `Cargo.toml`:
```toml
edition = "2024"
```

## Affected Areas

The warnings indicate drop order changes in:
1. **Last.fm client** (`src/commands/lastfm.rs:251, 322, 672`) - async operations with client lifetimes
2. **Scanner** (`src/scanner/commands.rs:132, 144`) - track reconciliation logic
3. **Watcher** (`src/watcher.rs:335, 460, 479, 526`) - file monitoring and track updates
4. **Database queries** (`src/db/library.rs:135, 152, 543, 562`) - statement drop order

These are mostly related to temporary values in match expressions and async `.await` points where destructors are involved.

## Testing Requirements

After migration:
- Run full test suite: `cargo test`
- Manual testing of:
  - Last.fm scrobbling and authentication
  - Library scanning and file watching
  - Database operations
  - Track reconciliation (moved/renamed files)

## References

- [Rust 2024 Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)
- [Temporary Tail Expression Scope Changes](https://doc.rust-lang.org/edition-guide/rust-2024/temporary-tail-expr-scope.html)
- [cargo fix --edition documentation](https://doc.rust-lang.org/cargo/commands/cargo-fix.html#edition-migration)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Cargo.toml edition field updated to "2024"
- [x] #2 All edition compatibility warnings resolved
- [x] #3 cargo fix --edition applied successfully
- [x] #4 Full test suite passes (cargo test)
- [ ] #5 Manual testing confirms no behavioral regressions in Last.fm, scanner, watcher, and database operations
- [x] #6 Remove #![allow(dependency_on_unit_never_type_fallback)] lint suppression from lib.rs
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

All Rust 2024 edition compatibility warnings have been resolved by refactoring code to ensure proper drop order semantics.

### Changes Made

**1. Async functions in lastfm.rs (lines 240-260, 310-356)**
- Fixed: Assigned `.await` results to variables before matching to ensure proper drop order of `client` and temporary values
- Pattern: `let result = future.await; match result { ... }`

**2. Match expression in lastfm.rs (line 672)**
- Fixed: Assigned `db.with_conn(...)` result to variable before matching to prevent early drop of error value
- Pattern: `let add_result = operation(); match add_result { ... }`

**3. Track reconciliation in scanner/commands.rs (lines 132, 144)**
- Fixed: Assigned `library::find_missing_track_*` and `library::reconcile_moved_track` results to variables
- Pattern: `let track_result = find(); let reconcile_result = reconcile();`

**4. File watcher in watcher.rs (lines 335, 460, 479, 526)**
- Fixed: Similar pattern for database operations and track reconciliation
- Pattern: Separate result assignment from conditional checks

**5. Database queries in db/library.rs (lines 135, 152, 543, 562)**
- Fixed: Assigned `stmt.query_row(...)` results to variables before matching
- Pattern: `let result = stmt.query_row(...); match result { ... }`

**6. Removed lint suppression from lib.rs**
- Removed: `#![allow(dependency_on_unit_never_type_fallback)]`
- Clean build with no warnings

### Testing Results

- ✅ All 320 tests pass
- ✅ cargo build succeeds with no warnings
- ✅ cargo test succeeds with no warnings
- ⏳ Manual testing pending user validation

### Drop Order Pattern

The core issue in Rust 2024 is that temporaries in tail expressions (the last expression in a block) are dropped earlier than in Rust 2021. The fix pattern is:

```rust
// Rust 2021 (risky in 2024)
match stmt.query_row([id], mapper) { ... }

// Rust 2024 (safe)
let result = stmt.query_row([id], mapper);
match result { ... }
```

This ensures that the temporary returned by `query_row` doesn't outlive variables it depends on like `stmt`.
<!-- SECTION:NOTES:END -->
