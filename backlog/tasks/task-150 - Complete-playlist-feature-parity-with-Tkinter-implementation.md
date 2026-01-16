---
id: task-150
title: Complete playlist feature parity with Tkinter implementation
status: In Progress
assignee: []
created_date: '2026-01-16 06:38'
updated_date: '2026-01-16 08:22'
labels:
  - ui
  - playlists
  - tauri-migration
  - ux
milestone: Tauri Migration
dependencies:
  - task-147
priority: medium
ordinal: 500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Tauri UI playlist implementation (task-147) covers basic CRUD but is missing several UX features from the original Tkinter spec (task-006, docs/custom-playlists.md).

## Current State (as of 2026-01-16)

**CRITICAL BUGS BLOCKING COMPLETION:**

### Bug 1: Track Context Menu Translucency
The library track context menu is extremely translucent, making it nearly unreadable. The underlying track list text shows through the menu background. This blocks testing of AC#3-8 in the browser.

**Root cause:** The `.context-menu` CSS class uses `background: hsl(var(--background))` but renders with high transparency. The column header context menu uses `bg-card` class and is opaque.

**Fix needed:** Change track context menu styling to match column header context menu (use `bg-card` or equivalent opaque background).

**Files:** `app/frontend/index.html` lines 36-73 (`.context-menu` CSS) and lines 588-651 (track context menu HTML)

### Bug 2: Playlist List Not Synced to Library Browser
The "Add to Playlist" submenu shows "No playlists yet" even when playlists exist in the sidebar.

**Root cause:** `libraryBrowser.playlists` is loaded on init and on `mt:playlists-updated` event, but the sidebar's `createPlaylist()` method does NOT dispatch this event after creating a playlist. The sidebar updates its own list but doesn't notify libraryBrowser.

**Fix needed:** In `sidebar.js`, dispatch `mt:playlists-updated` after `loadPlaylists()` completes in `createPlaylist()`.

**Files:** `app/frontend/js/components/sidebar.js` line 133 area

### Bug 3: Playlist View Data Shape Mismatch (CRITICAL)
When viewing a playlist, tracks show "Unknown title/artist" and blank album/time. Playback also fails.

**Root cause:** Backend `GET /api/playlists/{id}` returns playlist items shaped as:
```json
{ "tracks": [{ "position": 0, "added_date": "...", "track": { "id": 1, "title": "...", "artist": "...", ... } }] }
```

But `library.js` does:
```js
this.tracks = data.tracks || [];
```

This assigns the playlist item objects (with nested `track` property) directly to `this.tracks`. The UI then tries to access `track.title`, `track.artist`, etc. on the playlist item object, which doesn't have those properties at the top level.

**Fix needed:** In `library.js` `loadPlaylist()`, extract the nested track objects:
```js
this.tracks = (data.tracks || []).map(item => item.track || item);
```

**Files:** `app/frontend/js/stores/library.js` lines 116-131

### Bug 4: API Endpoint Mismatches

**4a. Reorder endpoint mismatch:**
- Backend: `POST /api/playlists/{id}/tracks/reorder` expects `{from_position, to_position}`
- Frontend `api.playlists.reorder()`: calls `/playlists/{id}/reorder` with `{track_ids: [...]}`

**Fix needed:** Update `api.js` to call correct endpoint with correct payload shape.

**Files:** `app/frontend/js/api.js` lines 417-422, `backend/routes/playlists.py` lines 118-131

**4b. Remove track endpoint missing:**
- `removeFromPlaylist()` in library-browser.js calls `api.playlists.removeTrack(playlistId, position)`
- But `api.js` only has `removeTracks()` which uses a different endpoint/shape

**Fix needed:** Add `removeTrack(playlistId, position)` to `api.js` that calls `DELETE /api/playlists/{id}/tracks/{position}`.

**Files:** `app/frontend/js/api.js` (add new method), `app/frontend/js/components/library-browser.js` line 1099

### Bug 5: Playlist Delete Confirmation Broken in Tauri
The delete playlist confirmation uses browser `confirm()` which doesn't work properly in Tauri webview.

**Root cause:** `sidebar.js` line 299 uses `confirm()` instead of Tauri's async dialog.

**Fix needed:** Use `window.__TAURI__?.dialog?.confirm()` with fallback to browser confirm, similar to how `removeSelected()` in library-browser.js does it.

**Files:** `app/frontend/js/components/sidebar.js` lines 296-317

### Bug 6: Unique Name Format Mismatch
Backend generates "New playlist 2" but spec says "New playlist (2)".

**Files:** `backend/services/database.py` `generate_unique_playlist_name()` method

## Missing Features

### 1. Inline Rename (UX improvement)
- Current: Uses browser `prompt()` for create/rename
- Spec: Entry overlay positioned via element bounds, pre-filled with auto-generated unique name
- Auto-unique naming: "New playlist", "New playlist (2)", etc.

### 2. Add Tracks to Playlist
- "Add to playlist" submenu in library track context menu
- Dynamically populated with all custom playlists
- Adds selected tracks to chosen playlist via API

