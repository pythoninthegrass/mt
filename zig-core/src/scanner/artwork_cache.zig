//! LRU cache for artwork to reduce IPC calls during queue navigation.
//!
//! Caches recently accessed artwork in memory to avoid repeatedly
//! extracting artwork from files when navigating prev/next in queue.

const std = @import("std");
const c = @import("../c.zig");

/// Default cache size (number of tracks)
const DEFAULT_CACHE_SIZE: usize = 100;

/// Artwork data structure (matches Rust Artwork type)
pub const Artwork = extern struct {
    // TODO: Implement fixed-size buffer layout for FFI safety
    // Should match Rust's Artwork struct with base64 data, mime_type, source, filename
    data: [8192]u8, // Base64-encoded image data (fixed-size buffer)
    data_len: u32,
    mime_type: [64]u8,
    mime_type_len: u32,
    source: [16]u8, // "embedded" or "folder"
    source_len: u32,
    filename: [256]u8,
    filename_len: u32,
    has_filename: bool,
};

/// Opaque cache handle for FFI
pub const CacheHandle = opaque {};

/// LRU cache node
const CacheNode = struct {
    track_id: i64,
    artwork: ?Artwork,
    prev: ?*CacheNode,
    next: ?*CacheNode,
};

/// LRU cache implementation
pub const ArtworkCache = struct {
    allocator: std.mem.Allocator,
    capacity: usize,
    map: std.AutoHashMap(i64, *CacheNode),
    head: ?*CacheNode,
    tail: ?*CacheNode,
    mutex: std.Thread.Mutex,

    pub fn init(allocator: std.mem.Allocator, capacity: usize) !*ArtworkCache {
        // TODO: Implement LRU cache initialization
        // - Allocate cache structure
        // - Initialize hash map with capacity
        // - Initialize mutex
        _ = allocator;
        _ = capacity;
        @panic("TODO: Implement ArtworkCache.init");
    }

    pub fn deinit(self: *ArtworkCache) void {
        // TODO: Implement cleanup
        // - Clear all nodes
        // - Deinit hash map
        // - Free cache structure
        _ = self;
        @panic("TODO: Implement ArtworkCache.deinit");
    }

    pub fn getOrLoad(self: *ArtworkCache, track_id: i64, filepath: [*:0]const u8) ?Artwork {
        // TODO: Implement get_or_load logic
        // 1. Lock mutex
        // 2. Check if track_id exists in map (cache hit)
        //    - If hit: move node to front (most recent), return artwork
        // 3. If miss: call extractArtwork(filepath)
        //    - Insert new node at front
        //    - Evict LRU node if at capacity
        // 4. Unlock mutex
        // 5. Return artwork
        _ = self;
        _ = track_id;
        _ = filepath;
        @panic("TODO: Implement ArtworkCache.getOrLoad");
    }

    pub fn invalidate(self: *ArtworkCache, track_id: i64) void {
        // TODO: Implement invalidation
        // - Lock mutex
        // - Remove node from map and linked list
        // - Free node
        // - Unlock mutex
        _ = self;
        _ = track_id;
        @panic("TODO: Implement ArtworkCache.invalidate");
    }

    pub fn clear(self: *ArtworkCache) void {
        // TODO: Implement clear
        // - Lock mutex
        // - Remove all nodes
        // - Clear hash map
        // - Reset head/tail
        // - Unlock mutex
        _ = self;
        @panic("TODO: Implement ArtworkCache.clear");
    }

    pub fn len(self: *ArtworkCache) usize {
        // TODO: Return current number of cached items
        _ = self;
        return 0;
    }

    fn moveToFront(self: *ArtworkCache, node: *CacheNode) void {
        // TODO: Move node to front of linked list (mark as most recently used)
        _ = self;
        _ = node;
    }

    fn evictLRU(self: *ArtworkCache) void {
        // TODO: Remove least recently used node (tail) when at capacity
        _ = self;
    }
};

/// Extract artwork from file (embedded or folder-based)
fn extractArtwork(filepath: [*:0]const u8) ?Artwork {
    // TODO: Implement artwork extraction
    // 1. Try embedded artwork first (via lofty or TagLib C)
    // 2. If no embedded artwork, try folder-based (cover.jpg, folder.jpg, etc.)
    // 3. Encode image data as base64
    // 4. Return Artwork struct or null
    _ = filepath;
    return null;
}

/// Extract embedded artwork using TagLib C bindings
fn extractEmbeddedArtwork(filepath: [*:0]const u8) ?Artwork {
    // TODO: Call TagLib C API to extract embedded artwork
    // - Open file with taglib_file_new()
    // - Get tag with taglib_file_tag()
    // - Extract picture data
    // - Base64 encode
    // - Populate Artwork struct
    _ = filepath;
    return null;
}

/// Find folder-based artwork in same directory
fn extractFolderArtwork(filepath: [*:0]const u8) ?Artwork {
    // TODO: Search for standard artwork filenames
    // - Get directory from filepath
    // - Try: cover.jpg, cover.png, folder.jpg, folder.png, etc.
    // - Read file data
    // - Base64 encode
    // - Populate Artwork struct
    _ = filepath;
    return null;
}

// ============================================================================
// Tests
// ============================================================================

test "ArtworkCache creation" {
    // TODO: Test cache creation with default capacity
    return error.SkipZigTest;
}

test "ArtworkCache get_or_load caching" {
    // TODO: Test that second call returns cached result
    return error.SkipZigTest;
}

test "ArtworkCache LRU eviction" {
    // TODO: Test that adding capacity+1 items evicts oldest
    return error.SkipZigTest;
}

test "ArtworkCache invalidation" {
    // TODO: Test invalidate removes entry
    return error.SkipZigTest;
}

test "ArtworkCache clear" {
    // TODO: Test clear removes all entries
    return error.SkipZigTest;
}
