# Tauri Music Player Implementation Guide

> **Note**: This guide incorporates real-world patterns from production Tauri + PEX sidecar implementations.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Application                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Frontend (WebView)                                   │  │
│  │  - HTML/CSS with Basecoat + Tailwind                  │  │
│  │  - AlpineJS for reactivity                            │  │
│  │  - Testable via tauri-plugin-devtools (dev)           │  │
│  └─────────────────┬─────────────────────────────────────┘  │
│                    │ Tauri Commands                         │
│  ┌─────────────────┴─────────────────────────────────────┐  │
│  │  Tauri Backend (Rust)                                 │  │
│  │  - Audio playback engine (symphonia + rodio)          │  │
│  │  - Window management                                  │  │
│  │  - Sidecar process lifecycle                          │  │
│  │  - System tray & media key integration                │  │
│  └─────────────────┬─────────────────────────────────────┘  │
└────────────────────┼────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     │ localhost:8000
┌────────────────────┴───────────────────────────────────────┐
│  Python Backend Sidecar (PEX SCIE)                         │
│  - FastAPI REST API                                        │
│  - WebSocket for real-time updates                         │
│  - Zig module integration                                  │
│  - File system scanning                                    │
│  - Audio metadata extraction (mutagen)                     │
│  - Library & queue management (SQLite)                     │
│  - Playlist management                                     │
└────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

**Audio Playback in Rust (not Python)**:
- Uses **symphonia** for decoding (FLAC, MP3, M4A/AAC, OGG, WAV)
- Uses **rodio/cpal** for audio output
- Eliminates VLC dependency and its packaging complexity
- Better cross-platform support (no musl/Alpine issues)

**Python Sidecar for Library Management**:
- Handles metadata extraction, library scanning, database operations
- Packaged as PEX SCIE (single executable, no Python installation required)
- Communicates with Rust backend via HTTP/WebSocket

## Phase 1: Project Setup

### 1.1 Initialize Tauri Project

```bash
# Install Tauri CLI (v2)
cargo install tauri-cli --version "^2"

# Create new Tauri project in worktree
wt switch --create tauri-migration --base=main
cargo tauri init

# Project structure
mt/
├── src/                   # Frontend source (Vite + AlpineJS)
│   ├── index.html
│   ├── app.js
│   └── styles/
├── src-tauri/             # Tauri/Rust backend
│   ├── src/
│   │   ├── lib.rs         # Main app setup, sidecar management
│   │   ├── audio.rs       # Symphonia playback engine
│   │   └── commands.rs    # Tauri command handlers
│   ├── bin/               # PEX SCIE binaries (staged here)
│   ├── Cargo.toml
│   └── tauri.conf.json
├── backend/               # Python backend source
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   └── services/
│   └── pyproject.toml
├── src/                   # Existing Zig scanning module
├── taskfiles/             # Taskfile build automation
│   ├── pex.yml
│   └── tauri.yml
└── tests/                 # E2E tests (Tauri WebDriver)
```

### 1.2 Setup Python Backend

```bash
cd backend

# Use uv for dependency management (NOT pip)
uv venv
source .venv/bin/activate

# Install dependencies
uv add fastapi uvicorn websockets python-multipart

# Development dependencies
uv add --dev pytest httpx
```

### 1.3 Install Frontend Dependencies

```bash
# Install build tooling
npm init -y
npm install -D vite tailwindcss @tailwindcss/vite

# Install AlpineJS and Basecoat
npm install alpinejs @nicholascostadev/basecoat
```

## Phase 2: Python Backend Development

### 2.1 Core Backend Structure

**backend/main.py** - Main FastAPI application
- CORS middleware for Tauri webview
- REST endpoints for music library operations
- WebSocket endpoint for real-time updates
- Integration with Zig scanning module

