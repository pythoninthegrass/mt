---
id: task-210
title: Implement minimal Rust build performance optimizations
status: Done
assignee: []
created_date: '2026-01-26 07:41'
updated_date: '2026-01-26 07:53'
labels:
  - performance
  - rust
  - ci
  - build-optimization
dependencies: []
priority: medium
ordinal: 13375
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement low-effort, high-impact Rust compile time optimizations based on [Tips for Faster Rust Compile Times](https://corrode.dev/blog/tips-for-faster-rust-compile-times/).

**Current state:** Project already has good baseline optimizations (lld linker, LTO, CI caching). This plan adds immediate wins with minimal risk.

## Phase 1: Local Development Speed (macOS)

### 1.1 Add macOS Debug Split-Debuginfo
**File:** `src-tauri/Cargo.toml`
**Impact:** Up to 70% faster debug builds on macOS
**Risk:** None (only affects dev profile)

Add to `[profile.dev]`:
```toml
[profile.dev]
split-debuginfo = "unpacked"  # macOS-specific: faster incremental builds
```

### 1.2 Optimize Proc-Macro Compilation
**File:** `src-tauri/Cargo.toml`
**Impact:** Faster builds when proc-macros are dependencies (serde_derive, tauri macros)
**Risk:** Minimal (only affects build scripts and proc-macros during dev)

Add new profile section:
```toml
[profile.dev.build-override]
opt-level = 3  # Optimize build scripts and proc-macros even in dev mode
```

### 1.3 Add cargo-nextest for Faster Test Execution
**Impact:** Up to 60% faster test runs (parallel execution, cleaner output)
**Risk:** None (cargo test still works as fallback)

Steps:
1. Install: `cargo install cargo-nextest`
2. Update Taskfile to use nextest:
   - Change `cargo test` to `cargo nextest run` in test tasks
3. Update CI workflow to cache nextest binary

## Phase 2: CI Build Speed

### 2.1 Disable Incremental Compilation in CI
**File:** `.github/workflows/test.yml`
**Impact:** Faster clean builds in CI (incremental adds overhead)
**Risk:** None (clean builds don't benefit from incremental)

Add to env section of Rust jobs:
```yaml
env:
  CARGO_INCREMENTAL: 0
  CARGO_TERM_COLOR: always
```

### 2.2 Split Compilation and Test Execution
**File:** `.github/workflows/test.yml`
**Impact:** Better CI visibility and failure isolation
**Risk:** None (separates concerns)

Change test command from:
```bash
cargo tarpaulin ...
```

To:
```bash
cargo test --no-run  # Compile tests only
cargo test           # Run tests
```

### 2.3 Add Swatinem/rust-cache Action
**File:** `.github/workflows/test.yml`
**Impact:** Faster dependency caching (replaces manual cache setup)
**Risk:** None (better maintained than custom cache)

Replace existing cache steps with:
```yaml
- uses: Swatinem/rust-cache@v2
  with:
    workspaces: src-tauri
    cache-on-failure: true
```

## Phase 3: Dependency Optimization (Low-Hanging Fruit)

### 3.1 Audit Tokio Features
**File:** `src-tauri/Cargo.toml`
**Impact:** Reduce compilation units by disabling unused async features
**Risk:** Low (need to verify which features are actually used)

Current: `tokio = { version = "1", features = ["full"] }`

Investigate actual usage and potentially trim to:
```toml
tokio = { version = "1", features = ["rt-multi-thread", "macros", "sync", "time"] }
```

### 3.2 Check for Duplicate Dependencies
**Command:** `cargo tree --duplicate`
**Impact:** Identify version conflicts causing duplicate compilations
**Risk:** None (informational only)

Run and document findings for future cleanup.

### 3.3 Remove Unused Dependencies
**Command:** `cargo machete` or `cargo-udeps`
**Impact:** Eliminate unnecessary compilation work
**Risk:** Low (verify before removing)

Install and run one of:
- `cargo install cargo-machete && cargo machete`
- `cargo install cargo-udeps && cargo +nightly udeps`

## Phase 4: Tooling Setup

### 4.1 Add Build Timing Analysis
**Impact:** Data-driven optimization decisions
**Risk:** None (informational)

Add task to Taskfile.yml:
```yaml
build:timings:
  desc: Analyze build performance bottlenecks
  dir: src-tauri
  cmds:
    - cargo build --timings
    - open target/cargo-timings/cargo-timing.html
```

### 4.2 Document cargo check Workflow
**Impact:** 2-3x faster validation during development
**Risk:** None (complement to cargo build)

Add to CLAUDE.md development workflow:
```bash
# Fast syntax/type checking (no binary output)
cargo check

# Full build with executable
cargo build
```

## Critical Files to Modify

1. `src-tauri/Cargo.toml` - Profile optimizations (1.1, 1.2, 3.1)
2. `.github/workflows/test.yml` - CI optimizations (2.1, 2.2, 2.3)
3. `Taskfile.yml` or `taskfiles/rust.yml` - Add nextest, timings tasks (1.3, 4.1)
4. `CLAUDE.md` - Document new workflow commands (4.2)

## Verification Plan

### Local Development
1. **Before/After Timing:**
   ```bash
   # Clean build timing (before)
   cargo clean && time cargo build

   # Clean build timing (after profile changes)
   cargo clean && time cargo build
   ```

2. **Incremental Build Timing:**
   ```bash
   # Touch a file and rebuild
   touch src-tauri/src/main.rs
   time cargo build
   ```

3. **Test Execution Speed:**
   ```bash
   # Before (with cargo test)
   time cargo test

   # After (with nextest)
   time cargo nextest run
   ```

### CI Verification
1. **Check CI build times** in GitHub Actions after merge
2. **Compare workflow duration** for similar commits before/after
3. **Verify caching is working** (look for "cache hit" in logs)

### Dependency Audit
1. **Run duplicate check:**
   ```bash
   cd src-tauri
   cargo tree --duplicate | tee duplicate-deps.txt
   ```

2. **Run unused dependency check:**
   ```bash
   cargo machete src-tauri
   ```

3. **Check feature usage:**
   ```bash
   # Verify Tokio features actually needed
   cargo tree -i tokio -e features
   ```

## Expected Improvements

| Optimization | Local Dev | CI Builds | Effort |
|-------------|-----------|-----------|---------|
| macOS split-debuginfo | 30-70% | N/A | 1 line |
| Proc-macro opt-level | 5-15% | 5-10% | 3 lines |
| cargo-nextest | N/A (test execution) | 30-60% (test time) | 15min |
| CI CARGO_INCREMENTAL=0 | N/A | 5-10% | 1 line |
| rust-cache action | N/A | 10-20% | 5 lines |
| Tokio feature trimming | 2-5% | 2-5% | 1 line + verification |

**Total estimated time:** 1-2 hours for all changes
**Risk level:** Minimal (mostly additive configuration)

## Implementation Order

1. **Immediate (< 5 min):** Phase 2.1 (CARGO_INCREMENTAL)
2. **Quick wins (< 30 min):** Phase 1.1, 1.2 (profile settings)
3. **Medium effort (< 1 hour):** Phase 2.3 (rust-cache), Phase 1.3 (nextest)
4. **Analysis phase (ongoing):** Phase 3 (dependency audit)
5. **Documentation:** Phase 4.2 (workflow docs)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All Phase 1 optimizations implemented in src-tauri/Cargo.toml
- [x] #2 All Phase 2 CI optimizations implemented in .github/workflows/test.yml
- [x] #3 cargo-nextest integrated into Taskfile and CI
- [x] #4 Phase 3 dependency audit completed with findings documented
- [x] #5 Phase 4 tooling and documentation added
- [ ] #6 Verification plan executed with before/after measurements
- [x] #7 All tests pass with new configurations
<!-- AC:END -->
