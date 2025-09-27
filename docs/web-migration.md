# Web Migration Guide

## Overview

This document outlines the strategy and considerations for porting MT music player from its current Tkinter desktop application to a web-based application using FastAPI or Flask. The migration aims to preserve core functionality while leveraging web technologies for enhanced accessibility and deployment flexibility.

## Architecture Transformation

### Current Desktop Architecture

```
Tkinter GUI → Python Core → VLC Player → SQLite DB
     ↓             ↓            ↓           ↓
User Input → Business Logic → Audio Output → Data Storage
```

### Target Web Architecture

```
React/Vue Frontend → FastAPI Backend → Database → Audio Service
      ↓                    ↓              ↓           ↓
   Browser Client → REST API Endpoints → PostgreSQL → Web Audio API
```

## Backend Migration Strategy

### Framework Selection: FastAPI vs Flask

#### FastAPI Advantages (Recommended)

- **Automatic API Documentation**: Built-in OpenAPI/Swagger integration
- **Type Safety**: Full Python type hint support with validation
- **Performance**: ASGI-based asynchronous request handling
- **Modern Standards**: Native async/await support throughout
- **Dependency Injection**: Clean dependency management system
- **WebSocket Support**: Real-time updates for playback status

#### FastAPI Implementation Structure

```python
# Core FastAPI application structure
from fastapi import FastAPI, WebSocket, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(title="MT Music Player API", version="2.0.0")

# API route structure
@app.get("/api/library/tracks")
async def get_tracks(db: AsyncSession = Depends(get_db)):
    return await track_service.get_all_tracks(db)

@app.post("/api/player/play/{track_id}")
async def play_track(track_id: int, player: PlayerService = Depends()):
    return await player.play_track(track_id)

@app.websocket("/ws/player-status")
async def player_status_websocket(websocket: WebSocket):
    await websocket.accept()
    # Real-time player status updates
```

### Data Layer Migration

#### Database Migration: SQLite → PostgreSQL

**Current SQLite Schema**:
```sql
-- Library table
CREATE TABLE library (
    id INTEGER PRIMARY KEY,
    filepath TEXT UNIQUE,
    title TEXT,
    artist TEXT,
    album TEXT,
    year INTEGER,
    duration INTEGER,
    file_hash TEXT UNIQUE
);

-- Queue table  
CREATE TABLE queue (
    id INTEGER PRIMARY KEY,
    track_id INTEGER REFERENCES library(id),
    position INTEGER,
    created_at TIMESTAMP
);
```

**PostgreSQL Schema Enhancement**:
```sql
-- Enhanced library table with web-specific fields
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    filepath TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    year INTEGER,
    duration_ms INTEGER,
    file_hash TEXT UNIQUE,
    file_size BIGINT,
    bitrate INTEGER,
    format TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    play_count INTEGER DEFAULT 0,
    last_played_at TIMESTAMPTZ
);

-- User management for multi-user support
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User-specific playlists
CREATE TABLE playlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Current playback queue per user
CREATE TABLE user_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    track_id INTEGER REFERENCES tracks(id),
    position INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, position)
);
```

#### Database Service Layer

```python
# Database service abstraction
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy import select

class TrackService:
    async def get_all_tracks(self, db: AsyncSession, user_id: int = None):
        """Get all tracks with optional user-specific filtering."""
        query = select(Track).options(selectinload(Track.playlists))
        if user_id:
            # Add user-specific filtering logic
            pass
        result = await db.execute(query)
        return result.scalars().all()
    
    async def search_tracks(self, db: AsyncSession, query: str):
        """Full-text search across track metadata."""
        search_query = select(Track).where(
            Track.title.ilike(f"%{query}%") |
            Track.artist.ilike(f"%{query}%") |
            Track.album.ilike(f"%{query}%")
        )
        result = await db.execute(search_query)
        return result.scalars().all()
```

### Business Logic Migration

#### Core Service Components

**Player Service**:
```python
class PlayerService:
    def __init__(self):
        self.current_track_id: Optional[int] = None
        self.is_playing: bool = False
        self.current_position_ms: int = 0
        self.volume: int = 80
        
    async def play_track(self, track_id: int, user_id: int):
        """Start playback of specified track."""
        track = await self.track_service.get_track(track_id)
        if not track:
            raise HTTPException(404, "Track not found")
            
        self.current_track_id = track_id
        self.is_playing = True
        self.current_position_ms = 0
        
        # Notify WebSocket clients of state change
        await self.broadcast_status_update()
        
        # Log play event for analytics
        await self.analytics_service.log_play_event(user_id, track_id)
        
        return {"status": "playing", "track_id": track_id}
```

