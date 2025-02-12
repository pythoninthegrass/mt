# mt

`mt` is a simple desktop music player designed for large music collections.

<!-- TODO: minimum requirements -->
<!-- TODO: setup -->
<!-- TODO: dev -->
<!-- TODO: install -->

## TODO

* UI
  * better, modern styling
  * split panes
* UX
  * performance
    * faster directory traversal
    * sqlite vs. duckdb
    * network caching / buffer / prefetch
* Features 
  * read ID3 tags
  * media keys
  * shuffle
  * repeat (1, all)
  * search
    * search form
    * dynamic fuzzy search by artist
  * dynamic queue order
  * last.fm scrobbling
  * lyrics
  * volume control
  * playlists
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
  * linting/formatting
