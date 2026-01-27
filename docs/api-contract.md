# REST API Contract

This document defines the REST API contract for the mt music player's FastAPI backend sidecar. The Tauri frontend communicates with this backend for all database operations (library, queue, playlists, favorites, settings).

## Overview

- **Base URL**: `http://localhost:8765/api`
- **Protocol**: HTTP/1.1 + WebSocket
- **Content-Type**: `application/json`
- **Authentication**: None (localhost only)

## Data Models

### Track

```typescript
interface Track {
  id: number;
  filepath: string;
  title: string | null;
  artist: string | null;
  album: string | null;
  album_artist: string | null;
  track_number: string | null;
  track_total: string | null;
  date: string | null;
  duration: number | null;      // seconds
  play_count: number;
  last_played: string | null;   // ISO 8601 datetime
  added_date: string;           // ISO 8601 datetime
}
```

### QueueItem

```typescript
interface QueueItem {
  position: number;             // 0-indexed position in queue
  track: Track;
}
```

### Playlist

```typescript
interface Playlist {
  id: number;
  name: string;
  description: string | null;
  created_date: string;         // ISO 8601 datetime
  modified_date: string;        // ISO 8601 datetime
  track_count: number;
}
```

### PlaylistTrack

```typescript
interface PlaylistTrack {
  position: number;             // 0-indexed position in playlist
  track: Track;
  added_date: string;           // ISO 8601 datetime
}
```

### LibraryStats

```typescript
interface LibraryStats {
  total_tracks: number;
  total_duration: number;       // seconds
  total_artists: number;
  total_albums: number;
}
```

### Error Response

```typescript
interface ErrorResponse {
  error: string;
  detail: string | null;
}
```

---

## Library Endpoints

### GET /api/library

