# mt

`mt` is a simple desktop music player designed for large music collections.

<!-- TODO: minimum requirements -->
<!-- TODO: setup -->
<!-- TODO: dev -->
<!-- TODO: install -->

## TODO

* DX
  * add mcp for github and browser-use
  * flet context
* UI
  * better, modern styling
    * Use font awesome (fas) icons
* UX
  * looping
    * ~~end of library loopback (w/o prev/next)~~
    * dedicated loop button
  * performance
    * go / zig / mojo bindings
    * faster directory traversal
    * sqlite vs. duckdb
    * network caching / buffer / prefetch
* Features
  * media keys
  * arrow keys
    * playhead navigation
  * shuffle
  * repeat (1, all)
  * search
    * search form
    * dynamic fuzzy search by artist
  * dynamic queue order
  * library
    * deduplication
  * last.fm scrobbling
  * lyrics
  * now playing (queue)
  * playlists
    * recently added
    * recently played
    * top 25 most played
  * mobile remote control
  * secret sauce 💸
* Testing
  * unit tests
  * integration tests
  * e2e tests
* Build
  * task runners
  * package for macos and linux
    * ~~tkinter initially~~
    * ~~tauri~~ flet once migrated to web app
  * windows (eventually)
* CI/CD
  * pre-commit hooks
  * codesigning