### 3. Drag-and-Drop to Sidebar
- Drag tracks from library view to sidebar playlist names
- Visual feedback: highlight playlist row when hovering with dragged tracks
- Drop adds tracks to that playlist

### 4. Drag-Reorder Within Playlist
- When viewing a playlist, drag tracks to reorder
- Persist new order via `api.playlists.reorder()`

### 5. Playlist View Delete Semantics
- Delete key in playlist view removes from playlist only (not library)
- "Remove from playlist" context menu option
- "Remove from library" as separate destructive option

## Files to Modify
- `app/frontend/index.html` - Context menu styling fix, markup for submenu
- `app/frontend/js/components/sidebar.js` - Inline rename, auto-unique naming, drag highlight, event dispatch, Tauri dialog
- `app/frontend/js/components/library-browser.js` - Add to playlist menu, drag-to-sidebar, reorder, delete semantics
- `app/frontend/js/stores/library.js` - Fix playlist data shape extraction
- `app/frontend/js/api.js` - Fix reorder endpoint, add removeTrack method
- `backend/services/database.py` - Fix unique name format

## Reference
- Original spec: docs/custom-playlists.md
- Tkinter implementation: task-006 (completed on main branch)
- Current Tauri implementation: task-147
- Screenshot showing bugs: /Users/lance/Desktop/mt_lib_ctx.png
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create playlist auto-generates unique name ("New playlist", "New playlist (2)", etc.)
- [ ] #2 Inline rename overlay for playlist creation and rename (not browser prompt)
- [ ] #3 "Add to playlist" submenu in library track context menu with all custom playlists
- [ ] #4 Drag tracks from library to sidebar playlist adds them to that playlist
- [ ] #5 Visual feedback (highlight) when dragging tracks over sidebar playlists
- [ ] #6 Drag-reorder tracks within playlist view persists via API
- [ ] #7 Delete key in playlist view removes from playlist only (not library)
- [ ] #8 "Remove from playlist" context menu option in playlist view
- [ ] #9 Playwright tests cover: add to playlist menu, drag-to-sidebar, reorder, remove from playlist
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Phase 1: Fix Blocking Bugs (Required before AC verification)

#### Step 1.1: Fix Track Context Menu Styling
**Priority: HIGH (blocks all testing)**

In `app/frontend/index.html`, update the track context menu to use opaque styling like the column header menu:

1. Find the track context menu div (line ~588-620):
```html
<div 
  x-show="contextMenu" 
  x-cloak
  class="context-menu track-context-menu"
```

2. Change to use `bg-card` class instead of relying on `.context-menu` CSS:
```html
<div 
  x-show="contextMenu" 
  x-cloak
  class="fixed z-100 min-w-45 border border-border rounded-lg shadow-lg p-1 bg-card"
```

3. Also update the playlist submenu (line ~622-651) with same styling.

4. Optionally update `.context-menu` CSS (lines 36-73) to use `bg-card` or add explicit opacity.

