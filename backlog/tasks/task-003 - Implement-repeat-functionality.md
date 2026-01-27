---
id: task-003
title: Implement repeat functionality
status: Done
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2026-01-24 22:28'
labels: []
dependencies: []
ordinal: 40382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add repeat modes for single track and ~~all tracks~~ (latter technically exists with loop button)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add repeat toggle button to player controls
- [x] #2 Implement repeat-one mode
- [x] #3 Update UI to show current repeat state
- [x] #4 Test repeat functionality with different queue states
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
- Use repeat_one.png image in place of the loop utility control when pressed a second time.
  - e.g., loop OFF > ON > REPEAT 1 > track either repeats once or user clicks REPEAT 1 to circle back to loop OFF
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Final Implementation: "Play Once More" Pattern ✅

### Overview
Repeat-one implements a "play once more" pattern where the user can request the currently playing track to play one additional time after it finishes, then automatically revert to loop OFF.

### Three-State Toggle Cycle
- **Loop OFF** (default): Tracks play once, removed from queue after playing
- **Loop ALL** (first click): All tracks loop in carousel mode
- **Repeat ONE** (second click): Current track queued for one more playthrough, auto-reverts to OFF
- Third click returns to Loop OFF

### Core Behavior

**When repeat-one is activated (second click):**
1. Current playing track is **moved** (not copied) from current_index to index 0
2. Track continues playing from current position
3. `repeat_one_prepended_track` tracks which file was moved

**When current track finishes (first playthrough):**
1. Check: `repeat_one=True and pending_revert=False`
2. Directly play track at index 0 (ignores shuffle completely)
3. Set `current_index = 0`

**When moved track starts playing at index 0:**
1. `_play_file()` detects: `repeat_one=True and filepath == repeat_one_prepended_track`
2. Set `repeat_one_pending_revert = True` (ready to auto-revert)
3. Clear `repeat_one_prepended_track = None`

**When track finishes second playthrough:**
1. Check: `repeat_one=True and pending_revert=True`
2. Auto-revert: set `repeat_one=False, loop_enabled=False`
3. Update UI to show loop OFF
4. Continue with loop OFF behavior (remove track, play next)

**Manual navigation (next/previous) during repeat-one:**
1. Plays track at index 0 immediately ("skip to the repeat")
2. Reverts to loop ALL (not OFF)
3. User gets their repeat, just earlier than natural track end

### Key Implementation Details

**QueueManager (core/queue.py):**
- `move_current_to_beginning()`: Moves track from current_index to index 0 (no duplication)
- Adjusts indices automatically
- Invalidates shuffle when queue modified

**PlayerCore (core/controls/player_core.py):**
- State variables:
  - `self.repeat_one`: Current repeat-one state (persisted in DB)
  - `self.repeat_one_pending_revert`: Flag for auto-revert after second playthrough
  - `self.repeat_one_prepended_track`: Filepath tracking for moved track
- `toggle_loop()`: Calls `move_current_to_beginning()` when activating repeat-one
- `_handle_track_end()`: Three-phase logic (stop_after_current, repeat-one auto-revert, repeat-one first playthrough, normal loop behavior)
- `next_song()` / `previous_song()`: Jump to index 0, revert to loop ALL
- `_play_file()`: Detect moved track starting, set pending_revert

**API (api/server.py):**
- `get_status`: Returns `repeat_one` state
- `toggle_loop`: Returns both `loop_enabled` and `repeat_one`

### Shuffle Override
Repeat-one **completely overrides shuffle** - when user explicitly wants to hear a track again, shuffle is ignored:
- Track at index 0 is always played next
- No shuffle navigation used during repeat-one
- Works identically with shuffle ON or OFF

### Test Coverage

**Unit Tests (9 tests):**
- `TestPlayerCoreLoop` (4 tests): Three-state toggle cycle validation
- `TestPlayerCoreRepeatOne` (5 tests):
  - Track moved to beginning on activation
  - Auto-revert after second playthrough
  - Manual next/previous plays prepended track
  - stop_after_current precedence

**E2E Tests (3 tests):**
- Three-state toggle verification
- State persistence across API calls
- Multi-toggle cycle correctness

**Test fixture updates:**
- `clean_queue` fixture updated to handle three-state reset
- Loops until both `loop_enabled` and `repeat_one` are False

### Commits
1. `d3a6ee0` - Phase 1: Core state management infrastructure
2. `f736f4c` - Phase 2: Initial playback logic (later corrected)
3. `662885e` - Phase 3: UI with three-state icons
4. `5ba2f80` - test: Update loop tests, add repeat-one tests
5. `2966137` - feat: Expose repeat_one in API, add E2E test
6. `f103818` - fix: Change to queue rotation (incorrect approach)
7. `d321117` - fix: Implement correct "play once more" behavior
8. `9b43eac` - fix: Track prepended track for proper auto-revert
9. `a93956b` - fix: Override shuffle, manual nav jumps to prepended
10. `ff32a75` - fix: Use move instead of prepend (no duplicates)

