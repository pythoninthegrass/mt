---
id: task-103
title: 'P4: Build player controls bar UI component'
status: Done
assignee: []
created_date: '2026-01-12 04:08'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - ui
  - phase-4
milestone: Tauri Migration
dependencies:
  - task-101
priority: high
ordinal: 91382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the bottom player controls bar using AlpineJS + Basecoat.

**Layout (left to right):**
1. Now playing info (album art placeholder, title, artist)
2. Transport controls (prev, play/pause, next)
3. Progress bar with time display
4. Volume control
5. Additional controls (shuffle, loop, queue toggle)

**Component structure:**
```html
<footer class="fixed bottom-0 w-full bg-background border-t p-4">
    <div class="flex items-center gap-4">
        <!-- Now Playing -->
        <div class="flex items-center gap-3 w-1/4">
            <div class="w-12 h-12 bg-muted rounded"></div>
            <div class="overflow-hidden">
                <p class="text-sm font-medium truncate" 
                   x-text="$store.player.currentTrack?.title || 'No track'"></p>
                <p class="text-xs text-muted-foreground truncate"
                   x-text="$store.player.currentTrack?.artist || '-'"></p>
            </div>
        </div>
        
        <!-- Controls -->
        <div class="flex-1 flex flex-col items-center gap-2">
            <div class="flex items-center gap-4">
                <button class="btn btn-ghost" @click="$store.player.previous()">⏮</button>
                <button class="btn btn-primary rounded-full" @click="$store.player.toggle()">
                    <span x-text="$store.player.isPlaying ? '⏸' : '▶'"></span>
                </button>
                <button class="btn btn-ghost" @click="$store.player.next()">⏭</button>
            </div>
            
            <!-- Progress -->
            <div class="w-full max-w-md flex items-center gap-2">
                <span class="text-xs" x-text="formatTime($store.player.currentTime)"></span>
                <input type="range" class="flex-1" min="0" max="100"
                       :value="$store.player.progress"
                       @input="$store.player.seek($event.target.value)">
                <span class="text-xs" x-text="formatTime($store.player.duration)"></span>
            </div>
        </div>
        
        <!-- Volume -->
        <div class="w-1/4 flex justify-end items-center gap-2">
            <span>🔊</span>
            <input type="range" class="w-24" min="0" max="100"
                   x-model="$store.player.volume"
                   @input="$store.player.setVolume($event.target.value)">
        </div>
    </div>
</footer>
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Now playing info displays current track
- [x] #2 Play/pause button toggles and updates icon
- [x] #3 Next/previous buttons work
- [x] #4 Progress bar shows current position
- [x] #5 Progress bar is seekable
- [x] #6 Volume slider controls audio level
- [x] #7 Time displays update during playback
<!-- AC:END -->
