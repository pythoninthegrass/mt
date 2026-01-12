---
id: task-104
title: 'P4: Build sidebar navigation component'
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
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the left sidebar for navigation using AlpineJS + Basecoat.

**Sections:**
1. Library views:
   - All Music
   - Liked Songs (favorites)
   - Recently Played
   - Recently Added
   - Top 25 Most Played

2. Playlists:
   - List of user playlists
   - "New Playlist" button

**Component structure:**
```html
<aside class="w-64 bg-background border-r h-full overflow-y-auto">
    <nav class="p-4 space-y-6">
        <!-- Library Section -->
        <div>
            <h3 class="text-xs font-semibold text-muted-foreground mb-2">LIBRARY</h3>
            <ul class="space-y-1">
                <li><button class="btn btn-ghost w-full justify-start"
                            :class="{ 'bg-accent': activeSection === 'music' }"
                            @click="loadSection('music')">🎵 All Music</button></li>
                <li><button class="btn btn-ghost w-full justify-start"
                            @click="loadSection('liked')">❤️ Liked Songs</button></li>
                <li><button class="btn btn-ghost w-full justify-start"
                            @click="loadSection('recent')">🕐 Recently Played</button></li>
                <li><button class="btn btn-ghost w-full justify-start"
                            @click="loadSection('added')">✨ Recently Added</button></li>
                <li><button class="btn btn-ghost w-full justify-start"
                            @click="loadSection('top25')">🔥 Top 25</button></li>
            </ul>
        </div>
        
        <!-- Playlists Section -->
        <div>
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-xs font-semibold text-muted-foreground">PLAYLISTS</h3>
                <button class="btn btn-ghost btn-sm" @click="createPlaylist()">+</button>
            </div>
            <ul class="space-y-1">
                <template x-for="playlist in playlists">
                    <li><button class="btn btn-ghost w-full justify-start truncate"
                                @click="loadPlaylist(playlist.id)"
                                x-text="playlist.name"></button></li>
                </template>
            </ul>
        </div>
    </nav>
</aside>
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All library sections clickable and load correct data
- [ ] #2 Active section highlighted
- [ ] #3 Playlists list populated from backend
- [ ] #4 New playlist button opens creation dialog
- [ ] #5 Sidebar scrolls if content overflows
<!-- AC:END -->