### Final Result
✅ All 61 tests pass
✅ Works with shuffle ON/OFF
✅ No duplicate tracks in queue
✅ Auto-reverts correctly after second playthrough
✅ Manual navigation jumps to repeat track
✅ Complete "play once more" UX

## Remaining Implementation (Phases 4-8)

### Phase 4: API Integration

**Files to modify:**

1. **api/server.py:568-570** - Update `_handle_toggle_loop()` response:
```python
return {
    'status': 'success',
    'loop_enabled': new_state.loop_enabled,
    'repeat_one': new_state.repeat_one  # ADD THIS
}
```

2. **api/server.py:639** - Update status endpoint response:
```python
'loop_enabled': self.music_player.player_core.loop_enabled,
'repeat_one': self.music_player.player_core.repeat_one,  # ADD THIS
```

3. **api/examples/automation.py:123** - Update display logic:
```python
print(f"Loop Enabled: {data.get('loop_enabled', False)}")
print(f"Repeat One: {data.get('repeat_one', False)}")  # ADD THIS
```

**Testing:**
- Start API server: `MT_API_SERVER_ENABLED=true uv run main.py`
- Run automation script: `python api/examples/automation.py`
- Verify toggle_loop command cycles through all three states

---

### Phase 5: Unit Tests (tests/test_unit_player_core.py)

Add 6 tests to `TestPlayerCoreLoop` class:

```python
def test_toggle_loop_three_state_cycle(self, player_core):
    """Verify OFF → LOOP ALL → REPEAT ONE → OFF cycle."""
    # Initial: OFF
    assert player_core.loop_enabled == False
    assert player_core.repeat_one == False
    
    # Click 1: LOOP ALL
    player_core.toggle_loop()
    assert player_core.loop_enabled == True
    assert player_core.repeat_one == False
    
    # Click 2: REPEAT ONE
    player_core.toggle_loop()
    assert player_core.loop_enabled == True
    assert player_core.repeat_one == True
    
    # Click 3: OFF
    player_core.toggle_loop()
    assert player_core.loop_enabled == False
    assert player_core.repeat_one == False

def test_repeat_one_plays_twice_then_advances(self, player_core, monkeypatch):
    """Verify track plays twice in 'once' mode."""
    monkeypatch.setattr('config.MT_REPEAT_ONE_MODE', 'once')
    player_core.repeat_one = True
    player_core.is_playing = True
    
    # Simulate track end - should repeat
    player_core._handle_track_end()
    assert player_core.repeat_one_count == 1
    
    # Simulate track end again - should advance
    player_core._handle_track_end()
    assert player_core.repeat_one_count == 0

def test_repeat_one_continuous_mode(self, player_core, monkeypatch):
    """Verify continuous repeat with MT_REPEAT_ONE_MODE=continuous."""
    monkeypatch.setattr('config.MT_REPEAT_ONE_MODE', 'continuous')
    player_core.repeat_one = True
    player_core.is_playing = True
    
    # Simulate track end multiple times - should always repeat
    for _ in range(5):
        player_core._handle_track_end()
        # Should still be playing same track

def test_repeat_counter_resets_on_next(self, player_core):
    """Verify counter resets when next_song() called."""
    player_core.repeat_one_count = 3
    player_core.next_song()
    assert player_core.repeat_one_count == 0

def test_repeat_counter_resets_on_previous(self, player_core):
    """Verify counter resets when previous_song() called."""
    player_core.repeat_one_count = 3
    player_core.previous_song()
    assert player_core.repeat_one_count == 0

def test_repeat_counter_resets_on_new_track(self, player_core):
    """Verify counter resets in _play_file()."""
    player_core.repeat_one_count = 3
    player_core._play_file('/path/to/track.mp3')
    assert player_core.repeat_one_count == 0
```

**Run tests:**
```bash
uv run pytest tests/test_unit_player_core.py::TestPlayerCoreLoop -v
```

---

### Phase 6: E2E Tests (tests/test_e2e_controls.py)

Add 2 integration tests:

