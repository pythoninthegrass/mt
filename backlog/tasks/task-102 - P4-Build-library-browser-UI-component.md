---
id: task-102
title: 'P4: Build library browser UI component'
status: To Do
assignee: []
created_date: '2026-01-12 04:08'
labels:
  - frontend
  - ui
  - phase-4
milestone: Tauri Migration
dependencies:
  - task-101
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the library browser view using AlpineJS + Basecoat.

**Features:**
- Track list table with columns: Title, Artist, Album, Duration
- Search input with debounced filtering
- Sortable columns (click header to sort)
- Double-click to play track
- Right-click context menu (add to queue, add to playlist, etc.)
- Loading state indicator
- Empty state when no tracks

**Component structure:**
```html
<div x-data x-show="$store.ui.view === 'library'">
    <!-- Search bar -->
    <input type="search" 
           x-model="$store.library.searchQuery"
           @input.debounce.300ms="$store.library.load($store.library.searchQuery)">
    
    <!-- Track table -->
    <table class="table">
        <thead>
            <tr>
                <th @click="sortBy('title')">Title</th>
                <th @click="sortBy('artist')">Artist</th>
                <th @click="sortBy('album')">Album</th>
                <th>Duration</th>
            </tr>
        </thead>
        <tbody>
            <template x-for="track in $store.library.tracks">
                <tr @dblclick="$store.player.play(track)"
                    :class="{ 'bg-primary/10': $store.player.currentTrack?.id === track.id }">
                    <td x-text="track.title"></td>
                    <td x-text="track.artist"></td>
                    <td x-text="track.album"></td>
                    <td x-text="formatDuration(track.duration)"></td>
                </tr>
            </template>
        </tbody>
    </table>
</div>
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Track list displays all library tracks
- [ ] #2 Search filters tracks in real-time
- [ ] #3 Column sorting works
- [ ] #4 Double-click plays track
- [ ] #5 Currently playing track highlighted
- [ ] #6 Loading and empty states display correctly
<!-- AC:END -->
