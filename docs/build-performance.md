# Build Performance Workflow

This document covers build performance optimization for mt development.

## Current Configuration

### Dev Profile (`src-tauri/Cargo.toml`)

```toml
[profile.dev]
split-debuginfo = "unpacked"  # macOS: faster incremental debug builds
debug = "line-tables-only"    # Reduced debug info, still get line numbers in backtraces

[profile.dev.build-override]
opt-level = 3  # Optimize proc-macros and build scripts
```

### Linker (`src-tauri/.cargo/config.toml`)

```toml
[build]
rustflags = ["-C", "link-arg=-fuse-ld=lld"]
```

## Performance Results

Measured on Apple M4 Max, macOS 15.7.1, Rust 1.92.0:

| Scenario | Time | Notes |
|----------|------|-------|
| Cold build | ~48s | Full rebuild from clean |
| Incremental build | ~776ms | After touching `src/main.rs` |

The incremental build target of ≤1.0s is met.

## Baseline Protocol

Use [hyperfine](https://github.com/sharkdp/hyperfine) for accurate measurements:

```bash
cd src-tauri

# Cold build (3 runs with cargo clean before each)
hyperfine --runs 3 --prepare 'cargo clean' 'cargo build'

# Incremental build (5 runs, 2 warmup)
hyperfine --warmup 2 --runs 5 --prepare 'touch src/main.rs' 'cargo build'

# Build timing breakdown (HTML report)
cargo build --timings
# Output: target/cargo-timings/cargo-timing.html
```

### Environment Checklist

Before benchmarking, verify:

```bash
rustc -Vv              # Rust version
cargo -V               # Cargo version
env | grep RUSTFLAGS   # Should be empty (or match config.toml)
env | grep RUSTC_WRAPPER  # Should be empty (no sccache)
```

Ensure consistent power state (AC power, low power mode off).

## Linker Options by Platform

### macOS (ARM64)

| Linker | Status | Notes |
|--------|--------|-------|
| **lld** | Recommended | Currently configured, fast and stable |
| ld-prime | Alternative | Apple's default, similar performance |
| sold | Avoid | Fastest but has codesign issues |

### Linux

| Linker | Status | Notes |
|--------|--------|-------|
| **mold** | Recommended | Fastest option |
| lld | Alternative | Good fallback |

```toml
# Linux config (src-tauri/.cargo/config.toml)
[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "link-arg=-fuse-ld=mold"]
```

### Windows

| Linker | Status | Notes |
|--------|--------|-------|
| rust-lld | Recommended | Fast for full builds |
| link.exe | Alternative | Better for tiny incrementals |

```toml
# Windows config (src-tauri/.cargo/config.toml)
[target.x86_64-pc-windows-msvc]
rustflags = ["-C", "link-arg=-fuse-ld=lld"]
```

## Debugging with Reduced Debug Info

The `debug = "line-tables-only"` setting provides:
- Line numbers in backtraces
- Faster builds and smaller binaries

For full debugging (variable inspection in debuggers), temporarily change to:

```toml
[profile.dev]
debug = true  # or debug = 2 for maximum info
```

## Quick Reference

```bash
# Development server
task tauri:dev

# Quick syntax check (no binary, faster than build)
cargo check --manifest-path src-tauri/Cargo.toml

# Run all tests
task test

# Build timing analysis
task build:timings
```

## References

- [Cargo Build Performance](https://doc.rust-lang.org/cargo/guide/build-performance.html)
- [Rust Performance Book - Build Configuration](https://nnethercote.github.io/perf-book/build-configuration.html)
- [Apple ld-prime (WWDC 2023)](https://developer.apple.com/videos/play/wwdc2023/10268/)
