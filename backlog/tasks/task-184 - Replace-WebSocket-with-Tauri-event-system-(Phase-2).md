---
id: task-184
title: Replace WebSocket with Tauri event system (Phase 2)
status: In Progress
assignee: []
created_date: '2026-01-21 17:38'
updated_date: '2026-01-21 18:32'
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
- [ ] #1 All 8 event types migrated to Tauri events
- [ ] #2 Rust event structs created with serde
- [ ] #3 Frontend updated to use appWindow.listen()
- [ ] #4 WebSocket code removed (backend and frontend)
- [ ] #5 Real-time updates working in UI
- [ ] #6 Event payload types match original
- [ ] #7 Performance verified (no regressions)
<!-- AC:END -->
