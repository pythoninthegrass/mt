# Tauri Migration Architecture

This document describes the target architecture for migrating MT from Tkinter/VLC to Tauri with native Rust audio playback.

## Overview

The migration replaces the current Python/Tkinter/VLC stack with a modern architecture:

| Current | Target |
|---------|--------|
| Tkinter GUI | Tauri WebView (Alpine.js + Basecoat) |
| VLC playback | Rust audio engine (symphonia + rodio) |
| Python monolith | Python sidecar (PEX) for data operations |
| macOS-only media keys | Cross-platform via Tauri plugins |

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Tauri Application                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Frontend (WebView)                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │  Alpine.js  │  │  Basecoat   │  │    Player Controls      │   │   │
│  │  │   Stores    │  │  Components │  │    Library Browser      │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                    Tauri invoke / events                                 │
│                              │                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Tauri Core (Rust)                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │   Window    │  │   Menus     │  │     Media Keys          │   │   │
│  │  │  Lifecycle  │  │   & Tray    │  │   (tauri-plugin-global- │   │   │
│  │  │             │  │             │  │    shortcut)            │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  │                                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐   │   │
│  │  │              Rust Audio Engine                             │   │   │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐  │   │   │
│  │  │  │ symphonia │  │   rodio   │  │   Audio State         │  │   │   │
│  │  │  │  (decode) │  │  (output) │  │   (position, volume)  │  │   │   │
│  │  │  └───────────┘  └───────────┘  └───────────────────────┘  │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                    Sidecar management                                    │
│                              │                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                 Python Sidecar (PEX)                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │  FastAPI    │  │  SQLite     │  │    Library Scanner      │   │   │
│  │  │  REST API   │  │  Database   │  │    (mutagen metadata)   │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │   │
│  │  │  Playlists  │  │   Lyrics    │  │    WebSocket Events     │   │   │
│  │  │  Management │  │   Fetching  │  │    (real-time updates)  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Tauri Core (Rust)

The Rust layer handles performance-critical and platform-specific functionality:

| Component | Responsibility |
|-----------|----------------|
| **Window Lifecycle** | Create, resize, minimize, close, fullscreen |
| **Native Menus** | Application menu, context menus, system tray |
| **Media Keys** | Global hotkeys via `tauri-plugin-global-shortcut` |
| **Audio Engine** | Decode and play audio with sub-millisecond latency |
| **Sidecar Management** | Spawn, monitor, and communicate with Python process |
| **Auto-Updater** | Check for and apply application updates |

### Rust Audio Engine

Native audio playback replacing VLC:

| Library | Purpose |
|---------|---------|
| **symphonia** | Audio decoding (FLAC, MP3, M4A/AAC, OGG/Vorbis, WAV) |
| **rodio** | Audio output abstraction (wraps cpal) |
| **cpal** | Cross-platform audio I/O |

**Audio State:**
- Current position (milliseconds)
- Duration
- Volume (0.0 - 1.0)
- Playing/paused state
- Loop mode (none, track, queue)

### Python Sidecar (PEX)

Data operations that benefit from Python's ecosystem:

| Component | Responsibility |
|-----------|----------------|
| **FastAPI Server** | REST API for library/playlist operations |
| **SQLite Database** | Persistent storage (reuses existing schema) |
| **Library Scanner** | Directory traversal, mutagen metadata extraction |
| **Playlist Manager** | CRUD operations for playlists |
| **Lyrics Fetcher** | External API integration (Genius, etc.) |
| **WebSocket Server** | Real-time events (scan progress, library updates) |

**Why PEX?**
- Single-file distribution (no Python installation required)
- Bundles all dependencies
- Cross-platform (same PEX works on macOS/Linux)
- Fast startup (~200ms)

### Frontend (WebView)

Modern web UI replacing Tkinter:

| Technology | Purpose |
|------------|---------|
| **Alpine.js** | Reactive state management, minimal footprint |
| **Basecoat** | Tailwind-based component library |
| **Vite** | Fast development builds, HMR |

**UI Components:**
- Library browser (tree view with virtual scrolling)
- Queue view (drag-and-drop reordering)
- Player controls (play/pause, seek, volume)
- Search bar (instant filtering)
- Sidebar navigation (library sections, playlists)

## Communication Patterns

### Frontend ↔ Tauri Core

**Tauri Invoke (Commands):**
```typescript
// Frontend calls Rust function
const status = await invoke('get_playback_status');
await invoke('play_track', { path: '/path/to/song.mp3' });
await invoke('seek', { position_ms: 30000 });
```

**Tauri Events (Push):**
```typescript
// Rust pushes updates to frontend
listen('playback-progress', (event) => {
  playerStore.position = event.payload.position_ms;
});

listen('track-ended', () => {
  playerStore.playNext();
});
```

### Tauri Core ↔ Python Sidecar

**REST API (Request/Response):**
```rust
// Rust calls Python sidecar
let response = reqwest::get("http://localhost:5556/api/library").await?;
let tracks: Vec<Track> = response.json().await?;
```

**WebSocket (Real-time):**
```rust
// Python pushes scan progress
// Rust forwards to frontend via Tauri events
ws.on_message(|msg| {
    app.emit_all("scan-progress", msg.payload);
});
```

### Communication Flow Example