**backend/routes/** - API route handlers
- `/api/library` - Library scanning and indexing
- `/api/tracks` - Track listing and search
- `/api/metadata` - Audio metadata retrieval
- `/api/playlists` - Playlist management
- `/api/playback` - Playback control

**backend/services/** - Business logic
- `scanner.py` - Directory scanning using Zig module
- `metadata.py` - Audio metadata extraction
- `playlist.py` - Playlist operations
- `cache.py` - Metadata caching

### 2.2 Key Backend Features

```python
# backend/main.py structure
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import your_zig_module

app = FastAPI()

# Allow Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST endpoints
@app.get("/api/scan/{path:path}")
async def scan_library(path: str):
    """Fast directory scanning with Zig module"""
    pass

@app.get("/api/tracks")
async def list_tracks(query: str = None, limit: int = 100):
    """List/search tracks"""
    pass

@app.post("/api/playlists")
async def create_playlist(name: str, track_ids: list):
    """Create playlist"""
    pass

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time playback state, progress, etc."""
    await websocket.accept()
    # Handle bidirectional communication
    pass

def run():
    """Entry point for PEX"""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### 2.3 Zig Module Integration

**Option A: Build as Python Extension**
```bash
# In zig-module directory
zig build-lib src/scanner.zig -dynamic -OReleaseFast

# Create Python wrapper using ctypes or CFFI
# Package as wheel for PEX inclusion
python setup.py bdist_wheel
```

**Option B: Separate Shared Library**
- Bundle compiled .so/.dll/.dylib with Tauri resources
- Load via ctypes in Python backend
- Set library paths in Tauri sidecar launcher

### 2.4 Build PEX SCIE File

PEX SCIE (Self-Contained Interpreted Executable) creates a single binary that includes Python itself - no system Python required. This is significantly better than traditional PEX for desktop app distribution.

**Benefits over traditional PEX:**
- 4x faster builds than PyInstaller
- 16% smaller binaries
- No Python installation required on target machine
- Hermetic builds (reproducible)

```bash
# taskfiles/pex.yml - Taskfile for PEX SCIE builds
version: '3'

vars:
  PYTHON_VERSION: "3.12"
  STAGING_DIR: "src-tauri/bin"

tasks:
  build:
    desc: Build PEX SCIE for current platform
    cmds:
      - mkdir -p {{.STAGING_DIR}}
      - |
        pex \
          fastapi uvicorn websockets python-multipart \
          mutagen eliot \
          -P backend/app \
          -e app.main:run \
          --scie eager \
          --scie-only \
          --scie-pbs-stripped \
          --scie-python-version {{.PYTHON_VERSION}} \
          -o {{.STAGING_DIR}}/main-{{.TARGET}}
    vars:
      TARGET:
        sh: |
          case "$(uname -s)-$(uname -m)" in
            Darwin-arm64) echo "aarch64-apple-darwin" ;;
            Darwin-x86_64) echo "x86_64-apple-darwin" ;;
            Linux-x86_64) echo "x86_64-unknown-linux-gnu" ;;
            Linux-aarch64) echo "aarch64-unknown-linux-gnu" ;;
            *) echo "unknown" ;;
          esac

  build-macos-arm:
    desc: Build for macOS ARM64
    cmds:
      - task: build
        vars:
          TARGET: aarch64-apple-darwin

  build-macos-intel:
    desc: Build for macOS x86_64
    cmds:
      - task: build
        vars:
          TARGET: x86_64-apple-darwin

  build-linux:
    desc: Build for Linux x86_64
    cmds:
      - task: build
        vars:
          TARGET: x86_64-unknown-linux-gnu
```

**Key PEX SCIE flags explained:**
- `--scie eager`: Build SCIE immediately (vs lazy extraction)
- `--scie-only`: Output only the SCIE binary (no .pex file)
- `--scie-pbs-stripped`: Use stripped Python Build Standalone (smaller binary)
- `--scie-python-version`: Pin Python version for reproducibility
- `-P backend/app`: Include local package directory
- `-e app.main:run`: Entry point function

**Detecting PEX runtime in Python:**
```python
# backend/app/main.py
import os

def is_frozen() -> bool:
    """Check if running as PEX SCIE binary."""
    return os.environ.get('PEX') is not None

def run():
    """Entry point for PEX SCIE."""
    import uvicorn
    
    # PEX sets working directory differently
    if is_frozen():
        # Adjust paths for bundled execution
        pass
    
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
```

## Phase 3: Tauri Backend Development

### 3.1 Rust Audio Engine (symphonia)

**src-tauri/Cargo.toml** - Dependencies:
```toml
[dependencies]
tauri = { version = "2", features = ["wry"], default-features = false }
tauri-plugin-shell = "2"
tauri-plugin-devtools = { version = "2", optional = true }
symphonia = { version = "0.5", features = ["all"] }
rodio = "0.19"
cpal = "0.15"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[features]
default = []
devtools = ["tauri-plugin-devtools"]
```

**src-tauri/src/audio.rs** - Playback engine:
```rust
use symphonia::core::codecs::{DecoderOptions, CODEC_TYPE_NULL};
use symphonia::core::formats::FormatOptions;
use symphonia::core::io::MediaSourceStream;
use symphonia::core::meta::MetadataOptions;
use symphonia::core::probe::Hint;
use rodio::{OutputStream, Sink};
use std::fs::File;
use std::sync::{Arc, Mutex};

pub struct AudioEngine {
    sink: Arc<Mutex<Option<Sink>>>,
    _stream: OutputStream,
}

impl AudioEngine {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let (stream, stream_handle) = OutputStream::try_default()?;
        let sink = Sink::try_new(&stream_handle)?;
        
        Ok(Self {
            sink: Arc::new(Mutex::new(Some(sink))),
            _stream: stream,
        })
    }
    
    pub fn play(&self, path: &str) -> Result<(), Box<dyn std::error::Error>> {
        let file = File::open(path)?;
        let source = rodio::Decoder::new(std::io::BufReader::new(file))?;
        
        if let Some(sink) = self.sink.lock().unwrap().as_ref() {
            sink.append(source);
            sink.play();
        }
        Ok(())
    }
    
    pub fn pause(&self) {
        if let Some(sink) = self.sink.lock().unwrap().as_ref() {
            sink.pause();
        }
    }
    
    pub fn resume(&self) {
        if let Some(sink) = self.sink.lock().unwrap().as_ref() {
            sink.play();
        }
    }
    
    pub fn stop(&self) {
        if let Some(sink) = self.sink.lock().unwrap().as_ref() {
            sink.stop();
        }
    }
    
    pub fn set_volume(&self, volume: f32) {
        if let Some(sink) = self.sink.lock().unwrap().as_ref() {
            sink.set_volume(volume);
        }
    }
}
```

### 3.2 Sidecar Process Management (Tauri v2)

**src-tauri/src/lib.rs** - Tauri v2 sidecar pattern:
```rust
use tauri::Manager;
use tauri_plugin_shell::ShellExt;

mod audio;
use audio::AudioEngine;

#[tauri::command]
fn get_backend_url() -> String {
    "http://127.0.0.1:8000".to_string()
}

#[tauri::command]
fn play_track(path: String, state: tauri::State<'_, AudioEngine>) -> Result<(), String> {
    state.play(&path).map_err(|e| e.to_string())
}

#[tauri::command]
fn pause(state: tauri::State<'_, AudioEngine>) {
    state.pause();
}

#[tauri::command]
fn resume(state: tauri::State<'_, AudioEngine>) {
    state.resume();
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Initialize audio engine
            let audio = AudioEngine::new()
                .expect("Failed to initialize audio engine");
            app.manage(audio);
            
            // Launch Python backend sidecar
            let shell = app.shell();
            let sidecar = shell.sidecar("main")?;
            
            match sidecar.spawn() {
                Ok((mut rx, _child)) => {
                    // Monitor sidecar output in background
                    tauri::async_runtime::spawn(async move {
                        while let Some(event) = rx.recv().await {
                            match event {
                                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                                    println!("[sidecar stdout] {}", String::from_utf8_lossy(&line));
                                }
                                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                                    eprintln!("[sidecar stderr] {}", String::from_utf8_lossy(&line));
                                }
                                _ => {}
                            }
                        }
                    });
                }
                Err(e) => {
                    eprintln!("Failed to spawn sidecar: {}", e);
                }
            }
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            play_track,
            pause,
            resume,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 3.3 Tauri Configuration (v2)

**src-tauri/tauri.conf.json** - Tauri v2 configuration:
```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "mt",
  "version": "0.1.0",
  "identifier": "com.mt.musicplayer",
  "build": {
    "beforeBuildCommand": "task pex:build && npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "externalBin": [
      "bin/main"
    ]
  },
  "app": {
    "windows": [
      {
        "title": "mt",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600
      }
    ],
    "security": {
      "csp": null
    }
  },
  "plugins": {
    "shell": {
      "sidecar": true,
      "scope": [
        {
          "name": "main",
          "sidecar": true
        }
      ]
    }
  }
}
```

### 3.4 Taskfile Integration

**taskfiles/tauri.yml** - Integrated build workflow:
```yaml
version: '3'

includes:
  pex: ./pex.yml

tasks:
  dev:
    desc: Run Tauri in development mode
    deps: [pex:build]
    cmds:
      - cargo tauri dev

  build:
    desc: Build production Tauri app
    deps: [pex:build]
    cmds:
      - cargo tauri build

  build-debug:
    desc: Build debug Tauri app
    deps: [pex:build]
    cmds:
      - cargo tauri build --debug
```

**Taskfile.yml** (root):
```yaml
version: '3'

includes:
  tauri: ./taskfiles/tauri.yml
  pex: ./taskfiles/pex.yml

tasks:
  dev:
    desc: Start development environment
    cmds:
      - task: tauri:dev

  build:
    desc: Build production app
    cmds:
      - task: tauri:build
```

## Phase 4: Frontend Development

### 4.1 Application Structure

**src/index.html** - Main application shell
- AlpineJS root component
- Basecoat styling
- WebSocket connection management
- API client setup

**src/components/** - UI components (if splitting)
- Library browser
- Track list
- Player controls
- Playlist manager
- Settings panel

### 4.2 AlpineJS Application State

```javascript
// src/app.js
import Alpine from 'alpinejs';

Alpine.data('musicPlayer', () => ({
    // State
    tracks: [],
    playlists: [],
    currentTrack: null,
    isPlaying: false,
    progress: 0,
    volume: 100,
    backendUrl: '',
    ws: null,
    
    // Lifecycle
    async init() {
        this.backendUrl = await window.__TAURI__.tauri.invoke('get_backend_url');
        await this.connectWebSocket();
        await this.loadLibrary();
    },
    
    // WebSocket management
    async connectWebSocket() {
        const wsUrl = this.backendUrl.replace('http', 'ws') + '/ws';
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealtimeUpdate(data);
        };
        
        this.ws.onerror = () => {
            // Reconnection logic
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    },
    
    // Library operations
    async scanLibrary(path) {
        const response = await fetch(
            `${this.backendUrl}/api/scan/${encodeURIComponent(path)}`
        );
        const data = await response.json();
        this.tracks = data.tracks;
    },
    
    async loadLibrary(query = '') {
        const response = await fetch(
            `${this.backendUrl}/api/tracks?query=${encodeURIComponent(query)}`
        );
        const data = await response.json();
        this.tracks = data.tracks;
    },
    
    // Playback control
    async playTrack(track) {
        const response = await fetch(`${this.backendUrl}/api/playback/play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ track_id: track.id })
        });
        this.currentTrack = track;
        this.isPlaying = true;
    },
    
    togglePlayback() {
        this.ws.send(JSON.stringify({ 
            command: 'toggle_playback' 
        }));
        this.isPlaying = !this.isPlaying;
    },
    
    seek(position) {
        this.ws.send(JSON.stringify({ 
            command: 'seek', 
            position: position 
        }));
    },
    
    setVolume(volume) {
        this.volume = volume;
        this.ws.send(JSON.stringify({ 
            command: 'set_volume', 
            volume: volume 
        }));
    },
    
    // Real-time updates from backend
    handleRealtimeUpdate(data) {
        if (data.event === 'progress') {
            this.progress = data.position;
        } else if (data.event === 'track_ended') {
            this.playNextTrack();
        }
    },
    
    // Playlist operations
    async createPlaylist(name) {
        await fetch(`${this.backendUrl}/api/playlists`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, track_ids: [] })
        });
        await this.loadPlaylists();
    },
    
    async loadPlaylists() {
        const response = await fetch(`${this.backendUrl}/api/playlists`);
        const data = await response.json();
        this.playlists = data.playlists;
    }
}));

Alpine.start();
```

### 4.3 UI Layout with Basecoat

```html
<!-- src/index.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Music Player</title>
    <link rel="stylesheet" href="basecoat.css">
    <style>
        /* Custom styles on top of Basecoat */
        .player-layout {
            display: grid;
            grid-template-columns: 250px 1fr;
            grid-template-rows: 1fr auto;
            height: 100vh;
        }
        
        .sidebar { grid-area: 1 / 1 / 2 / 2; }
        .main-content { grid-area: 1 / 2 / 2 / 3; }
        .player-controls { grid-area: 2 / 1 / 3 / 3; }
    </style>
