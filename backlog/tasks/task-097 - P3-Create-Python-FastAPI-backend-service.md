---
id: task-097
title: 'P3: Create Python FastAPI backend service'
status: To Do
assignee: []
created_date: '2026-01-12 04:07'
labels:
  - python
  - backend
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-096
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port the existing Python business logic to a FastAPI service that can run as a Tauri sidecar.

**Structure:**
```
backend/
├── main.py              # FastAPI app entry
├── routes/
│   ├── library.py       # Library endpoints
│   ├── queue.py         # Queue endpoints
│   ├── playlists.py     # Playlist endpoints
│   ├── favorites.py     # Favorites endpoints
│   └── settings.py      # Settings endpoints
├── services/
│   ├── library.py       # LibraryManager (from core/library.py)
│   ├── queue.py         # QueueManager (from core/queue.py)
│   ├── database.py      # MusicDatabase (from core/db/)
│   ├── metadata.py      # Metadata extraction
│   └── lyrics.py        # LyricsManager (from core/lyrics.py)
├── models/              # Pydantic models
└── requirements.txt
```

**Key changes from Tkinter version:**
- Remove all Tk dependencies
- Replace `window.after()` patterns with async/await
- Add CORS middleware for Tauri webview
- Add WebSocket endpoint for real-time events
- Use same SQLite DB schema (compatible migration)

**Entry point for PEX:**
```python
def run():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 FastAPI app runs standalone with uvicorn
- [ ] #2 All REST endpoints from contract implemented
- [ ] #3 WebSocket endpoint emits events
- [ ] #4 Uses same SQLite schema as Tkinter version
- [ ] #5 No tkinter imports anywhere in backend/
- [ ] #6 CORS configured for tauri://localhost
<!-- AC:END -->
