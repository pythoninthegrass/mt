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

### Property Tests (Hypothesis) - Python [DEPRECATED]

**Note**: Python backend is deprecated. These tests remain for reference but new property tests should use fast-check (JavaScript) or proptest (Rust).

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

### JavaScript Property Tests (fast-check)

**File Pattern**: `*.props.test.js`
**Examples**: `queue.props.test.js`, `player-utils.props.test.js`

**Characteristics**:

- Test frontend Alpine.js stores and utility functions
- Generate hundreds of test cases automatically using fast-check
- Validate invariants and properties across randomized inputs
- Run fast with Vitest test runner
- Automatically shrink failing examples to minimal reproducible cases
- No Tauri mocking required - test pure logic

**When to Use JavaScript Property Tests**:

- ✅ Testing queue operations (add, remove, shuffle, reorder)
- ✅ Testing player utilities (formatTime, clamp, calculateProgress)
- ✅ Testing invariants (volume ∈ [0,100], shuffle preserves tracks)
- ✅ Testing boundary conditions (empty queues, single tracks, overflow)
- ✅ Testing threshold checks (play count, scrobble triggers)
- ✅ Complementing E2E tests with pure logic validation

**Example Test Cases**:
```javascript
import { test, fc } from '@fast-check/vitest';

test.prop([fc.integer({ min: -1000, max: 2000 })])(
  'volume clamps to [0, 100]',
  async (volume) => {
    await store.setVolume(volume);

    expect(store.volume).toBeGreaterThanOrEqual(0);
    expect(store.volume).toBeLessThanOrEqual(100);
  }
);

test.prop([fc.uniqueArray(trackArbitrary, { selector: t => t.id })])(
  'shuffle preserves all tracks',
  async (tracks) => {
    store.items = [...tracks];
    const originalIds = tracks.map(t => t.id).sort();

    await store.toggleShuffle();
    const shuffledIds = store.items.map(t => t.id).sort();

    expect(shuffledIds).toEqual(originalIds);
  }
);

test.prop([fc.integer({ min: 0, max: 86400000 })])(
  'formatTime never returns negative values',
  (ms) => {
    const formatted = formatTime(ms);
    const [minutes, seconds] = formatted.split(':').map(Number);

    expect(minutes).toBeGreaterThanOrEqual(0);
    expect(seconds).toBeGreaterThanOrEqual(0);
    expect(seconds).toBeLessThan(60);
  }
);
```

### Rust Property Tests (proptest)

**File Pattern**: `*_props_test.rs`
**Examples**: `queue_props_test.rs`

**Characteristics**:

- Test backend Rust database operations and business logic
- Generate hundreds of test cases automatically using proptest
- Validate invariants across randomized inputs
- Run with `cargo test` alongside unit tests
- Automatically shrink failing examples to minimal reproducible cases
- Test with in-memory SQLite databases for speed

**When to Use Rust Property Tests**:

- ✅ Testing database operations (add, remove, insert at position)
- ✅ Testing queue consistency (position numbering, track preservation)
- ✅ Testing boundary conditions (empty queues, position bounds)
- ✅ Testing operation sequences (add → remove → clear)
- ✅ Testing invariants (sequential positions, non-negative values)
- ✅ Complementing unit tests with broader input coverage

**Example Test Cases**:
```rust
use proptest::prelude::*;

proptest! {
    /// Adding tracks to queue preserves track count
    #[test]
    fn add_to_queue_preserves_count(track_ids in track_id_list_strategy()) {
        let conn = create_test_db();

        // Add tracks to library first
        for &track_id in &track_ids {
            add_test_track(&conn,
                          &format!("/path/track{}.mp3", track_id),
                          &format!("Track {}", track_id));
        }

        let added = add_to_queue(&conn, &track_ids, None).unwrap();
        let queue = get_queue(&conn).unwrap();

        prop_assert_eq!(queue.len(), track_ids.len());
        prop_assert_eq!(added, track_ids.len() as i64);
    }

    /// Queue positions are always sequential
    #[test]
    fn queue_positions_are_sequential(track_count in 1usize..20) {
        let conn = create_test_db();

        let track_ids: Vec<i64> = (0..track_count)
            .map(|i| add_test_track(&conn,
                                   &format!("/path/track{}.mp3", i),
                                   &format!("Track {}", i)))
            .collect();

        add_to_queue(&conn, &track_ids, None).unwrap();
        let queue = get_queue(&conn).unwrap();

        // Positions should be 0, 1, 2, ...
        for (expected_pos, item) in queue.iter().enumerate() {
            prop_assert_eq!(item.position, expected_pos as i64);
        }
    }
}
```