</head>
<body x-data="musicPlayer()" x-init="init()">
    <div class="player-layout">
        <!-- Sidebar: Playlists and Library -->
        <aside class="sidebar">
            <nav>
                <button @click="scanLibrary('/path/to/music')">
                    Scan Library
                </button>
                
                <h3>Playlists</h3>
                <ul>
                    <template x-for="playlist in playlists" :key="playlist.id">
                        <li @click="loadPlaylist(playlist)" x-text="playlist.name"></li>
                    </template>
                </ul>
            </nav>
        </aside>
        
        <!-- Main: Track List -->
        <main class="main-content">
            <input 
                type="search" 
                placeholder="Search tracks..."
                @input.debounce.500ms="loadLibrary($event.target.value)"
            >
            
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Artist</th>
                        <th>Album</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    <template x-for="track in tracks" :key="track.id">
                        <tr 
                            @dblclick="playTrack(track)"
                            :class="{ 'playing': currentTrack?.id === track.id }"
                        >
                            <td x-text="track.title"></td>
                            <td x-text="track.artist"></td>
                            <td x-text="track.album"></td>
                            <td x-text="formatDuration(track.duration)"></td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </main>
        
        <!-- Player Controls -->
        <footer class="player-controls">
            <div class="now-playing">
                <template x-if="currentTrack">
                    <div>
                        <strong x-text="currentTrack.title"></strong>
                        <span x-text="currentTrack.artist"></span>
                    </div>
                </template>
            </div>
            
            <div class="controls">
                <button @click="playPrevious()">⏮</button>
                <button @click="togglePlayback()" x-text="isPlaying ? '⏸' : '▶'"></button>
                <button @click="playNext()">⏭</button>
            </div>
            
            <div class="progress-bar">
                <input 
                    type="range" 
                    min="0" 
                    max="100" 
                    :value="progress"
                    @input="seek($event.target.value)"
                >
                <span x-text="formatTime(progress)"></span>
                <span x-text="formatTime(currentTrack?.duration || 0)"></span>
            </div>
            
            <div class="volume">
                <input 
                    type="range" 
                    min="0" 
                    max="100" 
                    :value="volume"
                    @input="setVolume($event.target.value)"
                >
            </div>
        </footer>
    </div>
    
    <script type="module" src="app.js"></script>
