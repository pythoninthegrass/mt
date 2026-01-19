---
id: task-157
title: Integrate Alpine.js Intersect plugin for lazy loading and virtual scrolling
status: To Do
assignee: []
created_date: '2026-01-16 22:19'
labels:
  - frontend
  - alpine.js
  - performance
  - future
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Overview

Integrate Alpine.js's official Intersect plugin (`@alpinejs/intersect`) to enable lazy loading of album artwork and potentially implement virtual scrolling for large music libraries.

## Current State

The application currently:
- Loads all track data eagerly
- Renders all library rows at once
- No lazy loading of images or content
- No intersection-based loading

### Library Rendering (`index.html:440-500`)
```html
<template x-for="(track, index) in displayedTracks" :key="track.id">
  <tr class="library-row">
    <td><!-- index --></td>
    <td><!-- title --></td>
    <td><!-- artist --></td>
    <td><!-- album --></td>
    <td><!-- duration --></td>
  </tr>
</template>
```

### Potential Performance Issues

1. **Large libraries**: 10,000+ tracks render all rows
2. **Album art**: Would load all images at once if added
3. **Memory usage**: All DOM nodes created upfront
4. **Initial render**: Slow for very large collections

## Proposed Solution

### Installation
```bash
npm install @alpinejs/intersect
```

### Registration (`main.js`)
```javascript
import Alpine from 'alpinejs';
import intersect from '@alpinejs/intersect';

Alpine.plugin(intersect);
Alpine.start();
```

### Use Cases

#### 1. Lazy Load Album Artwork
```html
<template x-for="track in displayedTracks" :key="track.id">
  <tr class="library-row">
    <td class="album-art">
      <div 
        x-data="{ loaded: false }"
        x-intersect.once="loaded = true"
        class="w-10 h-10 bg-muted"
      >
        <img 
          x-show="loaded"
          :src="loaded ? track.albumArt : ''"
          class="w-full h-full object-cover"
          loading="lazy"
        >
      </div>
    </td>
    <!-- other columns -->
  </tr>
</template>
```

#### 2. Infinite Scroll / Load More
```html
<div x-data="{ 
  visibleCount: 100,
  loadMore() { this.visibleCount += 100; }
}">
  <template x-for="track in displayedTracks.slice(0, visibleCount)">
    <!-- track row -->
  </template>
  
  <!-- Sentinel element at bottom -->
  <div 
    x-show="visibleCount < displayedTracks.length"
    x-intersect="loadMore()"
    class="h-10"
  >
    <span class="text-muted">Loading more...</span>
  </div>
</div>
```

#### 3. Virtual Scrolling (Advanced)
```html
<div 
  x-data="virtualScroller($store.library.tracks)"
  class="h-full overflow-auto"
  @scroll="updateVisibleRange()"
>
  <!-- Spacer for items above viewport -->
  <div :style="{ height: topSpacerHeight + 'px' }"></div>
  
  <template x-for="track in visibleTracks" :key="track.id">
    <div class="track-row h-10">
      <!-- track content -->
    </div>
  </template>
  
  <!-- Spacer for items below viewport -->
  <div :style="{ height: bottomSpacerHeight + 'px' }"></div>
</div>
```

#### 4. Analytics / Play Tracking
```html
<div 
  x-intersect.threshold.50="trackView(track.id)"
>
  <!-- Track has been 50% visible, log impression -->
</div>
```

### Intersect Modifiers

```html
<!-- Trigger once (for lazy loading) -->
<div x-intersect.once="loadImage()">

<!-- Trigger when leaving viewport -->
<div x-intersect:leave="pauseVideo()">

<!-- Custom threshold (0-100%) -->
<div x-intersect.threshold.75="markAsViewed()">

<!-- Custom margin -->
<div x-intersect.margin.200px="preload()">

<!-- Half visible -->
<div x-intersect.half="onHalfVisible()">

<!-- Fully visible -->
<div x-intersect.full="onFullyVisible()">
```

## Projected Value

| Scenario | Before | After |
|----------|--------|-------|
| 10k tracks initial render | All 10k rows | 100 rows + lazy load |
| Album art loading | N/A (not implemented) | Lazy per-row |
| Memory usage | High (all DOM) | Low (virtual window) |
| Scroll performance | Degrades with size | Consistent |

## Implementation Priority

1. **Phase 1**: Lazy load album artwork (when art is added)
2. **Phase 2**: Infinite scroll for libraries > 1000 tracks
3. **Phase 3**: Full virtual scrolling for 10k+ track libraries

## Note

This is **lower priority** because:
1. Album artwork feature doesn't exist yet
2. Current library size may not warrant virtual scrolling
3. Browser handles thousands of rows reasonably well
4. Main value emerges with very large libraries (10k+ tracks)

However, this should be considered **before** adding album artwork to prevent loading hundreds of images at once.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Install and register @alpinejs/intersect plugin
- [ ] #2 Create proof-of-concept for lazy loading (placeholder images)
- [ ] #3 Implement infinite scroll for library view with 1000+ tracks
- [ ] #4 Measure performance improvement with large track collections
- [ ] #5 Document virtual scrolling pattern for future implementation
- [ ] #6 Add x-intersect.once to any lazy-loadable content
<!-- AC:END -->
