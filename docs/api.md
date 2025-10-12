# API Server Documentation

The mt music player includes a socket-based API server that enables programmatic control from external tools, LLMs, and automation scripts. This document provides comprehensive documentation on architecture, usage, and examples.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [API Commands Reference](#api-commands-reference)
- [Client Libraries](#client-libraries)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Overview

**Protocol**: JSON over TCP sockets
**Default Port**: 5555 (configurable)
**Security**: Localhost-only by default
**Thread Safety**: All commands execute on main UI thread
**Logging**: Full integration with Eliot structured logging

### Key Features

- **Comprehensive Control**: Playback, volume, queue, UI navigation, and more
- **Thread-Safe Execution**: Commands safely marshalled to main UI thread via tkinter's `after()`
- **Error Handling**: Detailed JSON error responses with troubleshooting info
- **LLM-Friendly**: Designed for automation and AI agent integration
- **Example Scripts**: Simple, full-featured, and automation examples included

## Architecture

### Core Components

The API server is implemented in `core/api.py` and consists of:

1. **APIServer Class**
   - Background thread running socket server
   - JSON command parser and validator
   - Command routing to 90+ handler methods
   - Response formatter with error handling

2. **Integration Points**
   - Initialized: `MusicPlayer.setup_api_server()` in `core/player.py`
   - Shutdown: `MusicPlayer.on_window_close()` cleanup
   - Access: Full reference to `MusicPlayer` instance and all components

3. **Command Handlers**
   - Playback controls (play, pause, stop, next, previous)
   - Track selection and queue management
   - UI navigation (view switching, item selection)
   - Volume and seek controls
   - Utility controls (loop, shuffle, favorite)
   - Information queries (status, track info, queue contents)
   - Media key simulation

4. **Thread Safety Model**
   ```python
   # Commands execute on main thread using tkinter's after()
   self.music_player.window.after(0, execute_on_main_thread)
   ```

### Design Decisions

- **Socket-based vs HTTP**: Sockets provide lower latency and simpler implementation
- **JSON Protocol**: Easy to debug, language-agnostic, human-readable
- **Localhost-only**: Security by default, no authentication needed
- **Synchronous Execution**: Commands block until completion (5s timeout)

## Configuration

Enable the API server through environment variables:

```bash
# Enable API server (disabled by default)
export MT_API_SERVER_ENABLED=true

# Optional: Configure custom port (default: 5555)
export MT_API_SERVER_PORT=5555

# Start the application
uv run main.py

# Or with auto-reload for development
MT_API_SERVER_ENABLED=true uv run repeater
```

Configuration is managed in `config.py`:

```python
# API Server Configuration
API_SERVER_ENABLED = config('MT_API_SERVER_ENABLED', default=False, cast=bool)
API_SERVER_PORT = config('MT_API_SERVER_PORT', default=5555, cast=int)
```

## API Commands Reference

All commands follow a standard JSON request/response format:

**Request Format:**
```json
{
  "action": "command_name",
  "param1": "value1",
  "param2": "value2"
}
```

**Response Format:**
```json
{
  "status": "success",
  "data": {...}  // Optional additional data
}
```

### Playback Controls

#### `play_pause` - Toggle play/pause

**Request:**
```json
{"action": "play_pause"}
```

**Response:**
```json
{
  "status": "success",
  "is_playing": true
}
```

**Context**: This is the most commonly used command. It toggles between play and pause states, making it ideal for media key bindings and quick automation scripts.

#### `play` - Start playback

**Request:**
```json
{"action": "play"}
```

**Response:**
```json
{
  "status": "success",
  "is_playing": true
}
```

**Context**: Forces playback to start. Use this when you need to ensure playback is active, regardless of current state.

#### `pause` - Pause playback

**Request:**
```json
{"action": "pause"}
```

**Response:**
```json
{
  "status": "success",
  "is_playing": false
}
```

**Context**: Forces pause. Useful for implementing "quiet hours" automation or event-driven pausing.

#### `stop` - Stop playback

**Request:**
```json
{"action": "stop"}
```

**Response:**
```json
{"status": "success"}
```

**Context**: Completely stops playback and resets the player state. Different from pause - use when ending a listening session.

#### `next` - Skip to next track

**Request:**
```json
{"action": "next"}
```

**Response:**
```json
{"status": "success"}
```

**Context**: Respects shuffle and loop modes. Will wrap around to first track if loop is enabled.

#### `previous` - Go to previous track

**Request:**
```json
{"action": "previous"}
```

**Response:**
```json
{"status": "success"}
```

**Context**: Returns to the previous track in queue. Respects shuffle history.

### Volume & Seek

#### `set_volume` - Set volume (0-100)

**Request:**
```json
{
  "action": "set_volume",
  "volume": 75
}
```

**Response:**
```json
{
  "status": "success",
  "volume": 75.0
}
```

**Context**: Volume is percentage-based (0-100). Changes are immediate and logged via Eliot. Useful for time-based automation (e.g., lower volume after 10 PM).

#### `seek` - Relative seek (offset in seconds)

**Request:**
```json
{
  "action": "seek",
  "offset": 10.0
}
```

**Response:**
```json
{
  "status": "success",
  "new_position": 45.5
}
```

**Context**: Seeks relative to current position. Positive values skip forward, negative skip backward. Useful for "skip 30 seconds" automation.

#### `seek_to_position` - Absolute seek (position in seconds)

**Request:**
```json
{
  "action": "seek_to_position",
  "position": 30.0
}
```

**Response:**
```json
{
  "status": "success",
  "position": 30.0
}
```

**Context**: Seeks to exact timestamp. Use when you need precise positioning (e.g., "start at 2:30").

### UI Navigation

#### `switch_view` - Switch views

**Valid views**: `library`, `queue`, `liked`, `top25`

**Request:**
```json
{
  "action": "switch_view",
  "view": "liked"
}
```

**Response:**
```json
{
  "status": "success",
  "view": "Liked Songs"
}
```

**Context**: Changes the active view in the player. Useful for automated navigation or testing UI workflows.

### Information Queries

#### `get_status` - Get comprehensive player status

**Request:**
```json
{"action": "get_status"}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "is_playing": true,
    "loop_enabled": false,
    "shuffle_enabled": true,
    "volume": 75,
    "current_time": 45.2,
    "duration": 320.5,
    "current_view": "Queue",
    "current_track": {
      "title": "Strobe",
      "artist": "deadmau5",
      "album": "For Lack of a Better Name",
      "filepath": "/path/to/song.mp3"
    }
  }
}
```

**Context**: Most comprehensive command - returns all player state. Use this for LLM context gathering or dashboard displays.

#### `get_queue` - Get current queue contents

**Request:**
```json
{"action": "get_queue"}
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "index": 0,
      "title": "Strobe",
      "artist": "deadmau5",
      "album": "For Lack of a Better Name"
    }
  ],
  "count": 1
}
```

**Context**: Returns all tracks in playback queue with metadata. Useful for queue management UIs or analysis.

## Client Libraries

The API includes three client implementations in `api/examples/`:

### 1. Simple Client (`api/examples/simple_client.py`)

Minimal implementation for quick scripts:

```python
import sys
sys.path.insert(0, 'api/examples')
from simple_client import send_command

# Basic usage
send_command('play_pause')
send_command('set_volume', volume=60)

# Get status
status = send_command('get_status')
if status['status'] == 'success':
    print(f"Playing: {status['data']['is_playing']}")
```

**Use when**: You need minimal code for simple automation tasks.

**Location**: `api/examples/simple_client.py`

### 2. Full Client (`api/examples/client.py`)

Object-oriented client with helper methods:

```python
import sys
sys.path.insert(0, 'api/examples')
from client import MtApiClient

client = MtApiClient()

# Playback control
client.play_pause()
client.next_track()
client.set_volume(75)

# Get information
status = client.get_status()
track = client.get_current_track()
queue = client.get_queue()
```

**Use when**: Building robust applications or complex automation.

**Location**: `api/examples/client.py`

### 3. Automation Examples (`api/examples/automation.py`)

Comprehensive test and automation suite:

```bash
# Run all tests
cd api/examples && python automation.py

# Or run specific tests in code
import sys
sys.path.insert(0, 'api/examples')
from automation import test_playback_controls

test_playback_controls(client)
```

**Use when**: Testing API functionality or learning the API through examples.

**Location**: `api/examples/automation.py`

## Usage Examples

### Basic Playback Automation

```python
import socket
import json

def send_api_command(action, **kwargs):
    s = socket.socket()
    s.connect(('localhost', 5555))
    command = {'action': action, **kwargs}
    s.send(json.dumps(command).encode())
    response = s.recv(4096).decode()
    s.close()
    return json.loads(response)

# Control playback
send_api_command('play')
send_api_command('set_volume', volume=75)
send_api_command('next')
```

### LLM Context Gathering

```python
from api_examples.client import MtApiClient

client = MtApiClient()

# Get comprehensive state for LLM
status = client.get_status()['data']

context = f"""
Current Music Player State:
- Playing: {status['is_playing']}
- Volume: {status['volume']}%
- Loop: {status['loop_enabled']}
- Shuffle: {status['shuffle_enabled']}
- Track: {status['current_track']['title']} by {status['current_track']['artist']}
- Progress: {status['current_time']:.1f}s / {status['duration']:.1f}s
"""

# LLM can now make informed decisions
if status['volume'] > 80:
    client.set_volume(60)
    print("Volume reduced from unsafe level")
```

### Automated Testing

```python
from api_examples.client import MtApiClient

def test_playback_flow():
    client = MtApiClient()

    # Start playback
    result = client.play()
    assert result['status'] == 'success'

    # Verify state
    status = client.get_status()
    assert status['data']['is_playing'] == True

    # Test volume control
    client.set_volume(50)
    status = client.get_status()
    assert status['data']['volume'] == 50

    # Test track navigation
    client.next_track()
    print("All tests passed!")

test_playback_flow()
```

### Time-Based Automation

```python
from api_examples.client import MtApiClient
import datetime

client = MtApiClient()

# Quiet hours automation
now = datetime.datetime.now().hour

if 22 <= now or now < 7:  # 10 PM to 7 AM
    status = client.get_status()
    if status['data']['volume'] > 30:
        client.set_volume(30)
        print("Quiet hours: Volume reduced to 30%")
```

## Error Handling

All API errors follow a consistent format:

```json
{
  "status": "error",
  "message": "Description of the error"
}
```

### Common Error Scenarios

1. **Unknown Action**

```json
{
  "status": "error",
  "message": "Unknown action: foo",
  "available_actions": ["play_pause", "play", "pause", ...]
}
```

2. **Missing Parameters**

```json
{
  "status": "error",
  "message": "No volume specified"
}
```

3. **Invalid Values**

```json
{
  "status": "error",
  "message": "Volume must be between 0 and 100"
}
```

4. **Execution Timeout**

```json
{
  "status": "error",
  "message": "Command execution timed out"
}
```

### Error Handling Example

```python
def safe_api_call(client, action, **kwargs):
    try:
        response = getattr(client, action)(**kwargs)
        if response['status'] == 'error':
            print(f"API Error: {response['message']}")
            return None
        return response
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

# Usage
result = safe_api_call(client, 'set_volume', volume=75)
if result:
    print("Volume set successfully")
```

## Security Considerations

1. **Localhost Only**: Server binds to `127.0.0.1` by default
   - Only accepts connections from the same machine
   - No network exposure without explicit configuration

2. **No Authentication**: Assumes localhost environment is trusted
   - Suitable for single-user desktop application
   - Add authentication layer if exposing to network

3. **Port Configuration**: Use non-standard ports if needed
   ```bash
   MT_API_SERVER_PORT=9999 uv run main.py
   ```

4. **Firewall Protection**: Ensure port is not exposed
   ```bash
   # Check if port is listening externally (should only show 127.0.0.1)
   netstat -an | grep 5555
   ```

5. **Input Validation**: All commands validated before execution
   - Parameter type checking
   - Value range validation
   - Command existence verification

## Troubleshooting

### Connection Refused

**Error:**
```
Error: [Errno 61] Connection refused
```

**Solutions:**

1. Ensure API server is enabled:
   ```bash
   MT_API_SERVER_ENABLED=true uv run main.py
   ```
2. Check if app is running:
   ```bash
   ps aux | grep "python.*main.py"
   ```
3. Verify port is not in use:
   ```bash
   lsof -i :5555
   ```

### Timeout Errors

**Error:**
```json
{"status": "error", "message": "Command execution timed out"}
```

**Solutions:**

1. UI thread is blocked - check for long-running operations
2. Increase timeout (edit `core/api.py` if needed)
3. Check Eliot logs for blocking operations

### Invalid Commands

**Error:**
```json
{
  "status": "error",
  "message": "Unknown action: foo"
}
```

**Solution:** Use `get_status()` to see available commands or check this documentation.

### Performance Issues

If experiencing slow response times:

1. Check system resources (CPU, memory)
2. Review Eliot logs for bottlenecks
3. Ensure VLC backend is responsive
4. Consider reducing concurrent API calls

## Performance Characteristics

- **Latency**: ~5-20ms for typical commands
- **Throughput**: Handles multiple concurrent connections
- **Timeout**: 5 second execution limit per command
- **Thread Safety**: All operations serialized on main UI thread
- **Max Connections**: No hard limit (system-dependent)

## See Also

- [Example Scripts](../api_examples/README.md) - Complete example implementations
- [Python Architecture](python-architecture.md) - Core system design
- [VLC Integration](vlc-integration.md) - Audio playback details
- [AGENTS.md](../AGENTS.md) - Development guidelines