## Running Tests

### Quick Reference (Task Commands)

| Layer | Task Command | Tests | Duration |
|-------|--------------|-------|----------|
| **All Tests** | `task test` | Rust + Vitest | ~30s |
| **Rust Backend** | `task test` | 317 tests | ~15s |
| **Vitest Unit** | `task npm:test` | 179 tests | ~2s |
| **Playwright E2E** | `task test:e2e` | 409 tests | ~1m |

```bash
# Run all tests (Rust + Vitest)
task test

# Run Vitest unit/property tests only
task npm:test

# Run Vitest in watch mode
task npm:test:watch

# Run Playwright E2E tests
task test:e2e                    # fast mode (webkit only)
E2E_MODE=full task test:e2e      # all browsers
task npm:test:e2e:ui             # interactive UI mode
```

### JavaScript Tests (Vitest)

```bash
# Via task runner
task npm:test                         # Run all unit/property tests
task npm:test:watch                   # Watch mode for development

# Direct npm commands
npm --prefix app/frontend test        # Run all tests
npm --prefix app/frontend test -- __tests__/*.props.test.js  # Property tests only
npm --prefix app/frontend test -- __tests__/library.store.test.js  # Specific file
npm --prefix app/frontend run test:coverage  # With coverage report
```

### Rust Tests

```bash
# Via task runner (included in `task test`)
task test

# Direct cargo commands
cargo test --manifest-path src-tauri/Cargo.toml           # All tests
cargo test --manifest-path src-tauri/Cargo.toml props     # Property tests only
cargo test --manifest-path src-tauri/Cargo.toml -- --nocapture  # Verbose output

# More property test examples
PROPTEST_CASES=1000 cargo test --manifest-path src-tauri/Cargo.toml props
```

### E2E Tests (Playwright)

```bash
# Via task runner
task test:e2e                         # Fast mode (webkit only, ~1m)
E2E_MODE=full task test:e2e           # All browsers (~3m)
E2E_MODE=tauri task test:e2e          # Include @tauri tests (~4m)
task npm:test:e2e:ui                  # Interactive UI mode

# Direct playwright commands
npx playwright test tests/library.spec.js     # Specific file
npx playwright test --headed                  # See browser
npx playwright test --debug tests/sidebar.spec.js  # Debug mode
npx playwright codegen                        # Generate test code
```

**E2E_MODE Options:**

| Mode | Browsers | @tauri tests | Tests | Duration |
|------|----------|--------------|-------|----------|
| `fast` (default) | WebKit only | Skipped | ~409 | ~1m |
| `full` | All 3 | Skipped | ~1227 | ~3m |
| `tauri` | All 3 | Included | ~1300+ | ~4m |

### Coverage Reports

```bash
# Frontend coverage (Vitest)
cd app/frontend && npm run test:coverage
# Report at: app/frontend/coverage/

# Backend coverage (macOS - uses llvm-cov)
cd src-tauri && cargo llvm-cov --html --output-dir coverage

# Backend coverage (Linux CI - uses tarpaulin)
cargo tarpaulin --out Html --output-dir coverage --fail-under 50
```

### Python Tests [DEPRECATED]

```bash
# Run ONLY unit tests (fast, for development)
uv run pytest tests/test_unit_*.py

# Run ONLY property tests (fast, for invariant validation)
uv run pytest tests/test_props_*.py

# Run all tests
uv run pytest tests/

# Note: Python backend is deprecated - use Rust tests instead
```

## Test Organization

### Python Tests [DEPRECATED]

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

### JavaScript Tests (Vitest)

```
app/frontend/__tests__/
├── library.store.test.js         # Library store unit tests (62 tests)
├── ui.store.test.js              # UI store unit tests (51 tests)
├── queue.store.test.js           # Queue shuffle invariant tests (13 tests)
├── queue.props.test.js           # Queue property tests (30 tests)
├── player.props.test.js          # Player property tests (38 tests)
├── player-utils.props.test.js    # Player utility tests (32 tests)
└── setup-player-mocks.js         # Test setup and mocks
```

### Rust Tests

```
src-tauri/src/db/
├── queue.rs                      # Queue database operations
└── queue_props_test.rs           # Property tests for queue operations (11 tests)
```

### E2E Tests (Playwright)

