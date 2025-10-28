---
id: task-003
title: Implement repeat functionality
status: In Progress
assignee: []
created_date: '2025-09-17 04:10'
updated_date: '2025-10-28 02:33'
labels: []
dependencies: []
ordinal: 9000
---

## Description

Add repeat modes for single track and ~~all tracks~~ (latter technically exists with loop button)

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Add repeat toggle button to player controls
- [ ] #2 Implement repeat-one mode
- [ ] #3 Update UI to show current repeat state
- [ ] #4 Test repeat functionality with different queue states
<!-- AC:END -->


## Implementation Plan

- Use repeat_one.png image in place of the loop utility control when pressed a second time.
  - e.g., loop OFF > ON > REPEAT 1 > track either repeats once or user clicks REPEAT 1 to circle back to loop OFF


## Implementation Notes

## Implementation Status: PHASE 3 COMPLETED ✅

### Completed Phases (3 commits):

**Phase 1: Core State Management** ✅ (commit d3a6ee0)
- Added `BUTTON_SYMBOLS['repeat_one'] = 'static/repeat_one.png'` to config.py
- Added `MT_REPEAT_ONE_MODE = config('MT_REPEAT_ONE_MODE', default='once')`
- Implemented `get_repeat_one() -> bool` and `set_repeat_one(enabled: bool)` in PreferencesManager (core/db/preferences.py)
- Added facade methods in MusicDatabase (core/db/database.py)

**Phase 2: Player Logic** ✅ (commit f736f4c)
- Added state variables in PlayerCore.__init__:
  - `self.repeat_one = self.db.get_repeat_one()`
  - `self.repeat_one_count = 0`
- Implemented three-state toggle_loop() cycling: OFF → LOOP ALL → REPEAT ONE → OFF
- Added repeat-one logic in _handle_track_end():
  - `MT_REPEAT_ONE_MODE='once'`: track plays twice then advances
  - `MT_REPEAT_ONE_MODE='continuous'`: track repeats indefinitely
  - Comprehensive Eliot logging for all transitions
- Reset `repeat_one_count = 0` in:
  - `_play_file()`: when starting new track
  - `next_song()`: when manually advancing
  - `previous_song()`: when manually going back
- Updated `update_loop_button_color()` callback signature to `(new_loop, new_repeat_one)`

**Phase 3: UI Updates** ✅ (commit 662885e)
- Added `initial_repeat_one` parameter to:
  - PlayerControls.__init__
  - ProgressBar.__init__  
  - MusicPlayer (passed as `initial_repeat_one=self.player_core.repeat_one`)
- Loaded repeat_one icon variants in setup_utility_controls():
  - `repeat_one_enabled`: 100% opacity with loop_enabled tint
  - `repeat_one_hover`: 100% opacity with primary color tint
- Updated initial button image selection (lines 135-141):
  - Checks `if self.repeat_one` → use repeat_one icon
  - Else `if self.loop_enabled` → use loop_enabled icon
  - Else → use loop_disabled icon
- Modified hover/leave handlers (lines 150-160):
  - Enter: Shows `repeat_one_hover` if repeat_one, else `loop_hover`
  - Leave: Shows `repeat_one_enabled` if repeat_one, else `loop_enabled` if loop_enabled, else `loop_disabled`
- Updated `update_loop_button_color(loop_enabled, repeat_one)` method:
  - Updates internal state
  - Selects correct icon based on three states
  - Calls `self.loop_button.configure(image=icon)`

---

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
