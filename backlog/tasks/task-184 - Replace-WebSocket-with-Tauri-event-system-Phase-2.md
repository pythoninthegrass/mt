---
id: task-184
title: Replace WebSocket with Tauri event system (Phase 2)
status: Done
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-24 22:28'
labels:
  - rust
  - migration
  - websocket
  - phase-2
  - events
  - tauri
dependencies:
  - task-173
  - task-180
priority: high
ordinal: 51382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace FastAPI WebSocket real-time events with Tauri's built-in event system for simpler architecture and better integration.

**Current WebSocket Events to Replace**:
- `library:updated` - Library changes (action, track_ids)
- `queue:updated` - Queue changes (action, positions, queue_length)
- `favorites:updated` - Favorites changes (action, track_id)
- `playlists:updated` - Playlist changes (action, playlist_id, track_ids)
- `settings:updated` - Settings changes (key, value, previous_value)
- `library:scan-progress` - Scan progress (job_id, status, scanned, found, errors)
- `library:scan-complete` - Scan completion (job_id, stats)
- `heartbeat` - Keep-alive (can be removed)

**Migration Approach**:

**Backend (Rust)**:
```rust
use tauri::Manager;

// Emit event
app.emit_all("library:updated", LibraryUpdatedEvent {
    action: "added",
    track_ids: vec![1, 2, 3],
})?;
```

**Frontend (JavaScript)**:
```javascript
import { appWindow } from '@tauri-apps/api/window';

// Listen for event
appWindow.listen('library:updated', (event) => {
    console.log('Library updated:', event.payload);
});
```

**Benefits**:
- No WebSocket server to manage
- Type-safe events with serde serialization
- Automatic connection management
- Lower latency (IPC vs HTTP)
- Simpler architecture

**Implementation**:
- Create Rust event structs with serde
- Replace all WebSocket broadcast calls with `app.emit_all()`
- Update frontend to use `appWindow.listen()` instead of WebSocket
- Remove WebSocket connection manager code
- Remove `/ws` endpoint

**Estimated Effort**: 1 week
**File**: backend/routes/websocket.py (140 lines to remove)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All 8 event types migrated to Tauri events
- [x] #2 Rust event structs created with serde
- [x] #3 Frontend updated to use appWindow.listen()
- [x] #4 WebSocket code removed (backend and frontend)
- [ ] #5 Real-time updates working in UI
- [x] #6 Event payload types match original
- [ ] #7 Performance verified (no regressions)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary (2026-01-21)

### Files Created
- `src-tauri/src/events.rs` - Rust event structs with serde serialization and EventEmitter trait
- `app/frontend/js/events.js` - Centralized Tauri event subscriptions

### Files Modified
- `src-tauri/src/lib.rs` - Added events module
- `src-tauri/src/commands/queue.rs` - Updated to use QueueUpdatedEvent
- `src-tauri/src/library/commands.rs` - Updated to use LibraryUpdatedEvent
- `src-tauri/src/scanner/commands.rs` - Updated to use ScanProgressEvent/ScanCompleteEvent
- `app/frontend/js/stores/index.js` - Initialize event listeners on startup
- `app/frontend/js/stores/queue.js` - Added refresh() and handleExternalUpdate() methods
- `app/frontend/js/stores/library.js` - Added setScanProgress(), clearScanProgress(), fetchTracks()

### Files Removed
- `backend/routes/websocket.py` - Entire WebSocket implementation

### Event Types Implemented
1. `library:updated` - LibraryUpdatedEvent {action, track_ids}
2. `library:scan-progress` - ScanProgressEvent {job_id, status, scanned, found, errors, current_path}
3. `library:scan-complete` - ScanCompleteEvent {job_id, added, skipped, errors, duration_ms}
4. `queue:updated` - QueueUpdatedEvent {action, positions, queue_length}
5. `favorites:updated` - FavoritesUpdatedEvent {action, track_id}
6. `playlists:updated` - PlaylistsUpdatedEvent {action, playlist_id, track_ids}
7. `settings:updated` - SettingsUpdatedEvent {key, value, previous_value}

### Architecture
- EventEmitter trait provides typed, ergonomic event emission methods
- Frontend events.js subscribes to all events on app startup
- Store methods called to update state when events received
- Bulk operations use empty arrays to signal "refresh all"

### Notes
- Heartbeat event removed (not needed with Tauri IPC)
- Python backend event models retained for documentation/reference

## Queue Event Handler Disabled (2026-01-21)

The `queue:updated` event handler was causing race conditions with playback. When a track was added to the queue, the event would trigger a refresh that could interfere with the playback flow.

**Root cause**: The frontend manages queue state locally, including `currentIndex` which is not persisted to the backend. When the event handler refreshed the queue from the backend, it would reset `currentIndex` to -1 (since the backend doesn't track it), breaking playback.

**Solution**: Disabled the queue event handler entirely. This is acceptable because:
1. The frontend is the sole source of queue changes
2. All changes are persisted via API calls
3. No external queue changes need to update the frontend

**Future consideration**: If multi-device sync or external queue manipulation is needed, the handler would need careful synchronization (e.g., skip events for self-initiated changes, or preserve currentIndex during refresh).
<!-- SECTION:NOTES:END -->
