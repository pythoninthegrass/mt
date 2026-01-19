# Infinite Scroll Pattern with Alpine.js Intersect Plugin

This document describes the infinite scroll implementation using the `@alpinejs/intersect` plugin for large track collections.

## Overview

The library view uses infinite scroll to improve performance when displaying large music collections. Instead of rendering all tracks at once, tracks are loaded in batches of 100 as the user scrolls.

## Implementation

### 1. Store Configuration (`js/stores/library.js`)

```javascript
{
  // Infinite scroll/pagination
  visibleCount: 100,   // Number of tracks to display
  batchSize: 100,      // Load 100 more tracks at a time

  // Methods
  getVisibleTracks() {
    return this.filteredTracks.slice(0, this.visibleCount);
  },

  loadMore() {
    if (this.visibleCount < this.filteredTracks.length) {
      this.visibleCount += this.batchSize;
    }
  },

  resetVisibleCount() {
    this.visibleCount = this.batchSize;
  }
}
```

### 2. Template Integration (`index.html`)

```html
<!-- Render visible tracks only -->
<template x-for="(track, index) in library.getVisibleTracks()" :key="track.id">
  <!-- track row -->
</template>

<!-- Sentinel element triggers loadMore() when visible -->
<div
  x-show="library.visibleCount < library.filteredTracks.length"
  x-intersect="library.loadMore()"
  class="py-4 text-center text-sm text-muted-foreground"
>
  Loading more tracks...
</div>
```

## How It Works

1. **Initial Load**: Only first 100 tracks are rendered (`visibleCount: 100`)
2. **Scroll Detection**: When sentinel element becomes visible, `x-intersect` triggers `loadMore()`
3. **Batch Loading**: `loadMore()` increases `visibleCount` by 100
4. **Re-render**: Alpine reactively re-renders with more tracks visible
5. **Filter Reset**: When search/sort changes, `resetVisibleCount()` resets to first 100

## Performance Benefits

| Scenario | Before | After |
|----------|--------|-------|
| 10,000 tracks initial render | 10,000 DOM nodes | 100 DOM nodes |
| Memory usage | High | ~99% reduction |
| Scroll performance | Degrades with size | Consistent |
| Initial page load | Slow | Fast |

## Future Enhancements

### Virtual Scrolling (Advanced)

For even better performance with 10k+ tracks, consider full virtual scrolling:

```javascript
{
  scrollTop: 0,
  rowHeight: 40,
  viewportHeight: 600,

  get visibleStartIndex() {
    return Math.floor(this.scrollTop / this.rowHeight);
  },

  get visibleEndIndex() {
    return Math.ceil((this.scrollTop + this.viewportHeight) / this.rowHeight);
  },

  get visibleTracks() {
    return this.filteredTracks.slice(
      this.visibleStartIndex,
      this.visibleEndIndex + 1
    );
  },

  get topSpacerHeight() {
    return this.visibleStartIndex * this.rowHeight;
  },

  get bottomSpacerHeight() {
    return (this.filteredTracks.length - this.visibleEndIndex - 1) * this.rowHeight;
  }
}
```

## Intersect Plugin Modifiers

The `@alpinejs/intersect` plugin supports various modifiers:

```html
<!-- Trigger once (for lazy loading images) -->
<div x-intersect.once="loadImage()">

<!-- Trigger when leaving viewport -->
<div x-intersect:leave="pauseVideo()">

<!-- Custom threshold (0-100%) -->
<div x-intersect.threshold.75="markAsViewed()">

<!-- Custom margin (preload before visible) -->
<div x-intersect.margin.200px="preload()">

<!-- Half visible -->
<div x-intersect.half="onHalfVisible()">

<!-- Fully visible -->
<div x-intersect.full="onFullyVisible()">
```

## Lazy Loading Album Artwork

When album artwork is added, use `x-intersect.once` for lazy loading:

```html
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
```

## Testing

To test infinite scroll with large datasets:

1. Load a library with 1000+ tracks
2. Scroll to bottom of library view
3. Observe sentinel element appearing
4. Verify next batch of 100 tracks loads
5. Check browser DevTools Performance tab for DOM node count
6. Compare memory usage before/after implementation

## Browser Compatibility

The Intersection Observer API (used by `x-intersect`) is supported in all modern browsers:
- Chrome 51+
- Firefox 55+
- Safari 12.1+
- Edge 15+

For Tauri apps, this is guaranteed to work as Tauri uses a modern WebView.
