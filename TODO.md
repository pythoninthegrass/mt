# TODO

* UI
  * better, modern styling
    * check out [basecoatui](https://basecoatui.com/)
    * use font awesome (fas) icons
  * ~~split panes~~
  * ~~app icon~~
  * Adjustable column widths
* UX
  * ~~end of library loopback (w/o prev/next)~~
  * performance
    * faster directory traversal
    * sqlite vs. duckdb
    * network caching / buffer / prefetch
* Features
  * Cross-platform
    * ~~macos~~/linux
      * ubuntu/wsl
    * windows (maybe)
  * ~~read ID3 tags~~
  * ~~media keys~~
  * arrow keys
    * playhead navigation
  * shuffle
  * repeat (1, all)
  * search
    * search form
    * dynamic fuzzy search by artist
  * dynamic queue order
  * ~~library~~
    * ~~deduplication~~
  * last.fm scrobbling
  * mobile remote control
  * lyrics
  * ~~volume control~~
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
  * ~~linting/formatting~~
  * codesigning