#### Step 1.2: Fix Playlist List Sync
**Priority: HIGH (blocks AC#3)**

In `app/frontend/js/components/sidebar.js`, after creating a playlist, dispatch the update event:

```js
async createPlaylist() {
  try {
    const { name: uniqueName } = await api.playlists.generateName();
    const playlist = await api.playlists.create(uniqueName);
    await this.loadPlaylists();
    
    // ADD THIS LINE - notify libraryBrowser to refresh its playlist list
    window.dispatchEvent(new CustomEvent('mt:playlists-updated'));
    
    const newPlaylist = this.playlists.find(p => p.playlistId === playlist.id);
    // ...
  }
}
```

#### Step 1.3: Fix Playlist View Data Shape
**Priority: CRITICAL (blocks playback and metadata display)**

In `app/frontend/js/stores/library.js`, update `loadPlaylist()`:

```js
async loadPlaylist(playlistId) {
  this.loading = true;
  try {
    const data = await api.playlists.get(playlistId);
    // Extract nested track objects from playlist items
    this.tracks = (data.tracks || []).map(item => item.track || item);
    this.totalTracks = this.tracks.length;
    this.totalDuration = this.tracks.reduce((sum, t) => sum + (t.duration || 0), 0);
    this.applyFilters();
    return data;
  } catch (error) {
    console.error('Failed to load playlist:', error);
    return null;
  } finally {
    this.loading = false;
  }
}
```

#### Step 1.4: Fix API Endpoint Mismatches
**Priority: HIGH (blocks AC#6, #7, #8)**

In `app/frontend/js/api.js`:

1. Fix `reorder()` method (lines 417-422):
```js
async reorder(playlistId, fromPosition, toPosition) {
  return request(`/playlists/${playlistId}/tracks/reorder`, {
    method: 'POST',
    body: JSON.stringify({ from_position: fromPosition, to_position: toPosition }),
  });
},
```

2. Add `removeTrack()` method:
```js
async removeTrack(playlistId, position) {
  return request(`/playlists/${playlistId}/tracks/${position}`, {
    method: 'DELETE',
  });
},
```

3. Update callers in `library-browser.js` to use correct method signatures.

#### Step 1.5: Fix Playlist Delete Confirmation
**Priority: MEDIUM**

In `app/frontend/js/components/sidebar.js`, update `deletePlaylist()`:

```js
async deletePlaylist() {
  if (!this.contextMenuPlaylist) return;
  
  const playlistName = this.contextMenuPlaylist.name;
  
  const confirmed = await window.__TAURI__?.dialog?.confirm(
    `Delete playlist "${playlistName}"?`,
    { title: 'Delete Playlist', kind: 'warning' }
  ) ?? window.confirm(`Delete playlist "${playlistName}"?`);
  
  if (!confirmed) {
    this.hidePlaylistContextMenu();
    return;
  }
  // ... rest of delete logic
}
```

#### Step 1.6: Fix Unique Name Format (Optional)
**Priority: LOW**

In `backend/services/database.py`, update `generate_unique_playlist_name()`:
```python
candidate = f"{base} ({suffix})"  # Instead of f"{base} {suffix}"
```

### Phase 2: Verify/Complete ACs

After Phase 1 fixes, verify each AC works end-to-end:

- AC#1: Test create playlist generates unique names
- AC#2: Test inline rename works (sidebar already has this)
- AC#3: Test "Add to Playlist" submenu shows all playlists
- AC#4: Test drag from library to sidebar playlist
- AC#5: Test visual highlight on drag over
- AC#6: Test drag reorder within playlist persists
- AC#7: Test Delete key in playlist view
- AC#8: Test "Remove from playlist" context menu
- AC#9: Update/verify Playwright tests

### Phase 3: Rebuild and Test

1. Rebuild PEX sidecar: `task pex:build --force`
2. Restart Tauri dev: `task tauri:dev`
3. Manual verification in Tauri
4. Run Playwright tests: `npx playwright test tests/sidebar.spec.js tests/library.spec.js`
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Session Notes (2026-01-16)

### Commits Made
- `657eff3` feat(playlist): complete playlist feature parity with Tkinter (task-150)
  - Added generate-name endpoint to backend
  - Added generate_unique_playlist_name method to DatabaseService
  - Implemented inline rename overlay for sidebar
  - Added drag handlers and context menu markup
  - Added Playwright tests

### What Was Attempted vs What Actually Works

**Attempted:** Full implementation of all 9 ACs
**Reality:** Multiple critical bugs prevent ACs from working end-to-end

### Key Findings from Manual Testing

1. **Screenshot evidence** (`/Users/lance/Desktop/mt_lib_ctx.png`):
   - Track context menu is extremely translucent (unreadable)
   - "Add to Playlist" submenu shows "No playlists yet" despite sidebar showing "Test" playlist
   - This proves playlist list sync is broken between sidebar and libraryBrowser

2. **User reported in Tauri:**
   - Was able to add track to playlist (powered through translucency)
   - Track appeared in playlist with "Unknown title/artist" and blank metadata
   - Playback doesn't work
   - Delete confirmation dialog doesn't wait for user response

### Root Causes Identified

1. **Translucency:** `.context-menu` CSS uses `hsl(var(--background))` which renders transparent. Column header menu uses `bg-card` and is opaque.

2. **Playlist sync:** Sidebar `createPlaylist()` doesn't dispatch `mt:playlists-updated` event after creating playlist.

3. **Data shape:** Backend returns `{ tracks: [{ position, track: {...} }] }` but frontend assigns directly to `this.tracks` without extracting nested `track` objects.

4. **API mismatches:**
   - Reorder: frontend calls wrong endpoint with wrong payload
   - RemoveTrack: method doesn't exist in api.js

5. **Tauri dialog:** Uses sync `confirm()` instead of async Tauri dialog

### Files That Need Changes

| File | Changes Needed |
|------|----------------|
| `app/frontend/index.html` | Fix context menu styling (use bg-card) |
| `app/frontend/js/components/sidebar.js` | Dispatch event after create, use Tauri dialog for delete |
| `app/frontend/js/stores/library.js` | Extract nested track objects in loadPlaylist() |
| `app/frontend/js/api.js` | Fix reorder(), add removeTrack() |
| `app/frontend/js/components/library-browser.js` | Update reorder/remove calls to use correct API |
| `backend/services/database.py` | Optional: fix name format to use parentheses |

### Testing Notes

- Playwright tests exist but don't catch these bugs because:
  - Tests use mocked data that matches expected shape
  - Tests don't verify actual API integration
  - Some tests have fixture issues (expect "Test Playlist 1/2" that don't exist)

- Manual testing in Tauri is required to verify fixes

### Next Agent Instructions

1. **Start with Bug 1 (translucency)** - this unblocks browser testing
2. **Then Bug 2 (playlist sync)** - this unblocks AC#3 verification
3. **Then Bug 3 (data shape)** - this unblocks playback and metadata
4. **Then Bug 4 (API)** - this unblocks AC#6, #7, #8
5. **Then Bug 5 (dialog)** - this fixes Tauri UX
6. After all bugs fixed, rebuild PEX and verify in Tauri
7. Update Playwright tests if needed
<!-- SECTION:NOTES:END -->
