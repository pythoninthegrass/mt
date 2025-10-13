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

### E2E Tests (Integration Tests)

**File Pattern**: `test_e2e_*.py`
**Examples**: `test_e2e_playback.py`, `test_e2e_controls.py`, `test_e2e_queue.py`, `test_e2e_integration.py`

**Characteristics**:

- Use real VLC instance (actual audio playback)
- Start full application with API server
- Use real music files for testing
- Slower (requires startup time, VLC initialization)
- Test complete user workflows
- Verify integration between components

**Note**: In this codebase, E2E tests serve as **integration tests**. They validate cross-component interactions, end-to-end workflows, and system integration. The comprehensive E2E test suite (59+ tests) covers all integration testing requirements including player-library integration, UI-database integration, queue management workflows, and cross-component functionality.

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

### Property Tests (Hypothesis)

**File Pattern**: `test_props_*.py`
**Examples**: `test_props_player_core.py`, `test_props_queue_manager.py`, `test_props_utils.py`

**Characteristics**:

- Use mocked dependencies (like unit tests)
- Generate hundreds of test cases automatically
- Discover edge cases through randomized testing
- Validate invariants and properties that should always hold
- Run fast (similar to unit tests)
- Automatically shrink failing examples to minimal cases

**When to Use Property Tests**:

- ✅ Testing invariants (e.g., volume always in [0, 100])
- ✅ Testing mathematical properties (commutativity, associativity)
- ✅ Testing round-trip conversions (serialize → deserialize)
- ✅ Testing idempotent operations (applying twice = applying once)
- ✅ Testing boundary conditions across many inputs
- ✅ Complementing unit tests with broader input coverage
- ✅ Discovering edge cases you haven't thought of

**Example Test Cases**:
```python
from hypothesis import given, strategies as st

@given(volume=st.integers(min_value=-1000, max_value=1000))
def test_volume_clamps_to_valid_range(player_core, volume):
    """Volume should always clamp to [0, 100] regardless of input."""
    player_core.set_volume(volume)
    actual = player_core.get_volume()
    assert 0 <= actual <= 100

@given(initial_state=st.booleans())
def test_loop_toggle_idempotent(player_core, initial_state):
    """Toggling loop twice should return to original state."""
    player_core.loop_enabled = initial_state
    player_core.toggle_loop()
    player_core.toggle_loop()
    assert player_core.loop_enabled == initial_state

@given(filepaths=st.lists(st.text(min_size=1), min_size=1, max_size=50))
def test_shuffle_preserves_queue_items(queue_manager, filepaths):
    """Shuffling should preserve all items, just reorder them."""
    for filepath in filepaths:
        queue_manager.add_to_queue(filepath)

    original_items = queue_manager.get_queue_items()
    queue_manager.toggle_shuffle()
    shuffled_items = queue_manager.get_shuffled_queue_items()

    assert len(original_items) == len(shuffled_items)
```

## Running Tests

```bash
# Run ONLY unit tests (fast, for development)
uv run pytest tests/test_unit_*.py -v -p no:pydust

# Run ONLY property tests (fast, for invariant validation)
uv run pytest tests/test_props_*.py -v -p no:pydust

# Run property tests with more examples (thorough)
uv run pytest tests/test_props_*.py -v --hypothesis-profile=thorough -p no:pydust

# Run property tests with statistics
uv run pytest tests/test_props_*.py -v --hypothesis-show-statistics -p no:pydust

# Run ONLY E2E tests (slower, for integration validation)
uv run pytest tests/test_e2e_*.py -v -p no:pydust

# Run unit + property tests (fast development feedback)
uv run pytest tests/test_unit_*.py tests/test_props_*.py -v -p no:pydust

# Run all tests
uv run pytest tests/ -v -p no:pydust
```

## Test Organization