```
tests/
├── library.spec.js               # Library view tests
├── sidebar.spec.js               # Sidebar navigation tests
├── queue.spec.js                 # Queue management tests
└── player.spec.js                # Player controls tests
```

**Test Suite Summary:**

| Layer | Tests | Duration | Description |
|-------|-------|----------|-------------|
| **Rust Backend** | 317 | ~15s | Unit + property tests (proptest) |
| **Vitest Unit** | 179 | ~2s | Store unit + property tests (fast-check) |
| **Playwright E2E** | 409 | ~1m | Browser integration tests (webkit) |
| **Total Active** | **905** | ~1.5m | Full test suite (fast mode) |

- **Python Tests** [DEPRECATED]: Legacy tests remain for reference only

## Decision Tree

```
                      Need to test something?
                              |
                              v
                Does it require real audio playback,
                browser testing, or full app integration?
                        /              \
                     YES                NO
                      |                  |
                      v                  v
              E2E Test (Playwright)  Frontend or Backend?
                                        /         \
                                Frontend            Backend
                                (JavaScript)        (Rust)
                                      |                |
                                      v                v
                              Testing invariants  Testing invariants
                              or properties?      or properties?
                                /         \         /         \
                             YES           NO     YES           NO
                              |             |      |             |
                              v             v      v             v
                        JS Property    Unit Test  Rust       Unit Test
                        Test                      Property
                        (fast-check)              Test
                                                  (proptest)
```

## Best Practices

1. **Write unit tests first** - They're faster to write and run
2. **Use property tests for invariants** - Let fast-check/proptest discover edge cases
3. **Frontend testing**:
   - Use JavaScript property tests (fast-check) for Alpine.js stores and utilities
   - Extract pure functions when possible to avoid complex Tauri mocking
   - Test invariants like volume bounds, shuffle preservation, threshold checks
4. **Backend testing**:
   - Use Rust property tests (proptest) for database operations and business logic
   - Use in-memory SQLite for fast property test execution
   - Test invariants like sequential positions, track preservation, bounds checking
5. **Use E2E tests (Playwright) for integration** - Browser automation, full workflows, cross-component behavior
6. **Mock external dependencies** - Tauri APIs, database, file system in unit and property tests
7. **Keep unit tests focused** - Test one thing at a time
8. **Use descriptive test names** - Should explain what and why
9. **Run property tests frequently** - During development for quick feedback on invariants
10. **Run E2E tests before commits** - To catch integration issues across the full stack
11. **Property tests complement unit tests** - Unit tests for specific cases, property tests for general properties
12. **Use test shrinking** - Both fast-check and proptest automatically minimize failing examples

## Mock VLC Usage [DEPRECATED - Python Only]

For Python unit tests, import mocks from `tests.mocks`:

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

## JavaScript and Rust Testing Patterns

### JavaScript Property Tests (fast-check)

**Unique Array Generation** (avoid duplicate IDs):
```javascript
const trackArbitrary = fc.integer({ min: 1, max: 10000 }).map(id => ({
  id,
  title: `Track ${id}`,
  filepath: `/path/track${id}.mp3`,
}));

const trackListArbitrary = fc.uniqueArray(trackArbitrary, {
  minLength: 0,
  maxLength: 100,
  selector: track => track.id, // Ensure unique IDs
});
```

**Float Generation** (avoid NaN):
```javascript
fc.float({ min: 0, max: 1, noNaN: true })
```

**Threshold Testing** (avoid floating-point precision issues):
```javascript
// Test with epsilon tolerance instead of exact boundary
const beforeTime = Math.floor(duration * threshold) - 10; // 10ms before
const afterTime = Math.floor(duration * threshold) + 10; // 10ms after
```

### Rust Property Tests (proptest)

**Strategy Generation**:
```rust
fn track_id_strategy() -> impl Strategy<Value = i64> {
    1i64..=1000
}

fn track_id_list_strategy() -> impl Strategy<Value = Vec<i64>> {
    prop::collection::vec(track_id_strategy(), 0..20)
}
```

**In-Memory Test Database**:
```rust
fn create_test_db() -> Connection {
    let conn = Connection::open_in_memory().unwrap();
    // Create schema...
    conn
}
```

**Type Casting** (fix i64 vs usize mismatches):
```rust
// Cast usize to i64 for comparison
prop_assert_eq!(item.position, expected_pos as i64);

// Use references for string comparison
prop_assert_eq!(&queue[i].track.filepath, &expected_filepath);
```

## Performance Goals

