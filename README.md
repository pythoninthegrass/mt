# mt

`mt` is a simple desktop music player designed for large music collections.

<!-- TODO: minimum requirements -->
<!-- TODO: setup -->
<!-- TODO: dev -->
<!-- TODO: install -->

## TODO

* UI
  * better, modern styling
    * Use font awesome (fas) icons
  * ~~split panes~~
  * ~~app icon~~
* UX
  * ~~end of library loopback (w/o prev/next)~~
  * performance
    * faster directory traversal
    * sqlite vs. duckdb
    * network caching / buffer / prefetch
* Features
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
