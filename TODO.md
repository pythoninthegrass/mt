# TODO

* Miscellaneous
  * Fix manual tracking causing repeated bars
    ```bash
    Current playing filepath: /Users/lance/Desktop/mt/music/01 Strobe.m4a
    Playing colors - bg: #00343a, fg: #33eeff
    Found playing item: 01 Strobe by Unknown Artist
    Correcting seek: VLC at 328.25s, target 326.35s
    Correcting seek: VLC at 401.59s, target 400.94s
    ```
* UI
  * better, modern styling
    * check out [basecoatui](https://basecoatui.com/)
    * use font awesome (fas) icons
  * Adjustable column widths
* UX
  * performance
    * faster directory traversal
    * sqlite vs. duckdb
    * network caching / buffer / prefetch
* Features
  * Cross-platform
    * linux
      * ubuntu/wsl
    * windows (maybe)
  * arrow keys
    * playhead navigation
  * shuffle
  * repeat (1, all)
  * search
    * search form
    * dynamic fuzzy search by artist
  * dynamic queue order
  * last.fm scrobbling
  * mobile remote control
  * lyrics
    * see fas
  * now playing (queue)
  * playlists
    * recently added
    * recently played
    * top 25 most played
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
  * pre-commit hooks
  * codesigning