```
tests/
├── README.md                     # This file
├── conftest.py                   # Shared fixtures (Hypothesis profiles, E2E fixtures)
├── mocks/                        # Mock implementations for unit tests
│   ├── __init__.py
│   └── vlc_mock.py               # Mock VLC classes
├── helpers/                      # Test helper utilities
│   └── api_client.py             # API client for E2E tests
├── test_unit_player_core.py      # Unit tests for PlayerCore (27 tests)
├── test_unit_queue_manager.py    # Unit tests for QueueManager (18 tests)
├── test_unit_library_manager.py  # Unit tests for LibraryManager (9 tests)
├── test_props_player_core.py     # Property tests for PlayerCore (12 tests)
├── test_props_queue_manager.py   # Property tests for QueueManager (6 tests)
├── test_props_utils.py           # Property tests for utilities (18 tests)
├── test_e2e_playback.py          # E2E tests for playback (8 tests)
├── test_e2e_controls.py          # E2E tests for controls (18 tests)
├── test_e2e_queue.py             # E2E tests for queue (10 tests)
├── test_e2e_views.py             # E2E tests for views (11 tests)
├── test_e2e_library.py           # E2E tests for library (9 tests)
└── test_e2e_integration.py       # E2E integration workflow tests (6 tests)
```

**Test Suite Summary:**
- **Unit Tests**: 51 tests (~0.07s) - Fast, isolated logic testing with mocks
- **Property Tests**: 36 tests (~0.39s) - Invariant validation with Hypothesis
- **E2E/Integration Tests**: 59 tests (~25s) - Full system integration testing
- **Total**: 146 tests covering unit, property, and integration testing

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
                  E2E Test        Can be isolated with mocks?
                                        /         \
                                     YES           NO
                                      |             |
                                      v             v
                              Testing invariants  E2E Test
                              or properties?
                                /         \
                             YES           NO
                              |             |
                              v             v
                        Property Test   Unit Test
```

## Best Practices

1. **Write unit tests first** - They're faster to write and run
2. **Use property tests for invariants** - Let Hypothesis discover edge cases
3. **Use E2E tests sparingly** - Only when integration is critical
4. **Mock external dependencies** - Database, file system, VLC in unit and property tests
5. **Keep unit tests focused** - Test one thing at a time
6. **Use descriptive test names** - Should explain what and why
7. **Run unit + property tests frequently** - During development for quick feedback
8. **Run E2E tests before commits** - To catch integration issues
9. **Property tests complement unit tests** - Unit tests for specific cases, property tests for general properties

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
- **Property tests**: < 5 seconds total (with fast profile: 50 examples per test)
- **Property tests (thorough)**: < 30 seconds total (with thorough profile: 1000 examples per test)
- **E2E tests**: < 30 seconds total (depends on test music files)

## Adding New Tests

When adding a new feature:

1. Start with unit tests for core logic
2. Add property tests for invariants:
   - Boundary conditions (e.g., volume clamping)
   - Idempotent operations (e.g., toggling twice)
   - Round-trip conversions
   - Collection operations preserving elements
3. Add E2E tests if the feature involves:
   - Real audio playback
   - Cross-component integration
   - User-facing workflows
4. Ensure new tests follow the naming convention
5. Update this README if introducing new patterns

## Writing Property Tests

Property tests use Hypothesis to generate test cases automatically. Here's how to write them:

### 1. Import Hypothesis

```python
from hypothesis import given, strategies as st
```

### 2. Use @given decorator with strategies

```python
@given(volume=st.integers(min_value=-1000, max_value=1000))
def test_volume_clamps(player_core, volume):
    player_core.set_volume(volume)
    assert 0 <= player_core.get_volume() <= 100
```

### 3. Common strategies

- `st.integers(min_value, max_value)` - Generate integers
- `st.floats(min_value, max_value)` - Generate floats
- `st.booleans()` - Generate True/False
- `st.text(min_size, max_size)` - Generate strings
- `st.lists(strategy, min_size, max_size)` - Generate lists

### 4. Configure test profiles

In `conftest.py`, Hypothesis profiles are configured:

- **fast**: 50 examples per test (default for development)
- **thorough**: 1000 examples per test (for comprehensive testing)

Use `--hypothesis-profile=thorough` to run more examples.
