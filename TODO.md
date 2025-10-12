# TODO

**Table of Contents**
* [TODO](#todo)
  * [High priority bug fixes](#high-priority-bug-fixes)
    * [Fix Controls Resizing (task-041)](#fix-controls-resizing-task-041)
    * [Fix Shuffle Randomness (task-042)](#fix-shuffle-randomness-task-042)
    * [Fix Progress Jumping (task-043)](#fix-progress-jumping-task-043)
    * [Fix Playing Track Highlight (task-044)](#fix-playing-track-highlight-task-044)
  * [Major feature additions](#major-feature-additions)
    * [Queue Next Feature (task-045)](#queue-next-feature-task-045)
    * [Settings Menu (task-046)](#settings-menu-task-046)
    * [Metadata Editing (task-047)](#metadata-editing-task-047)
  * [Everything else](#everything-else)
    * [Repeat Functionality (task-003)](#repeat-functionality-task-003)
    * [Arrow Key Navigation (task-004)](#arrow-key-navigation-task-004)
    * [Playlist Management (task-006)](#playlist-management-task-006)
    * [Last.fm Scrobbling (task-007)](#lastfm-scrobbling-task-007)
    * [Mobile Remote Control (task-008)](#mobile-remote-control-task-008)
    * [Cross-platform Support (task-009)](#cross-platform-support-task-009)
    * [Lyrics Feature (task-010)](#lyrics-feature-task-010)
    * [Performance Optimizations (task-012)](#performance-optimizations-task-012)
    * [VLC Logging Suppression (task-013)](#vlc-logging-suppression-task-013)
    * [Unit Tests (task-015)](#unit-tests-task-015)
    * [Integration Tests (task-016)](#integration-tests-task-016)
    * [E2E Tests (task-017)](#e2e-tests-task-017)
    * [Task Runners (task-018)](#task-runners-task-018)
    * [macOS/Linux Packaging (task-019)](#macoslinux-packaging-task-019)
    * [Windows Packaging (task-020)](#windows-packaging-task-020)
    * [Code Signing (task-021)](#code-signing-task-021)

## High priority bug fixes

### Fix Controls Resizing (task-041)

* Playback and utility controls move when resizing window

### Fix Shuffle Randomness (task-042)

* Shuffle order not being random and looping through a subset of available tracks

### Fix Progress Jumping (task-043)

* Manual jumping across track progress isn't precise
  * e.g., click 1:00 mark, it goes to 0:40 instead
  * First click works, subsequent don't
    * Possible vlc regression with time tracking being manipulated during playback

### Fix Playing Track Highlight (task-044)

* Cyan highlight of playing track
  * Currently same grey as manual track selection

## Major feature additions

### Queue Next Feature (task-045)

* Queue Next functionality (Cmd-D and Right click > Queue next)

### Settings Menu (task-046)

* Settings Menu with comprehensive sections (General, Appearance, Shortcuts, Now Playing, Library, Advanced)

### Metadata Editing (task-047)

* Inline metadata editing using mutagen

## Everything else

### Repeat Functionality (task-003)

* Repeat (1, all)

### Arrow Key Navigation (task-004)

* arrow keys
  * playhead navigation

### Playlist Management (task-006)

* playlists
  * **[task-035]** recently added
  * **[task-036]** recently played

### Last.fm Scrobbling (task-007)

* last.fm scrobbling

### Mobile Remote Control (task-008)

* mobile remote control

### Cross-platform Support (task-009)

* Cross-platform
  * linux
    * ubuntu/wsl
    * windows (maybe)

### Lyrics Feature (task-010)

* Lyrics + CC/Wiki artist background
* lyrics
  * see fas
* iTunes genius-style feature
* adjustable fade
* UI
  * Add genre, time columns
  * Light/Dark theme
  * Generate a diagram of the frontend and add to llm instructions
  * Snap columns w/double click based on total width of int/str
* UX
  * ~~Standardize utility button sizes~~
    * loop, shuffle, add
  * Combine loop buttons
    * Loop one track (1)
    * Loop all
    * Off

### Performance Optimizations (task-012)

* performance
  * faster directory traversal (i.e., zig)
    * Aside from scanning, add file paths to db
    * Log the amount of time it takes to add files to the library
    * mutagen tag reading might need to be optimized for large libraries as well
  * sqlite vs. ~~duckdb~~
    * terso
  * network caching / buffer / prefetch
  * Check for updates on startup
* Miscellaneous

### VLC Logging Suppression (task-013)

* Suppress python-vlc output in favor of eliot logging

* Rotate logs after 5 days
* Parameterize log_level, log_file, and stdout vs. file
* Testing

### Unit Tests (task-015)

* unit tests

### Integration Tests (task-016)

* integration tests

### E2E Tests (task-017)

* e2e tests
  * [askui](https://docs.askui.com/01-tutorials/tutorials-overview)
* Build

### Task Runners (task-018)

* task runners

### macOS/Linux Packaging (task-019)

* package for macos and linux
  * tkinter initially
  * ~~tauri once migrated to web app~~

### Windows Packaging (task-020)

* windows (eventually)
* CI/CD

### Code Signing (task-021)

* codesigning
