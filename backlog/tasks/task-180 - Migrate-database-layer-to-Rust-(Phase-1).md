---
id: task-180
title: Migrate database layer to Rust (Phase 1)
status: Done
assignee: []
created_date: '2026-01-21 17:37'
updated_date: '2026-01-21 20:47'
labels:
  - rust
  - migration
  - database
  - phase-1
  - foundation
dependencies:
  - task-173
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate the SQLite database layer from Python to Rust, establishing the foundation for all backend operations.

**Scope**:
- Set up rusqlite with r2d2 connection pooling
- Implement all 9 database tables with migrations (refinery or sqlx)
- Create Rust models matching Python Pydantic models
- Implement all CRUD operations with async support (tokio)
- Maintain exact database file format compatibility
- PRAGMA optimizations (WAL mode, foreign keys, 64MB cache)

**Tables to migrate**:
- library (18 columns) - Track metadata
- queue - Playback queue
- playlists - Playlist metadata
- playlist_items - Playlist tracks
- favorites - Favorited tracks
- settings - Key-value config
- scrobble_queue - Offline Last.fm queue
- watched_folders - Auto-scan folders
- lyrics_cache - Cached lyrics

**Rust Crates**:
- rusqlite - SQLite interface
- r2d2 or deadpool - Connection pooling
- refinery or sqlx - Schema migrations
- serde - Model serialization
- tokio - Async runtime

**Critical**: This is the foundation that all other migrations depend on. Must be rock-solid with comprehensive tests.

**Estimated Effort**: 2-3 weeks
**File**: backend/services/database.py (1,502 lines to migrate)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Database schema created with all 9 tables
- [x] #2 All CRUD operations implemented and tested
- [x] #3 Connection pooling configured and tested
- [x] #4 Migration system functional
- [x] #5 Database file format backward compatible
- [x] #6 Comprehensive integration tests passing
- [x] #7 Performance benchmarks documented
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Module Structure
```
src-tauri/src/db/
├── mod.rs           # Module exports, Database struct, connection pool
├── schema.rs        # Table creation SQL, migrations
├── models.rs        # Rust structs matching Python models
├── library.rs       # Library CRUD operations (~18 methods)
├── queue.rs         # Queue operations (~9 methods)
├── favorites.rs     # Favorites operations (~8 methods)
├── playlists.rs     # Playlist operations (~15 methods)
├── settings.rs      # Settings operations (~4 methods)
├── scrobble.rs      # Scrobble queue operations (~5 methods)
├── watched.rs       # Watched folders operations (~8 methods)
└── tests.rs         # Integration tests
```

### Dependencies
- rusqlite 0.34 with bundled feature
- r2d2 0.8 for connection pooling
- r2d2_sqlite 0.25 for rusqlite adapter

### Implementation Order
1. Foundation: deps, connection pool, schema, migrations, PRAGMAs
2. Models: Track, QueueItem, Playlist, etc.
3. Library operations (18 methods)
4. Queue operations (9 methods)
5. Favorites operations (8 methods)
6. Playlist operations (15 methods)
7. Settings, scrobble, watched folders
8. Testing & backward compatibility validation
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Performance Benchmarks (Release Build)

Benchmarked on macOS with in-memory SQLite database.

### Database Initialization
- Average: **0.449 ms**
- Includes: schema creation, 9 tables, indexes, migrations, PRAGMA settings

### Bulk Track Insertion
| Batch Size | Time | Throughput |
|------------|------|------------|
| 100 | 263µs | 380,228 tracks/sec |
| 500 | 1.27ms | 394,737 tracks/sec |
| 1,000 | 2.58ms | 387,072 tracks/sec |
| 5,000 | 12.28ms | 407,056 tracks/sec |

### Track Queries (10,000 tracks)
- Simple query (limit 50): **0.478 ms**
- Search query ('Artist 5'): **1.870 ms**
- Filtered query (artist + album): **0.427 ms**
- Library stats: **1.871 ms**

### Queue Operations
- Add 100 items: **777µs**
- Get queue (100 items): **0.182 ms**
- Clear queue: **5.3µs**

### Playlist Operations
- Create playlist: **0.004 ms**
- Add 100 tracks: **317µs**
- Get playlist with tracks: **0.219 ms**
- List 50 playlists: **0.029 ms**

### Settings Operations
- Set setting: **0.002 ms**
- Get setting: **0.001 ms**
- Get all (1000 entries): **0.176 ms**

### Connection Pool
- Acquire connection: **<0.001 ms**
- with_conn + operation: **0.003 ms**
- Transaction (10 ops): **0.014 ms**

**Conclusion**: Performance is excellent for a desktop music player. Track queries with 10K+ tracks complete in <2ms. Bulk insertion handles 400K+ tracks/sec.
<!-- SECTION:NOTES:END -->