```
User clicks "Add Music" button
         │
         ▼
┌─────────────────┐
│    Frontend     │  invoke('start_scan', { path: '/Music' })
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Tauri Core    │  POST http://localhost:5556/api/scan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Sidecar  │  Scans directory, extracts metadata
└────────┬────────┘
         │ WebSocket: { "type": "scan_progress", "count": 150 }
         ▼
┌─────────────────┐
│   Tauri Core    │  emit_all("scan-progress", payload)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Frontend     │  Updates progress bar
└─────────────────┘
```

## Platform Support Strategy

### Phase 1: macOS (Primary)

**Target:** macOS 12+ (Monterey and later)

| Feature | Implementation |
|---------|----------------|
| Window chrome | Native titlebar with traffic lights |
| Media keys | `tauri-plugin-global-shortcut` |
| Menu bar | Native application menu |
| Notifications | Native notification center |
| File associations | Info.plist configuration |

### Phase 2: Linux

**Target:** Ubuntu 22.04+, Fedora 38+

| Feature | Implementation |
|---------|----------------|
| Window chrome | Client-side decorations (CSD) |
| Media keys | D-Bus MPRIS integration |
| System tray | libappindicator |
| Audio output | PulseAudio/PipeWire via cpal |

### Phase 3: Windows

**Target:** Windows 10/11

| Feature | Implementation |
|---------|----------------|
| Window chrome | Native Win32 frame |
| Media keys | System Media Transport Controls (SMTC) |
| System tray | Windows notification area |
| Audio output | WASAPI via cpal |

## Directory Structure (Target)

```
mt/
├── src-tauri/              # Tauri Rust backend
│   ├── src/
│   │   ├── main.rs         # Entry point
│   │   ├── audio/          # Audio engine module
│   │   │   ├── mod.rs
│   │   │   ├── player.rs   # Playback control
│   │   │   └── decoder.rs  # symphonia integration
│   │   ├── commands/       # Tauri command handlers
│   │   │   ├── mod.rs
│   │   │   ├── playback.rs
│   │   │   └── library.rs
│   │   └── sidecar.rs      # Python process management
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                    # Frontend source
│   ├── index.html
│   ├── main.js             # Alpine.js initialization
│   ├── stores/             # Alpine.js stores
│   │   ├── player.js
│   │   └── library.js
│   ├── components/         # UI components
│   │   ├── library-browser.html
│   │   ├── queue-view.html
│   │   └── player-controls.html
│   └── styles/
│       └── main.css        # Tailwind + Basecoat
├── backend/                # Python sidecar
│   ├── main.py             # FastAPI entry point
│   ├── api/                # REST endpoints
│   ├── core/               # Reused from current codebase
│   │   ├── db/
│   │   ├── library.py
│   │   └── queue.py
│   └── requirements.txt
├── package.json            # Frontend dependencies
├── vite.config.js
└── tailwind.config.js
```

## Migration Path

### Hard-Cut Approach

The migration uses a **hard-cut** strategy rather than incremental replacement:

1. **Phase 1 (Infrastructure)**: Set up Tauri project, worktree, documentation
2. **Phase 2 (Audio)**: Build Rust audio engine, expose via Tauri commands
3. **Phase 3 (Backend)**: Create Python FastAPI sidecar, package as PEX
4. **Phase 4 (Frontend)**: Build Alpine.js UI with Basecoat components
5. **Phase 5 (Polish)**: Media keys, drag-drop, keyboard shortcuts, platform support

### Data Migration

- **Database**: Reuse existing SQLite schema (`mt.db`)
- **Preferences**: Migrate from current settings table
- **Playlists**: Direct compatibility (same schema)

### Rollback Strategy

The original Tkinter application remains functional in the `main` branch. The `tauri-migration` worktree allows parallel development without risk to the existing codebase.

## Performance Targets

| Metric | Target | Current (Tkinter/VLC) |
|--------|--------|----------------------|
| Cold start | < 500ms | ~2s |
| Track switch | < 50ms | ~200ms |
| Memory (idle) | < 100MB | ~150MB |
| CPU (playing) | < 5% | ~8% |
| Binary size | < 50MB | N/A (requires Python) |

## Dependencies

### Rust (Cargo.toml)

```toml
[dependencies]
tauri = { version = "2", features = ["shell-open"] }
symphonia = { version = "0.5", features = ["mp3", "flac", "aac", "ogg"] }
rodio = "0.19"
tokio = { version = "1", features = ["full"] }
reqwest = { version = "0.12", features = ["json"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[dependencies.tauri-plugin-global-shortcut]
version = "2"
```

### Python (pyproject.toml)

```toml
[project]
name = "mt-backend"
version = "0.1.0"
requires-python = ">=3.12,<3.13"

dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "mutagen>=1.47.0",
    "aiosqlite>=0.20",
    "websockets>=13",
    "httpx>=0.28",
    "eliot>=1.17.5",
    "eliot-tree>=24.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# PEX build: uv run pex . -o mt-backend.pex -c mt-backend
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "alpinejs": "^3.14",
    "@aspect/basecoat": "^0.1"
  },
  "devDependencies": {
    "vite": "^6",
    "tailwindcss": "^3.4",
    "@tailwindcss/forms": "^0.5"
  }
}
```
