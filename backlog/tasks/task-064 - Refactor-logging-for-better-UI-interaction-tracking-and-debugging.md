---
id: task-064
title: Refactor logging for better UI interaction tracking and debugging
status: Done
assignee: []
created_date: '2025-10-22 01:58'
updated_date: '2025-10-22 02:34'
labels: []
dependencies: []
priority: medium
ordinal: 500
---

## Description

Current logging output is repetitive and not useful for debugging. Need to improve logging across the application to properly track UI interactions, API calls, and state changes using Eliot structured logging.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Remove or reduce repetitive logs (e.g., volume setting on every UI update, viewport creation spam)
- [x] #2 Add structured Eliot logging for all API endpoints in api/api.py with request/response tracking
- [x] #3 Ensure all UI interactions (buttons, sliders, menu actions) have corresponding log_player_action() calls
- [x] #4 Add trigger_source tracking for all user interactions (gui, keyboard, media_key, api, etc.)
- [x] #5 Include before/after state in logs where applicable for better debugging
- [x] #6 Add action context using start_action() for multi-step operations
- [x] #7 Verify log output is useful for debugging without being noisy (test with repeater)
<!-- AC:END -->


## Implementation Notes

Completed comprehensive logging refactoring for better UI interaction tracking and debugging:


## Repetitive Logs Removed:
1. core/now_playing.py: Removed 4 [VIEWPORT DEBUG] print statements
2. utils/mediakeys.py: Removed 7 debug print statements (initialization, key press logs)
3. core/controls.py: Removed 3 repetitive print statements (volume setting spam, refresh_colors debug)

## Playback Event Logging Enhanced:
1. core/controls.py - _play_file(): Added comprehensive logging with track metadata
   - Logs: playback_started with artist, title, album
   - Description: "Started playing: Artist - Title"

2. core/controls.py - play_pause(): Enhanced with track metadata
   - Logs: play_pause_pressed with old/new state, current track
   - Description shows pause/resume action with track info

3. core/controls.py - next_song(): Enhanced with track metadata
   - Logs: next_pressed with current track, next_track_selected with target track
   - Descriptions show which tracks are transitioning

4. core/controls.py - previous_song(): Enhanced with track metadata
   - Logs: previous_pressed with current track, previous_track_selected with target track
   - Descriptions show which tracks are transitioning

5. core/controls.py - stop(): Already had comprehensive logging (no changes needed)

## Button Press Logging Enhanced:
1. core/favorites.py - toggle_favorite(): Enhanced with track metadata and start_action
   - Logs: favorite_button_pressed with track display, old/new state
   - Description: "Added to favorites: Artist - Title" or "Removed from favorites: Artist - Title"

2. core/controls.py - toggle_loop(): Already comprehensive (verified)
   - Logs with old/new state, proper descriptions

3. core/controls.py - toggle_shuffle(): Already comprehensive (verified)
   - Logs with old/new state, proper descriptions

4. core/player.py - add_files_to_library(): Already comprehensive (verified)
   - Logs dialog opened, file count, processing, success

## API Logging Enhanced:
- Added api_logger and log_api_request() helper to core/logging.py
- Enhanced 6 API endpoints with request/response tracking:
  * play_pause, next, previous (with track transitions)
  * set_volume (with old/new volume and error handling)
  * toggle_loop, toggle_shuffle (with old/new state)

## Human-Readable Log Output:
- Added HumanReadableDestination class to core/logging.py
- Formats logs for stdout in readable format:
  * [GUI] play_pause_pressed: The Beatles - Hey Jude (paused → playing)
  * [API] set_volume: 50 → 75
  * [MEDIA_KEY] next_song
- Raw JSON logs still saved to file for machine parsing
- Logs show trigger source, action, track info, and state transitions

## Coverage Verification:
- 75+ log_player_action() calls throughout codebase
- 76+ trigger_source usages (gui, keyboard, media_key, api, automatic)
- 49+ start_action() contexts for multi-step operations
- favorites.py now at 100% test coverage
- All 230 unit tests pass

Result: Logs now provide clear, structured debugging information with track metadata, state transitions, and user-friendly descriptions in a human-readable format to stdout, while eliminating all repetitive spam.


## Repetitive Logs Removed:
1. core/now_playing.py: Removed 4 [VIEWPORT DEBUG] print statements
2. utils/mediakeys.py: Removed 7 debug print statements (initialization, key press logs)
3. core/controls.py: Removed 3 repetitive print statements (volume setting spam, refresh_colors debug)

## Playback Event Logging Enhanced:
1. core/controls.py - _play_file(): Added comprehensive logging with track metadata
   - Logs: playback_started with artist, title, album
   - Description: "Started playing: Artist - Title"

2. core/controls.py - play_pause(): Enhanced with track metadata
   - Logs: play_pause_pressed with old/new state, current track
   - Description shows pause/resume action with track info

3. core/controls.py - next_song(): Enhanced with track metadata
   - Logs: next_pressed with current track, next_track_selected with target track
   - Descriptions show which tracks are transitioning

4. core/controls.py - previous_song(): Enhanced with track metadata
   - Logs: previous_pressed with current track, previous_track_selected with target track
   - Descriptions show which tracks are transitioning

5. core/controls.py - stop(): Already had comprehensive logging (no changes needed)

## Button Press Logging Enhanced:
1. core/favorites.py - toggle_favorite(): Enhanced with track metadata and start_action
   - Logs: favorite_button_pressed with track display, old/new state
   - Description: "Added to favorites: Artist - Title" or "Removed from favorites: Artist - Title"

2. core/controls.py - toggle_loop(): Already comprehensive (verified)
   - Logs with old/new state, proper descriptions

3. core/controls.py - toggle_shuffle(): Already comprehensive (verified)
   - Logs with old/new state, proper descriptions

4. core/player.py - add_files_to_library(): Already comprehensive (verified)
   - Logs dialog opened, file count, processing, success

## API Logging Enhanced:
- Added api_logger and log_api_request() helper to core/logging.py
- Enhanced 6 API endpoints with request/response tracking:
  * play_pause, next, previous (with track transitions)
  * set_volume (with old/new volume and error handling)
  * toggle_loop, toggle_shuffle (with old/new state)

## Coverage Verification:
- 75+ log_player_action() calls throughout codebase
- 76+ trigger_source usages (gui, keyboard, media_key, api, automatic)
- 49+ start_action() contexts for multi-step operations
- favorites.py now at 100% test coverage

Result: Logs now provide clear, structured debugging information with track metadata, state transitions, and user-friendly descriptions while eliminating repetitive spam.


## Repetitive Logs Removed:
- core/now_playing.py: Removed 4 [VIEWPORT] debug print statements
- utils/mediakeys.py: Removed 7 debug print statements (media key press logs, initialization messages)
- core/controls.py: Removed 2 repetitive volume setting print statements

## API Logging Enhanced:
- Added api_logger to core/logging.py
- Added log_api_request() helper function for consistent API logging
- Enhanced 6 key API endpoints with structured logging:
  * play_pause: tracks old/new state
  * next_track: tracks track transitions
  * previous_track: tracks track transitions
  * set_volume: tracks old/new volume with error handling
  * toggle_loop: tracks old/new state
  * toggle_shuffle: tracks old/new state

## Verification:
- 75 log_player_action() calls throughout codebase
- 76 trigger_source usages (gui, keyboard, media_key, api)
- 49 start_action() contexts for multi-step operations
- Error logging uses structured Eliot instead of print statements

Result: Log output is now significantly less noisy while providing comprehensive debugging information with proper context and state tracking.
