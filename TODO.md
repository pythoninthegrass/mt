# TODO

* Fix
  * ~~Changing window size via maximize (button, top bar) resizes columns~~
  * Menu bar name/PID
    * python3 > `mt`
  * Shuffle order not being random and looping through a subset of available tracks
  * Manual jumping across track progress isn't precise
    * e.g., click 1:00 mark, it goes to 0:40 instead
    * First click works, subsequent don't
      * Possible vlc regression with time tracking being manipulated during playback
  * Cyan highlight of playing track
    * Currently same grey as manual track selection
* Features
  * Queue
    * Next
      * Cmd-D
      * Right click > Queue next
    * Dynamic queue order
  * Inline metadata editing (mutagen)
  * Settings Menu
    * cf. TyCal
    * Cog / Cmd-,
      * General
      * Appearance
      * Shortcuts
      * Now Playing
      * Library
      * Advanced
        * App Info
          * Version
          * Build
          * OS (macOS version/build)
        * Maintenance
          * Reset all settings
          * Capture logs as zip on desktop
  * Repeat (1, all)
  * iTunes genius-style feature
  * adjustable fade
  * arrow keys
    * playhead navigation
  * playlists
    * recently added
    * recently played
  * last.fm scrobbling
  * Lyrics + CC/Wiki artist background
  * mobile remote control
  * Cross-platform
    * linux
      * ubuntu/wsl
    * windows (maybe)
  * lyrics
    * see fas
  * now playing (queue)
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
  * Suppress python-vlc output in favor of eliot logging
  * Rotate logs after 5 days
  * Parameterize log_level, log_file, and stdout vs. file
* Testing
  * unit tests
  * integration tests
  * e2e tests
    * [askui](https://docs.askui.com/01-tutorials/tutorials-overview)
* Build
  * task runners
  * package for macos and linux
    * tkinter initially
    * ~~tauri once migrated to web app~~
  * windows (eventually)
* CI/CD
  * codesigning