</body>
</html>
```

## Phase 5: Testing Strategy

### 5.1 Testing with tauri-plugin-devtools

For development and testing, use `tauri-plugin-devtools` which provides inspection and debugging capabilities.

**src-tauri/Cargo.toml** - Devtools as optional feature:
```toml
[dependencies]
tauri = { version = "2", features = ["wry"], default-features = false }
tauri-plugin-shell = "2"
tauri-plugin-devtools = { version = "2", optional = true }

[features]
default = []
devtools = ["tauri-plugin-devtools"]
```

**src-tauri/src/lib.rs** - Conditional initialization:
```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init());
    
    // Only include devtools when feature is enabled
    #[cfg(feature = "devtools")]
    {
        builder = builder.plugin(tauri_plugin_devtools::init());
    }
    
    builder
        .setup(|app| {
            // ... setup code
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            play_track,
            pause,
            resume,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 5.2 Rust Unit Tests

```rust
// src-tauri/src/audio.rs
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_audio_engine_creation() {
        // Note: May fail in CI without audio device
        if std::env::var("CI").is_ok() {
            return;
        }
        let engine = AudioEngine::new();
        assert!(engine.is_ok());
    }
    
    #[test]
    fn test_volume_bounds() {
        // Volume should be clamped to 0.0-1.0
        let engine = AudioEngine::new().unwrap();
        engine.set_volume(1.5); // Should clamp to 1.0
        engine.set_volume(-0.5); // Should clamp to 0.0
    }
}
```

### 5.2 Backend Unit Tests

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_scan_library():
    response = client.get("/api/scan/path/to/music")
    assert response.status_code == 200
    assert "tracks" in response.json()

def test_list_tracks():
    response = client.get("/api/tracks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["tracks"], list)

def test_create_playlist():
    response = client.post(
        "/api/playlists",
        json={"name": "Test", "track_ids": []}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test"

@pytest.mark.asyncio
async def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"command": "ping"})
        data = websocket.receive_json()
        assert data["status"] == "ok"
```

### 5.3 Zig Module Tests

```zig
// zig-module/tests/scanner_test.zig
const std = @import("std");
const scanner = @import("../src/scanner.zig");
const testing = std.testing;

test "scan directory returns files" {
    const allocator = testing.allocator;
    const files = try scanner.scanDirectory(allocator, "/test/path");
    defer files.deinit();
    
    try testing.expect(files.items.len > 0);
}

test "extract metadata from audio file" {
    const allocator = testing.allocator;
    const metadata = try scanner.getMetadata(allocator, "/test/file.mp3");
    defer metadata.deinit();
    
    try testing.expectEqualStrings("Test Title", metadata.title);
}
```

## Phase 6: Build and Packaging

### 6.1 Development Build

```bash
# Single command with Taskfile (recommended)
task dev

# Or manually:
# Terminal 1: Run Python backend directly (for development)
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Run Tauri in dev mode
cargo tauri dev
```

### 6.2 Production Build Process

```bash
# Single command with Taskfile (recommended)
task build

# Or step by step:

# 1. Build Zig module (if using Zig scanner)
cd src
zig build -Doptimize=ReleaseFast
cd ..

# 2. Build PEX SCIE sidecar
task pex:build

# 3. Build Tauri app
cargo tauri build

# Output:
# - macOS: .app bundle and .dmg installer
# - Windows: .exe installer and .msi
# - Linux: .AppImage, .deb, .rpm
```

### 6.3 Cross-Platform Build with Taskfile

**Taskfile.yml** (complete build orchestration):
```yaml
version: '3'

vars:
  PYTHON_VERSION: "3.12"

includes:
  pex: ./taskfiles/pex.yml
  tauri: ./taskfiles/tauri.yml

tasks:
  dev:
    desc: Start development environment
    cmds:
      - task: tauri:dev

  build:
    desc: Build production app for current platform
    cmds:
      - task: pex:build
      - task: tauri:build

  build-all:
    desc: Build for all platforms (requires cross-compilation setup)
    cmds:
      - task: pex:build-macos-arm
      - task: pex:build-macos-intel
      - task: pex:build-linux
      - cargo tauri build --target aarch64-apple-darwin
      - cargo tauri build --target x86_64-apple-darwin
      - cargo tauri build --target x86_64-unknown-linux-gnu

  clean:
    desc: Clean all build artifacts
    cmds:
      - rm -rf src-tauri/bin/*
      - rm -rf src-tauri/target
      - rm -rf dist
      - rm -rf src/.zig-cache

  lint:
    desc: Run all linters
    cmds:
      - cd backend && uv run ruff check --fix
      - cd src-tauri && cargo clippy
      - npm run lint

  test:
    desc: Run all tests
    cmds:
      - cd backend && uv run pytest
      - cd src-tauri && cargo test
```

### 6.4 CI/CD Pipeline Example

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    branches: [main, tauri-migration]
  pull_request:
    branches: [main]

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Rust
        uses: dtolnay/rust-action@stable
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install Task
        uses: arduino/setup-task@v2
      
      - name: Install Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          npm ci
          cd backend && uv sync
      
      - name: Build
        run: task build
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: mt-macos
          path: src-tauri/target/release/bundle/dmg/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf libasound2-dev
      
      - name: Install Rust
        uses: dtolnay/rust-action@stable
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install Task
        uses: arduino/setup-task@v2
      
      - name: Install Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          npm ci
          cd backend && uv sync
      
      - name: Build
        run: task build
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: mt-linux
          path: |
            src-tauri/target/release/bundle/appimage/*.AppImage
            src-tauri/target/release/bundle/deb/*.deb
```

## Phase 7: Migration Strategy

### 7.1 Development Approach

**Hard cut using git worktree** (not parallel development):
```bash
# Create isolated worktree for migration
wt switch --create tauri-migration --base=main

# Work in isolation until feature-complete
# Then merge back to main
wt merge --target=main
```

### 7.2 Migration Phases

**Phase 1: Documentation & Setup** (Week 1)
- [x] Create tauri-migration worktree
- [x] Update architecture documentation
- [ ] Initialize Tauri v2 project structure
- [ ] Set up Taskfile build system

**Phase 2: Rust Audio Engine** (Week 2-3)
- [ ] Implement symphonia-based playback
- [ ] Add rodio/cpal audio output
- [ ] Expose Tauri commands for playback control
- [ ] Test with FLAC, MP3, M4A, OGG, WAV

**Phase 3: Python Backend Service** (Week 3-4)
- [ ] Define REST + WebSocket API contract
- [ ] Port library scanning (keep Zig module)
- [ ] Port metadata extraction (mutagen)
- [ ] Port SQLite database layer
- [ ] Package as PEX SCIE sidecar

**Phase 4: Frontend UI** (Week 5-6)
- [ ] Set up Vite + Tailwind + Basecoat
- [ ] Implement AlpineJS global stores
- [ ] Build library browser component
- [ ] Build player controls bar
- [ ] Build sidebar navigation

**Phase 5: Platform Features** (Week 7-8)
- [ ] macOS global media key support
- [ ] Drag-and-drop file import
- [ ] Keyboard shortcuts
- [ ] System tray integration

**Phase 6: Testing & Polish** (Week 9-10)
- [ ] E2E tests with Tauri WebDriver
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Linux platform support

**Phase 7: Release** (Week 11-12)
- [ ] Windows platform support
- [ ] Auto-update system
- [ ] Code signing
- [ ] Documentation

### 7.3 Feature Parity Checklist

**From tkinter app (must have):**
- [ ] Directory scanning (with Zig module)
- [ ] Metadata extraction (mutagen)
- [ ] Track listing and search
- [ ] Queue management with drag-and-drop reorder
- [ ] Playback control (play/pause/stop/next/prev)
- [ ] Seek/progress bar
- [ ] Volume control
- [ ] Loop and shuffle modes
- [ ] Keyboard shortcuts
- [ ] Settings persistence
- [ ] Favorites view

**New capabilities:**
- [ ] Modern, responsive UI (Basecoat + Tailwind)
- [ ] Rust-native audio playback (no VLC dependency)
- [ ] E2E testing with Tauri WebDriver
- [ ] Better error handling and logging
- [ ] Real-time progress updates via WebSocket
- [ ] System tray integration
- [ ] Cross-platform installers (.dmg, .AppImage, .deb, .exe)
- [ ] Auto-updates

**Deferred (post-1.0):**
- [ ] Network share support (UNC paths)
- [ ] Playlist creation/management
- [ ] Album art display
- [ ] Lyrics integration

## Key Architectural Decisions

### Why Rust Audio (symphonia) instead of VLC?
- **No external dependencies**: VLC requires system installation, symphonia is pure Rust
- **Better packaging**: No need to bundle VLC libraries or handle platform-specific paths
- **Cross-platform**: Works identically on macOS, Linux, Windows without special handling
- **Format support**: FLAC, MP3, M4A/AAC, OGG, WAV - covers 99% of music libraries
- **Performance**: Native Rust performance, lower latency than Python bindings
- **No musl issues**: VLC doesn't work well with Alpine/musl libc; symphonia has no such limitations

### Why PEX SCIE?
- **Self-contained**: Includes Python interpreter - no system Python required
- **Fast builds**: 4x faster than PyInstaller
- **Small binaries**: 16% smaller than PyInstaller
- **Hermetic**: Reproducible builds with pinned dependencies
- **Single file**: Easy to bundle with Tauri as sidecar

### Why AlpineJS?
- Lightweight (15KB)
- Simple reactivity model
- No build step required (but works great with Vite)
- Perfect for music player interactions
- Easy to learn for Python developers

### Why Basecoat + Tailwind?
- Modern, professional styling
- Consistent across platforms
- Utility-first approach matches AlpineJS philosophy
- Good accessibility defaults
- Easy theming with CSS variables

### Why FastAPI for Sidecar?
- Async/await support for WebSocket
- Automatic API documentation (useful during development)
- Type hints and validation with Pydantic
- Fast performance
- Familiar to Python developers

### Why Taskfile?
- Simpler than Make for cross-platform builds
- YAML syntax is readable and maintainable
- Built-in task dependencies
- Works on Windows, macOS, Linux without modification
- Easy to integrate with CI/CD

## Network Shares Considerations

For Windows UNC paths (`\\server\share`) and mounted network drives:

**Backend handling:**
```python
# backend/services/scanner.py
import os
import sys

def normalize_path(path: str) -> str:
    """Handle UNC paths and network shares"""
    if sys.platform == 'win32':
        # Convert forward slashes
        path = path.replace('/', '\\')
        # Handle UNC paths
        if path.startswith('\\\\'):
            return path
    return os.path.abspath(os.path.expanduser(path))
```

**Test with:**
- Windows UNC: `\\192.168.1.100\music`
- macOS/Linux mount: `/mnt/network-share`
- Samba shares
- NFS mounts

## Performance Optimization

### Zig Module Benefits
- Fast directory traversal
- Efficient metadata extraction
- Minimal memory overhead
- Parallel processing capability

### Caching Strategy
```python
# backend/services/cache.py
import sqlite3
from pathlib import Path

class MetadataCache:
    """Cache metadata to avoid re-scanning"""
    
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def get_cached_metadata(self, file_path: str, mtime: float):
        """Get cached metadata if file hasn't changed"""
        cursor = self.conn.execute(
            "SELECT metadata FROM cache WHERE path = ? AND mtime = ?",
            (file_path, mtime)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    
    def cache_metadata(self, file_path: str, mtime: float, metadata: dict):
        """Store metadata in cache"""
        self.conn.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
            (file_path, mtime, json.dumps(metadata))
        )
        self.conn.commit()
```

## Deployment Considerations

### Auto-Updates
Tauri supports built-in update mechanism:
```json
// tauri.conf.json
{
  "updater": {
    "active": true,
    "endpoints": [
      "https://releases.example.com/{{target}}/{{current_version}}"
    ],
    "dialog": true,
    "pubkey": "YOUR_PUBLIC_KEY"
  }
}
```

### System Tray
```rust
// src-tauri/src/main.rs
use tauri::SystemTrayMenu;

fn create_system_tray() -> SystemTray {
    let tray_menu = SystemTrayMenu::new()
        .add_item(CustomMenuItem::new("show", "Show"))
        .add_item(CustomMenuItem::new("play_pause", "Play/Pause"))
        .add_item(CustomMenuItem::new("quit", "Quit"));
    
    SystemTray::new().with_menu(tray_menu)
}
```

## Success Metrics

### Performance Targets
- Scan 10,000 tracks in <5 seconds (Zig module)
- UI response time <100ms for all interactions
- WebSocket latency <50ms for playback updates
- Memory usage <200MB for typical library (5000 tracks)
- App startup time <2 seconds (including sidecar)
- Audio playback latency <50ms (symphonia + rodio)

### Quality Targets
- Unit test coverage for core logic (Rust + Python)
- Zero crashes in 1-hour stress test
- Support for major audio formats: FLAC, MP3, M4A/AAC, OGG, WAV
- Clean LSP diagnostics (no warnings)
- Clippy clean (Rust linting)

### Build Targets
- PEX SCIE build time <30 seconds
- Final app bundle size <100MB (including Python runtime)
- Reproducible builds (same input → same output)

## Next Steps

See backlog tasks under "Tauri Migration" milestone for detailed tracking:

1. **Phase 1: Documentation** (task-090 through task-092)
   - Create worktree
   - Update architecture docs
   - Add migration section

2. **Phase 2: Rust Audio** (task-093 through task-095)
   - Initialize Tauri project
   - Implement symphonia playback
   - Expose Tauri commands

3. **Phase 3: Python Backend** (task-096 through task-099)
   - Define API contract
   - Create FastAPI service
   - Package as PEX SCIE
   - Implement sidecar management

4. **Phase 4: Frontend** (task-100 through task-104)
   - Set up build tooling
   - Implement Alpine stores
   - Build UI components

5. **Phase 5: Platform Features** (task-105 through task-109)
   - Media keys
   - Drag-and-drop
   - Keyboard shortcuts
   - Linux/Windows support

## References

- [Tauri v2 Documentation](https://v2.tauri.app/)
- [symphonia - Rust audio decoding](https://github.com/pdeljanov/Symphonia)
- [rodio - Rust audio playback](https://github.com/RustAudio/rodio)
- [PEX Documentation](https://docs.pex-tool.org/)
- [AlpineJS Documentation](https://alpinejs.dev/)
- [Basecoat Components](https://basecoat.dev/)