**Queue Service**:
```python
class QueueService:
    async def get_user_queue(self, db: AsyncSession, user_id: int):
        """Get current user queue in order."""
        query = (
            select(UserQueue)
            .options(selectinload(UserQueue.track))
            .where(UserQueue.user_id == user_id)
            .order_by(UserQueue.position)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def add_to_queue(self, db: AsyncSession, user_id: int, track_id: int):
        """Add track to end of user queue."""
        max_position = await self.get_max_queue_position(db, user_id)
        new_queue_item = UserQueue(
            user_id=user_id,
            track_id=track_id,
            position=max_position + 1
        )
        db.add(new_queue_item)
        await db.commit()
        return new_queue_item
```

### Audio Playback Migration

#### Current VLC Integration → Web Audio

**Challenge**: VLC cannot run in browsers; web audio requires different approach

**Solution Options**:

1. **Server-Side Audio Streaming** (Recommended)

```python
from fastapi.responses import StreamingResponse
import aiofiles

@app.get("/api/audio/stream/{track_id}")
async def stream_audio(track_id: int, range: Optional[str] = Header(None)):
    """Stream audio file with range request support."""
    track = await track_service.get_track(track_id)
    
    async with aiofiles.open(track.filepath, 'rb') as audio_file:
        if range:
            # Handle HTTP range requests for seeking
            start, end = parse_range_header(range)
            await audio_file.seek(start)
            chunk_size = end - start + 1
            audio_data = await audio_file.read(chunk_size)
        else:
            audio_data = await audio_file.read()
    
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(audio_data)),
            "Cache-Control": "public, max-age=3600"
        }
    )
```

2. **Client-Side Web Audio API**

```javascript
// Frontend audio player implementation
class WebAudioPlayer {
    constructor() {
        this.audio = new Audio();
        this.isPlaying = false;
        this.currentTrackId = null;
        
        this.audio.addEventListener('ended', () => {
            this.onTrackEnded();
        });
        
        this.audio.addEventListener('timeupdate', () => {
            this.onTimeUpdate(this.audio.currentTime);
        });
    }
    
    async playTrack(trackId) {
        this.audio.src = `/api/audio/stream/${trackId}`;
        await this.audio.play();
        this.isPlaying = true;
        this.currentTrackId = trackId;
        
        // Notify server of play event
        await fetch('/api/player/play', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({track_id: trackId})
        });
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
    }
    
    seek(timeSeconds) {
        this.audio.currentTime = timeSeconds;
    }
    
    setVolume(volume) {
        this.audio.volume = volume / 100;
    }
}
```

## Frontend Migration Strategy

### Framework Selection: React vs Vue

#### React Implementation (Recommended)

**Component Architecture**:
```javascript
// Main application component structure
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';

function App() {
    return (
        <Provider store={store}>
            <Router>
                <div className="app">
                    <Header />
                    <div className="main-content">
                        <Routes>
                            <Route path="/library" element={<LibraryView />} />
                            <Route path="/queue" element={<QueueView />} />
                            <Route path="/playlists" element={<PlaylistView />} />
                            <Route path="/search" element={<SearchView />} />
                        </Routes>
                    </div>
                    <PlayerControls />
                </div>
            </Router>
        </Provider>
    );
}
```

**State Management with Redux Toolkit**:
```javascript
// Player state slice
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const playTrack = createAsyncThunk(
    'player/playTrack',
    async (trackId) => {
        const response = await fetch(`/api/player/play/${trackId}`, {
            method: 'POST'
        });
        return response.json();
    }
);

const playerSlice = createSlice({
    name: 'player',
    initialState: {
        currentTrackId: null,
        isPlaying: false,
        currentTime: 0,
        duration: 0,
        volume: 80,
        queue: [],
        isLoading: false
    },
    reducers: {
        setCurrentTime: (state, action) => {
            state.currentTime = action.payload;
        },
        setVolume: (state, action) => {
            state.volume = action.payload;
        }
    },
    extraReducers: (builder) => {
        builder
            .addCase(playTrack.pending, (state) => {
                state.isLoading = true;
            })
            .addCase(playTrack.fulfilled, (state, action) => {
                state.currentTrackId = action.payload.track_id;
                state.isPlaying = true;
                state.isLoading = false;
            });
    }
});
```