```python
@pytest.mark.slow
def test_toggle_loop_three_states(api_client, clean_queue):
    """Test three-state loop cycling via API."""
    # Get initial state (should be OFF)
    status = api_client.send('get_status')
    assert status['data']['loop_enabled'] == False
    assert status['data']['repeat_one'] == False
    
    # Toggle to LOOP ALL
    response = api_client.send('toggle_loop')
    assert response['loop_enabled'] == True
    assert response['repeat_one'] == False
    
    # Toggle to REPEAT ONE
    response = api_client.send('toggle_loop')
    assert response['loop_enabled'] == True
    assert response['repeat_one'] == True
    
    # Toggle to OFF
    response = api_client.send('toggle_loop')
    assert response['loop_enabled'] == False
    assert response['repeat_one'] == False

@pytest.mark.slow
def test_repeat_one_playback(api_client, clean_queue, test_tracks):
    """Test actual repeat-one playback behavior."""
    # Add a short test track to queue
    api_client.send('add_tracks', {'tracks': [test_tracks[0]]})
    
    # Enable repeat-one mode
    api_client.send('toggle_loop')  # OFF → LOOP ALL
    api_client.send('toggle_loop')  # LOOP ALL → REPEAT ONE
    
    # Start playback
    api_client.send('play_pause')
    
    # Wait for track to end (use short test file)
    time.sleep(5)
    
    # Verify track repeated (check play count or current time reset)
    # Implementation depends on available API commands
```

**Run tests:**
```bash
uv run pytest tests/test_e2e_controls.py::test_toggle_loop_three_states -v
uv run pytest tests/test_e2e_controls.py::test_repeat_one_playback -v
```

---

### Phase 7: Visual Verification

**Manual testing steps:**

1. **Start app with repeater:**
```bash
pkill -f "python.*main.py" || true
sleep 2
nohup uv run repeater > /dev/null 2>&1 &
sleep 3  # Wait for app to fully load
```

2. **Take initial screenshot:**
```bash
# Use screencap MCP to capture app window
# Save to /tmp/mt-repeat-initial.png
```

3. **Test three-state cycling:**
- Click loop button once → Verify LOOP ALL icon displays
- Take screenshot → `/tmp/mt-repeat-loop-all.png`
- Click loop button again → Verify REPEAT ONE icon displays  
- Take screenshot → `/tmp/mt-repeat-one.png`
- Click loop button again → Verify OFF state (dimmed icon)
- Take screenshot → `/tmp/mt-repeat-off.png`

4. **Test repeat-one playback:**
- Add a short track to queue
- Enable REPEAT ONE mode
- Play track and observe it replays once then advances
- Check Eliot logs for repeat events:
```bash
# Look for: repeat_one_replay, repeat_one_advance
```

5. **Verify hover states:**
- Hover over loop button in each state
- Verify correct hover icon displays (teal tint)

**Expected visual results:**
- OFF: Gray repeat icon (50% opacity)
- LOOP ALL: Blue/teal repeat icon (100% opacity)
- REPEAT ONE: Blue/teal repeat-one icon with "1" symbol (100% opacity)
- Hover: Bright teal tint on current icon

---

### Phase 8: Update Backlog Task

**Final task update:**

```bash
# Mark all acceptance criteria complete
backlog task edit 003 --check-ac 1 --check-ac 2 --check-ac 3 --check-ac 4

# Set status to Done
backlog task edit 003 -s Done

# Add final notes
backlog task edit 003 --notes "Implementation completed across 8 phases with atomic commits.
All acceptance criteria met. See commit history for details: d3a6ee0, f736f4c, 662885e, + API/test commits."
```

---

## Quick Start for Next Session

```bash
# 1. Review current state
git log --oneline -5
backlog task 003 --plain

# 2. Continue with Phase 4 (API Integration)
# Edit api/server.py, api/examples/automation.py
# Test with: MT_API_SERVER_ENABLED=true uv run main.py

# 3. Move to Phase 5 (Unit Tests)
# Add tests to tests/test_unit_player_core.py
# Run: uv run pytest tests/test_unit_player_core.py::TestPlayerCoreLoop -v

# 4. Complete remaining phases sequentially
```

---

## Architecture Summary

**Three States:**
- State 0 (OFF): `loop_enabled=False, repeat_one=False`
- State 1 (LOOP ALL): `loop_enabled=True, repeat_one=False`
- State 2 (REPEAT ONE): `loop_enabled=True, repeat_one=True`

**Repeat Modes:**
- `MT_REPEAT_ONE_MODE='once'`: Track plays 2x (original + 1 repeat), then advances
- `MT_REPEAT_ONE_MODE='continuous'`: Track repeats indefinitely until mode changes

**Key Files Modified:**
- config.py: Icon paths, MT_REPEAT_ONE_MODE config
- core/db/preferences.py: Database get/set methods
- core/controls/player_core.py: State management, toggle logic, track end handling
- core/gui/player_controls.py: Icon loading, three-state button logic
- core/gui/progress_status.py: Pass-through parameter
- core/player/__init__.py: Initial state propagation
<!-- SECTION:NOTES:END -->
