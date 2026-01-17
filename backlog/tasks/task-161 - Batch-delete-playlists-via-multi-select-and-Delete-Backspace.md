---
id: task-161
title: Batch delete playlists via multi-select and Delete/Backspace
status: Done
assignee: []
created_date: '2026-01-17 04:35'
updated_date: '2026-01-17 04:38'
labels:
  - ui
  - playlists
  - ux
milestone: Tauri Migration
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add multi-select behavior to sidebar playlists and support batch deletion using keyboard (Delete/Backspace).

**Selection behavior:**
- Cmd/Ctrl-click toggles playlist selection without navigating to it
- Shift-click selects a contiguous range from the last anchor to clicked playlist
- Regular click (no modifier) clears selection and navigates as usual

**Deletion behavior:**
- Delete/Backspace while playlist list is focused triggers confirmation dialog
- Uses same confirmation UX as current single-playlist context menu delete (Tauri dialog with browser fallback)
- If confirmed, all selected playlists are deleted via API, sidebar updates, selection clears
- If canceled, nothing changes
- Delete/Backspace is ignored while inline rename input is focused
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Cmd/Ctrl-click on a playlist toggles it in selection without clearing other selections or navigating
- [x] #2 Shift-click selects contiguous range from last anchor to clicked playlist
- [x] #3 Selected playlists have distinct visual state from active/hover states
- [x] #4 Delete/Backspace while playlist list focused shows confirmation dialog
- [x] #5 Confirmation uses same UX as single-playlist delete (Tauri dialog with browser fallback)
- [x] #6 Confirmed deletion removes all selected playlists via API and updates sidebar
- [x] #7 Canceled deletion leaves playlists and selection unchanged
- [x] #8 Delete/Backspace ignored while inline rename input is focused
- [x] #9 Playwright tests cover: Cmd/Ctrl multi-select, Shift range select, Delete triggers confirm, cancel preserves state, confirm deletes and updates UI
<!-- AC:END -->