**Component Migration Examples**:

1. **Library View Component**:

```javascript
import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchTracks, searchTracks } from '../store/librarySlice';

function LibraryView() {
    const dispatch = useDispatch();
    const { tracks, loading, searchQuery } = useSelector(state => state.library);
    const [selectedSection, setSelectedSection] = useState('all');
    
    useEffect(() => {
        dispatch(fetchTracks());
    }, [dispatch]);
    
    const handleSectionSelect = (section) => {
        setSelectedSection(section);
        // Filter tracks based on section
    };
    
    return (
        <div className="library-view">
            <div className="library-sidebar">
                <LibrarySidebar 
                    selectedSection={selectedSection}
                    onSectionSelect={handleSectionSelect}
                />
            </div>
            <div className="track-list">
                <TrackList tracks={filteredTracks} />
            </div>
        </div>
    );
}
```

2. **Queue View Component**:

```javascript
import React from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';

function QueueView() {
    const { queue } = useSelector(state => state.player);
    const dispatch = useDispatch();
    
    const moveTrack = (dragIndex, hoverIndex) => {
        dispatch(reorderQueue({ dragIndex, hoverIndex }));
    };
    
    return (
        <DndProvider backend={HTML5Backend}>
            <div className="queue-view">
                <div className="queue-header">
                    <h2>Current Queue ({queue.length} tracks)</h2>
                </div>
                <div className="queue-tracks">
                    {queue.map((track, index) => (
                        <DraggableTrackItem
                            key={track.id}
                            track={track}
                            index={index}
                            moveTrack={moveTrack}
                        />
                    ))}
                </div>
            </div>
        </DndProvider>
    );
}
```

### Real-Time Communication

**WebSocket Integration**:
```javascript
// WebSocket service for real-time updates
class WebSocketService {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 5000;
    }
    
    connect(dispatch) {
        this.ws = new WebSocket('ws://localhost:8000/ws/player-status');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            dispatch(updatePlayerStatus(data));
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, attempting reconnection...');
            setTimeout(() => this.connect(dispatch), this.reconnectInterval);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    sendCommand(command, payload = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ command, ...payload }));
        }
    }
}
```

## Feature Parity Analysis

### Direct Migrations

#### Core Features (1:1 Migration)

- **Track Library**: Database-driven with search and filtering
- **Queue Management**: Drag-and-drop reordering with persistence
- **Playback Controls**: Play, pause, next, previous, seek, volume
- **Playlist Management**: User-created playlists with CRUD operations
- **Settings**: User preferences with database storage

#### Enhanced Web Features

- **Multi-User Support**: User authentication and separate libraries
- **Real-Time Sync**: Multiple device synchronization via WebSockets
- **Social Features**: Playlist sharing, collaborative playlists
- **Analytics**: Detailed listening statistics and recommendations
- **Cloud Storage**: Integration with cloud music services

### Web-Specific Challenges

#### Browser Limitations

- **File System Access**: Limited local file system integration
- **Audio Format Support**: Browser codec dependencies
- **Performance**: JavaScript vs native performance for large libraries
- **Storage**: Browser storage limits vs unlimited desktop storage

#### Solutions and Workarounds

1. **File Upload Interface**:

```javascript
// Replace drag-and-drop directory scanning with file upload
function FileUploader() {
    const handleFileUpload = async (files) => {
        const formData = new FormData();
        Array.from(files).forEach(file => {
            if (file.type.startsWith('audio/')) {
                formData.append('files', file);
            }
        });
        
        await fetch('/api/library/upload', {
            method: 'POST',
            body: formData
        });
    };
    
    return (
        <input 
            type="file" 
            multiple 
            accept="audio/*"
            onChange={(e) => handleFileUpload(e.target.files)}
        />
    );
}
```

2. **Progressive Loading**:

```javascript
// Handle large libraries with pagination and virtual scrolling
import { FixedSizeList as VirtualList } from 'react-window';

function VirtualizedTrackList({ tracks }) {
    const Row = ({ index, style }) => (
        <div style={style}>
            <TrackItem track={tracks[index]} />
        </div>
    );
    
    return (
        <VirtualList
            height={600}
            itemCount={tracks.length}
            itemSize={50}
            width="100%"
        >
            {Row}
        </VirtualList>
    );
}
```

## Deployment Strategy

### Development Environment