| Test Layer | Target | Current |
|------------|--------|---------|
| **Rust Backend** | < 20s | ~15s (317 tests) |
| **Vitest Unit** | < 5s | ~2s (179 tests) |
| **Playwright (fast)** | < 2m | ~1m (409 tests) |
| **Playwright (full)** | < 5m | ~3m (1227 tests) |
| **Full Suite** | < 2m | ~1.5m (905 tests) |

## Adding New Tests

When adding a new feature:

1. **Start with unit tests** for core logic (if applicable)
2. **Add property tests** for invariants:
   - **Frontend (JavaScript)**: Use fast-check for Alpine.js stores and utilities
   - **Backend (Rust)**: Use proptest for database operations and business logic
   - Common invariant patterns:
     - Boundary conditions (e.g., volume clamping to [0, 100])
     - Idempotent operations (e.g., toggling twice returns to original state)
     - Collection operations (e.g., shuffle preserves all tracks)
     - Sequential properties (e.g., queue positions are 0, 1, 2, ...)
     - Round-trip conversions (e.g., serialize → deserialize)
3. **Add E2E tests (Playwright)** if the feature involves:
   - Real browser interaction
   - Cross-component integration
   - User-facing workflows
   - Audio playback (tag with `@tauri`)
4. **Ensure new tests follow naming conventions**:
   - JavaScript: `*.props.test.js`
   - Rust: `*_props_test.rs`
   - Playwright: `*.spec.js`
5. **Update this README** if introducing new patterns or test categories

## Writing Property Tests

### JavaScript Property Tests (fast-check)

**1. Import fast-check**:
```javascript
import { test, fc } from '@fast-check/vitest';
```

**2. Use test.prop() with arbitraries**:
```javascript
test.prop([fc.integer({ min: 0, max: 100 })])(
  'volume stays in valid range',
  async (volume) => {
    await store.setVolume(volume);
    expect(store.volume).toBeGreaterThanOrEqual(0);
    expect(store.volume).toBeLessThanOrEqual(100);
  }
);
```

**3. Common arbitraries**:
- `fc.integer({ min, max })` - Generate integers
- `fc.float({ min, max, noNaN: true })` - Generate floats (avoid NaN!)
- `fc.boolean()` - Generate true/false
- `fc.string({ minLength, maxLength })` - Generate strings
- `fc.array(arbitrary, { minLength, maxLength })` - Generate arrays
- `fc.uniqueArray(arbitrary, { selector })` - Generate arrays with unique elements

**4. Configuration**:
Default: 100 examples per test. Configure in vitest.config.js if needed.

### Rust Property Tests (proptest)

**1. Import proptest**:
```rust
use proptest::prelude::*;
```

**2. Use proptest! macro with strategies**:
```rust
proptest! {
    #[test]
    fn volume_clamps_to_valid_range(volume in -1000i32..=2000) {
        let clamped = clamp(volume, 0, 100);
        prop_assert!(clamped >= 0);
        prop_assert!(clamped <= 100);
    }
}
```

**3. Common strategies**:
- `min..max` - Generate integers in range
- `min..=max` - Generate integers in inclusive range
- `prop::collection::vec(strategy, size_range)` - Generate vectors
- `prop::option::of(strategy)` - Generate Option<T>
- `"regex pattern"` - Generate strings matching regex

**4. Configuration**:
Default: 256 examples per test. Configure via environment:
```bash
PROPTEST_CASES=1000 cargo test  # More examples
PROPTEST_MAX_SHRINK_ITERS=0 cargo test  # Disable shrinking (faster)
```

### Python Property Tests (Hypothesis) [DEPRECATED]

**1. Import Hypothesis**:
```python
from hypothesis import given, strategies as st
```

**2. Use @given decorator with strategies**:
```python
@given(volume=st.integers(min_value=-1000, max_value=1000))
def test_volume_clamps(player_core, volume):
    player_core.set_volume(volume)
    assert 0 <= player_core.get_volume() <= 100
```

**3. Common strategies**:
- `st.integers(min_value, max_value)` - Generate integers
- `st.floats(min_value, max_value)` - Generate floats
- `st.booleans()` - Generate True/False
- `st.text(min_size, max_size)` - Generate strings
- `st.lists(strategy, min_size, max_size)` - Generate lists

**4. Configure test profiles** (in `conftest.py`):
- **fast**: 50 examples per test (default)
- **thorough**: 1000 examples per test
- Use `--hypothesis-profile=thorough` for more examples
