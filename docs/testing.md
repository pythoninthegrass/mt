# Testing Guidelines

This directory contains two types of tests: **unit tests** and **E2E (end-to-end) tests**. Understanding when to use each type is crucial for maintaining a fast, reliable test suite.

## Test Types

### Unit Tests (Mocked)

**File Pattern**: `test_unit_*.py`
**Example**: `test_unit_player_core.py`

**Characteristics**:

- Use mocked VLC (no real audio playback)
- No external dependencies (no actual files, no subprocess)
- Run very fast (<1 second total)
- Deterministic (no timing issues)
- Test core logic in isolation

**When to Use Unit Tests**:

- ✅ Testing business logic (seek calculations, state management)
- ✅ Testing control flow (play/pause, next/previous, loop, shuffle)
- ✅ Testing edge cases (volume bounds, empty queue, etc.)
- ✅ Testing internal methods (private helper functions)
- ✅ During development (fast feedback loop)
- ✅ Testing behavior that doesn't require UI or real audio

**Example Test Cases**:
```python
def test_volume_clamping(player_core):
    """Volume should clamp to 0-100 range."""
    player_core.set_volume(150)
    assert player_core.get_volume() == 100

def test_seek_to_position(player_core):
    """Seek to 50% should set time to middle of track."""
    player_core.media_player._length = 180000
    player_core.seek(0.5)
    assert player_core.media_player.get_time() == 90000
```

### E2E Tests (Integration)

**File Pattern**: `test_e2e_*.py`
**Examples**: `test_e2e_playback.py`, `test_e2e_controls.py`, `test_e2e_queue.py`

**Characteristics**:

- Use real VLC instance (actual audio playback)
- Start full application with API server
- Use real music files for testing
- Slower (requires startup time, VLC initialization)
- Test complete user workflows
- Verify integration between components

**When to Use E2E Tests**:

- ✅ Testing actual VLC integration (real playback, seeking, events)
- ✅ Testing complete user workflows (add to queue → play → skip)
- ✅ Testing API server commands
- ✅ Testing cross-component integration (player + queue + library)
- ✅ Testing behavior that depends on real files or playback
- ✅ Testing timing-sensitive behavior (track end events, progress updates)
- ✅ Regression testing for critical user paths

**Example Test Cases**:
```python
def test_play_pause_toggle(api_client, test_music_files, clean_queue):
    """Test that play/pause actually works with real VLC."""
    api_client.send('add_to_queue', files=[test_music_files[0]])
    api_client.send('play_pause')
    time.sleep(TEST_TIMEOUT)  # Wait for VLC to initialize

    status = api_client.send('get_status')
    assert status['data']['is_playing'] is True
```

## Running Tests

```bash
# Run ONLY unit tests (fast, for development)
uv run pytest tests/test_unit_*.py -v -p no:pydust

# Run ONLY E2E tests (slower, for integration validation)
uv run pytest tests/test_e2e_*.py -v -p no:pydust

# Run all tests
uv run pytest tests/ -v -p no:pydust
```

## Test Organization

```
tests/
├── README.md                    # This file
├── conftest.py                  # E2E test fixtures (app_process, api_client)
├── mocks/                       # Mock implementations for unit tests
│   ├── __init__.py
│   └── vlc_mock.py             # Mock VLC classes
├── test_unit_player_core.py    # Unit tests for PlayerCore
├── test_e2e_playback.py        # E2E tests for playback
├── test_e2e_controls.py        # E2E tests for controls
├── test_e2e_queue.py           # E2E tests for queue
├── test_e2e_views.py           # E2E tests for views
└── test_e2e_library.py         # E2E tests for library
```

## Decision Tree

```
                  Need to test something?
                          |
                          v
            Does it require real audio playback,
            actual files, or full app integration?
                    /              \
                 YES                NO
                  |                  |
                  v                  v
            E2E Test          Can be isolated with mocks?
                                    /         \
                                 YES           NO
                                  |             |
                                  v             v
                             Unit Test      E2E Test
```

## Best Practices

1. **Write unit tests first** - They're faster to write and run
2. **Use E2E tests sparingly** - Only when integration is critical
3. **Mock external dependencies** - Database, file system, VLC in unit tests
4. **Keep unit tests focused** - Test one thing at a time
5. **Use descriptive test names** - Should explain what and why
6. **Run unit tests frequently** - During development for quick feedback
7. **Run E2E tests before commits** - To catch integration issues

## Mock VLC Usage

For unit tests, import mocks from `tests.mocks`:

```python
from tests.mocks import MockInstance, MockEventType

@pytest.fixture
def mock_vlc():
    mock_vlc_module = Mock()
    mock_vlc_module.Instance = MockInstance
    mock_vlc_module.EventType = MockEventType
    return mock_vlc_module

@pytest.fixture
def player_core(mock_vlc, mock_db, mock_queue_manager):
    with patch.dict('sys.modules', {'vlc': mock_vlc}):
        from core.controls import PlayerCore
        return PlayerCore(mock_db, mock_queue_manager)
```

## Performance Goals

- **Unit tests**: < 1 second total (currently: ~0.12s)
- **E2E tests**: < 30 seconds total (depends on test music files)

## Adding New Tests

When adding a new feature:

1. Start with unit tests for core logic
2. Add E2E tests if the feature involves:
   - Real audio playback
   - Cross-component integration
   - User-facing workflows
3. Ensure new tests follow the naming convention
4. Update this README if introducing new patterns