Get all tracks in the library with optional filtering and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | - | Search term (matches title, artist, album) |
| `artist` | string | - | Filter by artist name |
| `album` | string | - | Filter by album name |
| `sort_by` | string | `added_date` | Sort field: `title`, `artist`, `album`, `added_date`, `play_count` |
| `sort_order` | string | `desc` | Sort order: `asc`, `desc` |
| `limit` | integer | 100 | Max tracks to return (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Response:** `200 OK`
```json
{
  "tracks": [
    {
      "id": 1,
      "filepath": "/path/to/song.flac",
      "title": "Strobe",
      "artist": "deadmau5",
      "album": "For Lack of a Better Name",
      "album_artist": "deadmau5",
      "track_number": "9",
      "track_total": "12",
      "date": "2009",
      "duration": 637.5,
      "play_count": 42,
      "last_played": "2025-01-13T10:30:00Z",
      "added_date": "2024-06-15T14:22:00Z"
    }
  ],
  "total": 1500,
  "limit": 100,
  "offset": 0
}
```

### GET /api/library/{track_id}

Get a single track by ID.

**Response:** `200 OK`
```json
{
  "id": 1,
  "filepath": "/path/to/song.flac",
  "title": "Strobe",
  "artist": "deadmau5",
  "album": "For Lack of a Better Name",
  "album_artist": "deadmau5",
  "track_number": "9",
  "track_total": "12",
  "date": "2009",
  "duration": 637.5,
  "play_count": 42,
  "last_played": "2025-01-13T10:30:00Z",
  "added_date": "2024-06-15T14:22:00Z"
}
```

**Error:** `404 Not Found`
```json
{
  "error": "not_found",
  "detail": "Track with id 999 not found"
}
```

### GET /api/library/stats

Get library statistics.

**Response:** `200 OK`
```json
{
  "total_tracks": 1500,
  "total_duration": 432000,
  "total_artists": 245,
  "total_albums": 312
}
```

### POST /api/library/scan

Scan a directory for music files and add to library.

**Request Body:**
```json
{
  "path": "/path/to/music",
  "recursive": true
}
```

**Response:** `202 Accepted`
```json
{
  "status": "scanning",
  "job_id": "scan_abc123"
}
```

The scan runs asynchronously. Progress is reported via WebSocket events.

### DELETE /api/library/{track_id}

Remove a track from the library.

**Response:** `204 No Content`

**Error:** `404 Not Found`
```json
{
  "error": "not_found",
  "detail": "Track with id 999 not found"
}
```

### PUT /api/library/{track_id}/play-count

Increment play count for a track.

**Response:** `200 OK`
```json
{
  "id": 1,
  "play_count": 43,
  "last_played": "2025-01-13T23:15:00Z"
}
```

---

## Queue Endpoints

### GET /api/queue

Get the current playback queue.

**Response:** `200 OK`
```json
{
  "items": [
    {
      "position": 0,
      "track": {
        "id": 1,
        "filepath": "/path/to/song.flac",
        "title": "Strobe",
        "artist": "deadmau5",
        "album": "For Lack of a Better Name",
        "duration": 637.5
      }
    },
    {
      "position": 1,
      "track": {
        "id": 2,
        "filepath": "/path/to/another.mp3",
        "title": "Ghosts n Stuff",
        "artist": "deadmau5",
        "album": "For Lack of a Better Name",
        "duration": 360.2
      }
    }
  ],
  "count": 2
}
```

### POST /api/queue/add

Add track(s) to the queue.

**Request Body:**
```json
{
  "track_ids": [1, 2, 3],
  "position": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `track_ids` | number[] | Yes | Track IDs to add |
| `position` | number \| null | No | Insert position (null = end of queue) |

**Response:** `201 Created`
```json
{
  "added": 3,
  "queue_length": 5
}
```

### POST /api/queue/add-files

Add files directly to the queue (for drag-and-drop).

**Request Body:**
```json
{
  "filepaths": ["/path/to/song1.flac", "/path/to/song2.mp3"],
  "position": null
}
```

**Response:** `201 Created`
```json
{
  "added": 2,
  "queue_length": 4,
  "tracks": [
    {"id": 15, "title": "New Song 1", "artist": "Artist"},
    {"id": 16, "title": "New Song 2", "artist": "Artist"}
  ]
}
```

### DELETE /api/queue/{position}

Remove a track from the queue by position.

**Response:** `204 No Content`

**Error:** `404 Not Found`
```json
{
  "error": "not_found",
  "detail": "No track at position 99"
}
```

### POST /api/queue/clear

Clear the entire queue.

**Response:** `204 No Content`

### POST /api/queue/reorder

Reorder tracks in the queue.

**Request Body:**
```json
{
  "from_position": 3,
  "to_position": 0
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "queue_length": 5
}
```

### POST /api/queue/shuffle

Shuffle the queue (optionally keeping current track at position 0).

**Request Body:**
```json
{
  "keep_current": true
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "queue_length": 5
}
```

---

## Playlists Endpoints

### GET /api/playlists

Get all playlists.

**Response:** `200 OK`
```json
{
  "playlists": [
    {
      "id": 1,
      "name": "Chill Vibes",
      "description": "Relaxing electronic music",
      "created_date": "2024-06-15T14:22:00Z",
      "modified_date": "2025-01-10T08:30:00Z",
      "track_count": 45
    },
    {
      "id": 2,
      "name": "Workout Mix",
      "description": null,
      "created_date": "2024-08-20T10:00:00Z",
      "modified_date": "2024-12-01T16:45:00Z",
      "track_count": 32
    }
  ]
}
```

### POST /api/playlists

Create a new playlist.

**Request Body:**
```json
{
  "name": "New Playlist",
  "description": "Optional description"
}
```

**Response:** `201 Created`
```json
{
  "id": 3,
  "name": "New Playlist",
  "description": "Optional description",
  "created_date": "2025-01-13T23:20:00Z",
  "modified_date": "2025-01-13T23:20:00Z",
  "track_count": 0
}
```

**Error:** `409 Conflict`
```json
{
  "error": "conflict",
  "detail": "Playlist with name 'New Playlist' already exists"
}
```

### GET /api/playlists/{playlist_id}

Get a playlist with its tracks.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Chill Vibes",
  "description": "Relaxing electronic music",
  "created_date": "2024-06-15T14:22:00Z",
  "modified_date": "2025-01-10T08:30:00Z",
  "track_count": 45,
  "tracks": [
    {
      "position": 0,
      "track": {
        "id": 1,
        "filepath": "/path/to/song.flac",
        "title": "Strobe",
        "artist": "deadmau5",
        "album": "For Lack of a Better Name",
        "duration": 637.5
      },
      "added_date": "2024-06-15T14:25:00Z"
    }
  ]
}
```

### PUT /api/playlists/{playlist_id}

Update playlist metadata.

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Updated Name",
  "description": "Updated description",
  "created_date": "2024-06-15T14:22:00Z",
  "modified_date": "2025-01-13T23:25:00Z",
  "track_count": 45
}
```

### DELETE /api/playlists/{playlist_id}

Delete a playlist.

**Response:** `204 No Content`

### POST /api/playlists/{playlist_id}/tracks

Add tracks to a playlist.

**Request Body:**
```json
{
  "track_ids": [1, 2, 3],
  "position": null
}
```

**Response:** `201 Created`
```json
{
  "added": 3,
  "playlist_track_count": 48
}
```

### DELETE /api/playlists/{playlist_id}/tracks/{position}

Remove a track from a playlist by position.

**Response:** `204 No Content`

### POST /api/playlists/{playlist_id}/tracks/reorder

Reorder tracks within a playlist.

**Request Body:**
```json
{
  "from_position": 5,
  "to_position": 0
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "playlist_track_count": 45
}
```

---

## Favorites Endpoints

### GET /api/favorites

Get all favorited tracks (Liked Songs).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Max tracks to return |
| `offset` | integer | 0 | Pagination offset |

**Response:** `200 OK`
```json
{
  "tracks": [
    {
      "id": 1,
      "filepath": "/path/to/song.flac",
      "title": "Strobe",
      "artist": "deadmau5",
      "album": "For Lack of a Better Name",
      "duration": 637.5,
      "favorited_date": "2024-12-25T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

### GET /api/favorites/top25

Get top 25 most played tracks.

**Response:** `200 OK`
```json
{
  "tracks": [
    {
      "id": 1,
      "filepath": "/path/to/song.flac",
      "title": "Strobe",
      "artist": "deadmau5",
      "album": "For Lack of a Better Name",
      "duration": 637.5,
      "play_count": 142
    }
  ]
}
```

### GET /api/favorites/{track_id}

Check if a track is favorited.

**Response:** `200 OK`
```json
{
  "is_favorite": true,
  "favorited_date": "2024-12-25T10:00:00Z"
}
```

### POST /api/favorites/{track_id}

Add a track to favorites.

**Response:** `201 Created`
```json
{
  "success": true,
  "favorited_date": "2025-01-13T23:30:00Z"
}
```

**Error:** `409 Conflict`
```json
{
  "error": "conflict",
  "detail": "Track is already favorited"
}
```

### DELETE /api/favorites/{track_id}

Remove a track from favorites.

**Response:** `204 No Content`

---

## Settings Endpoints

### GET /api/settings

Get all user settings.

**Response:** `200 OK`
```json
{
  "settings": {
    "volume": 75,
    "shuffle": false,
    "loop_mode": "none",
    "library_paths": ["/Users/lance/Music"],
    "theme": "dark",
    "sidebar_width": 250,
    "queue_panel_height": 300
  }
}
```

### GET /api/settings/{key}

Get a specific setting.

**Response:** `200 OK`
```json
{
  "key": "volume",
  "value": 75
}
```

**Error:** `404 Not Found`
```json
{
  "error": "not_found",
  "detail": "Setting 'unknown_key' not found"
}
```

### PUT /api/settings/{key}

Update a setting.

**Request Body:**
```json
{
  "value": 80
}
```

**Response:** `200 OK`
```json
{
  "key": "volume",
  "value": 80
}
```

### PUT /api/settings

Bulk update settings.

**Request Body:**
```json
{
  "volume": 80,
  "shuffle": true,
  "loop_mode": "one"
}
```

**Response:** `200 OK`
```json
{
  "updated": ["volume", "shuffle", "loop_mode"]
}
```

---

## WebSocket Events

Connect to `ws://localhost:8765/ws` for real-time events.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.event, message.data);
};
```

### Event Format

```typescript
interface WebSocketMessage {
  event: string;
  data: any;
  timestamp: string;  // ISO 8601
}
```

### Events

#### `library:updated`

Fired when library changes (track added, removed, or metadata updated).

```json
{
  "event": "library:updated",
  "data": {
    "action": "added",
    "track_ids": [15, 16, 17]
  },
  "timestamp": "2025-01-13T23:35:00Z"
}
```

Actions: `added`, `removed`, `updated`

#### `library:scan-progress`

Fired during library scan.

```json
{
  "event": "library:scan-progress",
  "data": {
    "job_id": "scan_abc123",
    "status": "scanning",
    "scanned": 150,
    "found": 145,
    "errors": 2,
    "current_path": "/path/to/current/folder"
  },
  "timestamp": "2025-01-13T23:36:00Z"
}
```

Status: `scanning`, `completed`, `failed`

#### `library:scan-complete`

Fired when library scan completes.

```json
{
  "event": "library:scan-complete",
  "data": {
    "job_id": "scan_abc123",
    "added": 145,
    "skipped": 5,
    "errors": 2,
    "duration_ms": 12500
  },
  "timestamp": "2025-01-13T23:37:00Z"
}
```

#### `queue:updated`

Fired when queue changes.

```json
{
  "event": "queue:updated",
  "data": {
    "action": "added",
    "positions": [3, 4, 5],
    "queue_length": 8
  },
  "timestamp": "2025-01-13T23:38:00Z"
}
```

Actions: `added`, `removed`, `reordered`, `cleared`, `shuffled`

#### `favorites:updated`

Fired when favorites change.

```json
{
  "event": "favorites:updated",
  "data": {
    "action": "added",
    "track_id": 1
  },
  "timestamp": "2025-01-13T23:39:00Z"
}
```

Actions: `added`, `removed`

#### `playlists:updated`

Fired when playlists change.

```json
{
  "event": "playlists:updated",
  "data": {
    "action": "track_added",
    "playlist_id": 1,
    "track_ids": [5, 6]
  },
  "timestamp": "2025-01-13T23:40:00Z"
}
```

Actions: `created`, `updated`, `deleted`, `track_added`, `track_removed`, `reordered`

#### `settings:updated`

Fired when settings change.

```json
{
  "event": "settings:updated",
  "data": {
    "key": "volume",
    "value": 80,
    "previous_value": 75
  },
  "timestamp": "2025-01-13T23:41:00Z"
}
```

---

## Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `bad_request` | Invalid request body or parameters |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Resource already exists or conflict |
| 422 | `validation_error` | Request validation failed |
| 500 | `internal_error` | Server error |

---

## Rate Limiting

No rate limiting for localhost connections. If exposed to network, implement rate limiting at reverse proxy level.

---

## CORS

CORS is enabled for `http://localhost:*` and `tauri://localhost` origins to support Tauri webview.

---

## Health Check

### GET /api/health

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "uptime_seconds": 3600
}
```