```yaml
# docker-compose.yml for development
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mt_music
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./music_files:/app/music_files
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: mt_music
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Production Deployment

**Infrastructure Options**:

1. **Self-Hosted**:
   - **Backend**: FastAPI with Gunicorn/Uvicorn
   - **Database**: PostgreSQL with regular backups
   - **File Storage**: Local storage with backup strategy
   - **Reverse Proxy**: Nginx for static files and SSL termination

2. **Cloud Deployment**:
   - **Backend**: Heroku, Railway, or DigitalOcean App Platform
   - **Database**: Heroku Postgres, AWS RDS, or DigitalOcean Managed Database
   - **File Storage**: AWS S3, DigitalOcean Spaces, or similar
   - **CDN**: CloudFlare for global content delivery

3. **Containerized**:
   - **Orchestration**: Docker Swarm or Kubernetes
   - **Load Balancing**: Built-in container orchestration
   - **Scalability**: Horizontal scaling for multiple instances

## Migration Timeline

### Phase 1: Backend Foundation (4-6 weeks)

1. **FastAPI Setup**: Basic application structure and routing
2. **Database Migration**: PostgreSQL schema and data migration tools
3. **Authentication**: User management and JWT-based authentication
4. **Core API Endpoints**: Library, queue, and player control APIs
5. **Audio Streaming**: Basic audio file serving with range support

### Phase 2: Frontend Development (6-8 weeks)

1. **React Application Setup**: Component architecture and routing
2. **State Management**: Redux store configuration
3. **Core Components**: Library view, queue view, player controls
4. **WebSocket Integration**: Real-time status updates
5. **Responsive Design**: Mobile and desktop layouts

### Phase 3: Feature Parity (4-6 weeks)

1. **Search Implementation**: Full-text search across library
2. **Playlist Management**: User playlist creation and management
3. **Queue Operations**: Drag-and-drop reordering and queue management
4. **Settings and Preferences**: User configuration management
5. **Theme System**: CSS-based theming similar to current JSON themes

### Phase 4: Testing and Polish (2-4 weeks)

1. **End-to-End Testing**: Full application workflow testing
2. **Performance Optimization**: Large library handling and optimization
3. **Bug Fixes**: Issue resolution and stability improvements
4. **Documentation**: API documentation and user guides
5. **Deployment**: Production deployment and monitoring setup

### Phase 5: Enhanced Features (Ongoing)

1. **Multi-User Features**: User management and sharing capabilities
2. **Social Integration**: Last.fm integration and social features
3. **Analytics**: Advanced listening statistics and recommendations
4. **Mobile App**: React Native or PWA for mobile access
5. **Integration APIs**: Third-party service integrations

## Risk Assessment and Mitigation

### Technical Risks

1. **Performance with Large Libraries**:
   - **Risk**: Web application slower than native desktop
   - **Mitigation**: Virtual scrolling, pagination, database indexing, caching

2. **Audio Format Compatibility**:
   - **Risk**: Browser codec limitations affecting playback
   - **Mitigation**: Server-side transcoding, format detection, fallback formats

3. **File Storage Scalability**:
   - **Risk**: Large music collections exceeding server storage
   - **Mitigation**: Cloud storage integration, compression, streaming protocols

### User Experience Risks

1. **Feature Loss During Migration**:
   - **Risk**: Missing desktop-specific features in web version
   - **Mitigation**: Feature parity checklist, user feedback integration, gradual migration

2. **Performance Expectations**:
   - **Risk**: Users expecting desktop-level performance from web app
   - **Mitigation**: Performance benchmarking, optimization focus, user education

3. **Data Migration**:
   - **Risk**: Loss of user libraries and preferences during migration
   - **Mitigation**: Comprehensive migration tools, backup procedures, rollback capability

## Success Metrics

### Technical Metrics

- **API Response Time**: < 200ms for typical requests
- **Page Load Time**: < 2 seconds for library views
- **Audio Streaming Latency**: < 1 second startup time
- **Concurrent Users**: Support for 100+ concurrent users per server

### User Experience Metrics

- **Feature Parity**: 100% of core desktop features available in web version
- **Mobile Responsiveness**: Full functionality on mobile devices
- **Browser Compatibility**: Support for Chrome, Firefox, Safari, Edge
- **Accessibility**: WCAG 2.1 AA compliance for screen readers and keyboard navigation

This migration guide provides a comprehensive roadmap for transforming MT music player from a desktop Tkinter application to a modern web application while maintaining feature parity and enhancing the user experience for the web platform.
