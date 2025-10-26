# TODO

**Table of Contents**

* [TODO](#todo)
  * [Miscellaneous](#miscellaneous)
  * [High priority bug fixes](#high-priority-bug-fixes)
    * [Fix Playing Track Highlight (task-044)](#fix-playing-track-highlight-task-044)
    * [Fix Context Menu Highlight (task-058)](#fix-context-menu-highlight-task-058)
  * [Major feature additions](#major-feature-additions)
    * [Settings Menu (task-046)](#settings-menu-task-046)
  * [Everything else](#everything-else)
    * [Repeat Functionality (task-003)](#repeat-functionality-task-003)
    * [Arrow Key Navigation (task-004)](#arrow-key-navigation-task-004)
    * [Playlist Management (task-006)](#playlist-management-task-006)
    * [Last.fm Scrobbling (task-007)](#lastfm-scrobbling-task-007)
    * [Mobile Remote Control (task-008)](#mobile-remote-control-task-008)
    * [Cross-platform Support (task-009)](#cross-platform-support-task-009)
    * [Performance Optimizations (task-012)](#performance-optimizations-task-012)
    * [Task Runners (task-018)](#task-runners-task-018)
    * [macOS/Linux Packaging (task-019)](#macoslinux-packaging-task-019)
    * [Windows Packaging (task-020)](#windows-packaging-task-020)
    * [Code Signing (task-021)](#code-signing-task-021)

## Miscellaneous

* Change stats font to monospace

## High priority bug fixes

### Fix Playing Track Highlight (task-044)

* Cyan highlight of playing track
  * Currently same grey as manual track selection

### Fix Context Menu Highlight (task-058)

* Context menu highlight should use theme primary color

## Major feature additions

### Settings Menu (task-046)

* Settings Menu with comprehensive sections (General, Appearance, Shortcuts, Now Playing, Library, Advanced)

## Everything else

### Repeat Functionality (task-003)

* Repeat (1, all)

### Arrow Key Navigation (task-004)

* arrow keys
  * playhead navigation

### Playlist Management (task-006)

* Additional playlist functionality (core playlists completed)

### Last.fm Scrobbling (task-007)

* last.fm scrobbling

### Mobile Remote Control (task-008)

* mobile remote control

### Cross-platform Support (task-009)

* Cross-platform
  * linux
    * ubuntu/wsl
    * windows (maybe)

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
