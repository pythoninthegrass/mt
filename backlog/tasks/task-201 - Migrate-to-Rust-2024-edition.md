---
id: task-201
title: Migrate to Rust 2024 edition
status: In Progress
assignee: []
created_date: '2026-01-25 05:26'
updated_date: '2026-01-25 08:40'
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
- [ ] #1 Cargo.toml edition field updated to "2024"
- [ ] #2 All edition compatibility warnings resolved
- [ ] #3 cargo fix --edition applied successfully
- [ ] #4 Full test suite passes (cargo test)
- [ ] #5 Manual testing confirms no behavioral regressions in Last.fm, scanner, watcher, and database operations
- [ ] #6 Remove #![allow(dependency_on_unit_never_type_fallback)] lint suppression from lib.rs
<!-- AC:END -->
