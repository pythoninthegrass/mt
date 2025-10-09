# TODO

* Fix
  * ~~Reduce horizontal padding between utility controls~~
  * ~~Grey background on volume icon~~
  * Manual jumping across track progress isn't precise
    * e.g., click 1:00 mark, it goes to 0:40 instead
    * First click works, subsequent don't
      * Possible vlc regression with time tracking being manipulated during playback
  * Shuffle order not being random and looping through a subset of avaiable tracks
  * Cyan highlight of playing track
    * Currently same grey as manual track selection
* Features
  * ~~search~~
    * ~~search form~~
    * ~~dynamic fuzzy search by artist~~
  * repeat (1, all)
  * adjustable fade
  * arrow keys
    * playhead navigation
  * dynamic queue order
  * playlists
    * recently added
    * recently played
    * top 25 most played
  * last.fm scrobbling
  * mobile remote control
  * Cross-platform
    * linux
      * ubuntu/wsl
    * windows (maybe)
  * lyrics
    * see fas
  * now playing (queue)
* UI
  * Shrink stoplight buttons to match system styling
  * Add genre and time columns
  * better, modern styling
    * ~~check out [basecoatui](https://basecoatui.com/)~~
    * ~~use font awesome (fas) icons~~
* UX
  * Standardize utility button sizes
    * loop, shuffle, add
  * Combine loop buttons
    * Loop one track (1)
    * Loop all
    * Off
  * performance
    * faster directory traversal (i.e., zig)
      * Aside from scanning, add file paths to db
      * mutagen tag reading might need to be optimized for large libraries as well
    * sqlite vs. ~~duckdb~~
      * terso
    * network caching / buffer / prefetch
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
    * tauri once migrated to web app
  * windows (eventually)
* CI/CD
  * ~~pre-commit hooks~~
  * codesigning
