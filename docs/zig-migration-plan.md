# Rust to Zig Migration Plan

## Overview

This document outlines the plan to migrate business logic from Rust to Zig via FFI, while keeping Tauri as the desktop shell and the AlpineJS/Basecoat frontend unchanged.

### Goals

- Reduce Rust complexity by moving core business logic to Zig
- Leverage Zig's C ABI compatibility for clean FFI boundaries
- Maintain existing Tauri integration layer
- Preserve all existing functionality and tests

### Non-Goals

- Rewriting the frontend
- Replacing Tauri
- Migrating audio playback (remains in Rust due to crate ecosystem)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (unchanged)                      │
│              AlpineJS + Basecoat + Vite                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Tauri Shell (Rust)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ commands/*  │  │  events.rs  │  │   media_keys.rs     │  │
│  │ (dispatch)  │  │             │  │   watcher.rs        │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ffi/ (Rust FFI bindings)               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ C ABI
┌─────────────────────────────────────────────────────────────┐
│                    zig-core (Zig)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  scanner/   │  │    db/      │  │     lastfm/         │  │
│  │  metadata   │  │  library    │  │     client          │  │
│  │  fingerprint│  │  queue      │  │     signature       │  │
│  │  artwork    │  │  playlists  │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
mt/
├── zig-core/
│   ├── build.zig
│   ├── src/
│   │   ├── lib.zig              # FFI exports root
│   │   ├── ffi.zig              # C ABI exports
│   │   ├── types.zig            # Shared types
│   │   ├── scanner/
│   │   │   ├── scanner.zig      # Module root
│   │   │   ├── metadata.zig     # Tag extraction (TagLib)
│   │   │   ├── fingerprint.zig  # File change detection
│   │   │   ├── artwork.zig      # Album art extraction
│   │   │   └── inventory.zig    # Directory scanning
│   │   ├── db/
│   │   │   ├── database.zig     # SQLite connection (zig-sqlite)
│   │   │   ├── models.zig       # Data models
│   │   │   ├── library.zig      # Library queries
│   │   │   ├── queue.zig        # Queue management
│   │   │   ├── playlists.zig    # Playlist CRUD
│   │   │   └── favorites.zig    # Favorites
│   │   └── lastfm/
│   │       ├── client.zig       # HTTP client
│   │       ├── signature.zig    # API signing
│   │       └── types.zig        # API types
│   └── tests/
├── src-tauri/
│   ├── src/
│   │   ├── ffi/                 # Rust FFI bindings
│   │   │   ├── mod.rs
│   │   │   ├── scanner.rs
│   │   │   ├── db.rs
│   │   │   └── lastfm.rs
│   │   └── ... (existing, thinned)
│   └── build.rs                 # Modified to build Zig first
└── app/frontend/                # Unchanged
```

---

## Layer Classification

### Keep in Rust (Tauri integration)

These files stay in Rust permanently—they're thin dispatch or platform-specific:

| File | Reason |
|------|--------|
| `main.rs` | Tauri bootstrap |
| `lib.rs` | Crate root, adds FFI imports |
| `commands/*.rs` | Thin Tauri command handlers (dispatch to Zig) |
| `dialog.rs` | Tauri dialog APIs |
| `events.rs` | Tauri event system |
| `media_keys.rs` | OS-level media key handling |
| `watcher.rs` | fs notify integration |
| `audio/*.rs` | Audio playback (rodio/cpal ecosystem) |

### Migrate to Zig

| File | Target | Notes |
|------|--------|-------|
| `scanner/metadata.rs` | `zig-core/src/scanner/metadata.zig` | TagLib C bindings |
| `scanner/fingerprint.rs` | `zig-core/src/scanner/fingerprint.zig` | Pure computation |
| `scanner/artwork.rs` | `zig-core/src/scanner/artwork.zig` | Image extraction |
| `scanner/artwork_cache.rs` | `zig-core/src/scanner/artwork_cache.zig` | Cache management |
| `scanner/inventory.rs` | `zig-core/src/scanner/inventory.zig` | Directory walking |
| `scanner/scan.rs` | `zig-core/src/scanner/scan.zig` | Orchestration |
| `metadata.rs` | `zig-core/src/metadata.zig` | Shared metadata types |
| `db/models.rs` | `zig-core/src/db/models.zig` | Data structures |
| `db/schema.rs` | `zig-core/src/db/schema.zig` | Schema definitions |
| `db/library.rs` | `zig-core/src/db/library.zig` | Library queries |
| `db/favorites.rs` | `zig-core/src/db/favorites.zig` | Favorites CRUD |
| `db/playlists.rs` | `zig-core/src/db/playlists.zig` | Playlist CRUD |
| `db/queue.rs` | `zig-core/src/db/queue.zig` | Queue state |
| `db/scrobble.rs` | `zig-core/src/db/scrobble.zig` | Scrobble tracking |
| `db/settings.rs` | `zig-core/src/db/settings.zig` | Settings storage |
| `db/watched.rs` | `zig-core/src/db/watched.zig` | Watched folders |
| `lastfm/client.rs` | `zig-core/src/lastfm/client.zig` | HTTP client |
| `lastfm/config.rs` | `zig-core/src/lastfm/config.zig` | Configuration |
| `lastfm/rate_limiter.rs` | `zig-core/src/lastfm/rate_limiter.zig` | Rate limiting |
| `lastfm/signature.rs` | `zig-core/src/lastfm/signature.zig` | API signing |
| `lastfm/types.rs` | `zig-core/src/lastfm/types.zig` | API types |

---

## Migration Order

| Phase | Files | Effort | Risk | Status |
|-------|-------|--------|------|--------|
| 0 | Create `zig-core/`, `build.zig`, `build.rs` integration | 1 day | Low | ✅ Started |
| 1 | `scanner/metadata.rs` → Zig | 2-3 days | Low | ✅ Started |
| 1 | `scanner/fingerprint.rs` → Zig | 1-2 days | Low | ✅ Started |
| 1 | `scanner/artwork.rs`, `artwork_cache.rs` → Zig | 2 days | Low | ⬜ |
| 1 | `scanner/inventory.rs`, `scan.rs` → Zig | 2-3 days | Medium | ⬜ |
| 2 | `db/models.rs`, `db/schema.rs` → Zig | 1 day | Low | ⬜ |
| 2 | `db/library.rs` → Zig | 2-3 days | Medium | ⬜ |
| 2 | `db/queue.rs`, `db/playlists.rs`, `db/favorites.rs` → Zig | 2-3 days | Medium | ⬜ |
| 3 | `lastfm/signature.rs`, `lastfm/types.rs` → Zig | 1 day | Low | ⬜ |
| 3 | `lastfm/client.rs`, `lastfm/rate_limiter.rs` → Zig | 2-3 days | Medium | ⬜ |

---

## FFI Conventions

### Memory Ownership

- **Zig allocates, Zig frees**: Functions that return pointers include a corresponding `mt_free_*` function
- **Caller-provided buffers**: For performance-critical paths, use `*_into` variants that write to caller-provided memory
- **Fixed-size structs**: `ExtractedMetadata` uses fixed-size arrays to avoid heap allocation across FFI

### Error Handling

- Functions return `bool` for success/failure when using out-parameters
- Structs include `is_valid` and `error_code` fields
- Error codes defined in `types.ScanError` enum

### Naming Convention

- All FFI exports prefixed with `mt_`
- Zig functions use camelCase internally
- C ABI exports use snake_case

---

## Build Integration

### build.rs (Rust)

```rust
fn main() {
    // Build Zig library first
    let status = std::process::Command::new("zig")
        .args(["build", "-Doptimize=ReleaseFast"])
        .current_dir("../zig-core")
        .status()
        .expect("failed to build zig-core");
    
    assert!(status.success(), "zig-core build failed");
    
    // Link the static library
    println!("cargo:rustc-link-search=native=../zig-core/zig-out/lib");
    println!("cargo:rustc-link-lib=static=mtcore");
    
    // Link TagLib (required by zig-core)
    println!("cargo:rustc-link-lib=tag_c");
    
    // Rebuild if zig sources change
    println!("cargo:rerun-if-changed=../zig-core/src");
    
    tauri_build::build()
}
```

### Dependencies

**macOS:**
```bash
brew install taglib
```

**Linux:**
```bash
apt install libtag1-dev
```

**Windows:**
```powershell
vcpkg install taglib
```

---

## Testing Strategy

### Unit Tests (Zig)

```bash
cd zig-core
zig build test
```

### Integration Tests (Rust)

Existing Rust tests in `src-tauri/src/**/*_test.rs` continue to work, now exercising FFI paths.

### End-to-End (Playwright)

Frontend tests in `app/frontend/tests/*.spec.js` unchanged.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Cross-platform builds | Test CI on macOS, Windows, Linux early |
| Debugging across FFI | Liberal use of `std.log` in Zig; debug builds log all FFI calls |
| Zig stability (pre-1.0) | Pin Zig version in CI; C ABI won't change |
| TagLib availability | Document installation; consider vendoring |
| SQLite version mismatch | Use zig-sqlite's bundled SQLite |

---

## Current Progress

### Completed

- [x] `zig-core/build.zig` - Build system
- [x] `zig-core/src/lib.zig` - Library root
- [x] `zig-core/src/types.zig` - Core types (`ExtractedMetadata`, `FileFingerprint`, etc.)
- [x] `zig-core/src/ffi.zig` - FFI exports
- [x] `zig-core/src/scanner/scanner.zig` - Scanner module root
- [x] `zig-core/src/scanner/metadata.zig` - Metadata extraction with TagLib
- [x] `zig-core/src/scanner/fingerprint.zig` - File fingerprinting
- [x] `src-tauri/src/ffi/mod.rs` - Rust FFI module
- [x] `src-tauri/src/ffi/scanner.rs` - Rust bindings for scanner FFI

### Next Steps

1. Update `src-tauri/build.rs` to compile Zig first
2. Add `pub mod ffi;` to `src-tauri/src/lib.rs`
3. Test FFI with real audio files
4. Migrate `scanner/artwork.rs`
5. Migrate `scanner/inventory.rs` and `scanner/scan.rs`

---

## Development Workflow

### Building

```bash
# Build Zig library
cd zig-core && zig build

# Build Tauri app (includes Zig build via build.rs)
cd src-tauri && cargo build

# Run tests
cd zig-core && zig build test
cd src-tauri && cargo test
```

### Worktree

The Zig migration work is developed in a separate worktree:

```bash
git worktree add ../mt-zig-migration zig-migration
```

This allows parallel development without disrupting the main branch.
