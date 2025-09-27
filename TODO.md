# TODO

* Features
  * search
    * search form
    * dynamic fuzzy search by artist
  * repeat (1, all)
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
* UI
  * better, modern styling
    * check out [basecoatui](https://basecoatui.com/)
    * use font awesome (fas) icons
* Testing
  * unit tests
  * integration tests
  * e2e tests
* Build
  * task runners
  * package for macos and linux
    * tkinter initially
    * tauri once migrated to web app
  * windows (eventually)
* CI/CD
  * ~~pre-commit hooks~~
  * codesigning
