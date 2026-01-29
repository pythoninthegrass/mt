//! FFI exports for Rust/Tauri integration
//!
//! All functions use C ABI and fixed-size types for safe FFI.

const std = @import("std");
const types = @import("types.zig");
const scanner = @import("scanner/scanner.zig");
const metadata = @import("scanner/metadata.zig");

const ExtractedMetadata = types.ExtractedMetadata;
const FileFingerprint = types.FileFingerprint;
const ScanStats = types.ScanStats;

// Use a general purpose allocator for FFI allocations
var gpa = std.heap.GeneralPurposeAllocator(.{}){};

// ============================================================================
// Scanner FFI
// ============================================================================

/// Extract metadata from a single file.
/// Returns a pointer to ExtractedMetadata that must be freed with mt_free_metadata.
export fn mt_extract_metadata(path_ptr: [*:0]const u8) callconv(.C) ?*ExtractedMetadata {
    const path = std.mem.span(path_ptr);

    const result = gpa.allocator().create(ExtractedMetadata) catch return null;
    result.* = metadata.extractMetadata(path);

    return result;
}

/// Free metadata returned by mt_extract_metadata
export fn mt_free_metadata(ptr: ?*ExtractedMetadata) callconv(.C) void {
    if (ptr) |p| {
        gpa.allocator().destroy(p);
    }
}

/// Extract metadata into a caller-provided buffer (no allocation).
/// Returns true on success.
export fn mt_extract_metadata_into(
    path_ptr: [*:0]const u8,
    out: *ExtractedMetadata,
) callconv(.C) bool {
    const path = std.mem.span(path_ptr);
    out.* = metadata.extractMetadata(path);
    return out.is_valid;
}

/// Batch extract metadata from multiple files.
/// Caller provides arrays for paths and results.
/// Returns number of successfully extracted files.
export fn mt_extract_metadata_batch(
    paths: [*]const [*:0]const u8,
    count: usize,
    results: [*]ExtractedMetadata,
) callconv(.C) usize {
    var success_count: usize = 0;

    for (0..count) |i| {
        const path = std.mem.span(paths[i]);
        results[i] = metadata.extractMetadata(path);
        if (results[i].is_valid) {
            success_count += 1;
        }
    }

    return success_count;
}

/// Check if a file has a supported audio extension
export fn mt_is_audio_file(path_ptr: [*:0]const u8) callconv(.C) bool {
    const path = std.mem.span(path_ptr);
    return types.isAudioFile(path);
}

// ============================================================================
// Fingerprint FFI
// ============================================================================

/// Get file fingerprint from path.
/// Returns true on success, populates out_fp.
export fn mt_get_fingerprint(
    path_ptr: [*:0]const u8,
    out_fp: *FileFingerprint,
) callconv(.C) bool {
    const path = std.mem.span(path_ptr);

    const fp = @import("scanner/fingerprint.zig").fromPath(path) catch {
        return false;
    };

    out_fp.* = fp;
    return true;
}

/// Compare two fingerprints for equality (ignores inode)
export fn mt_fingerprint_matches(
    fp1: *const FileFingerprint,
    fp2: *const FileFingerprint,
) callconv(.C) bool {
    return fp1.matches(fp2.*);
}

// ============================================================================
// Memory management
// ============================================================================

/// Allocate a buffer of the given size.
/// Returns null on failure.
export fn mt_alloc(size: usize) callconv(.C) ?[*]u8 {
    const slice = gpa.allocator().alloc(u8, size) catch return null;
    return slice.ptr;
}

/// Free a buffer allocated by mt_alloc.
export fn mt_free(ptr: ?[*]u8, size: usize) callconv(.C) void {
    if (ptr) |p| {
        gpa.allocator().free(p[0..size]);
    }
}

// ============================================================================
// Version info
// ============================================================================

/// Get library version string
export fn mt_version() callconv(.C) [*:0]const u8 {
    return "0.1.0";
}

// ============================================================================
// Artwork Cache FFI
// ============================================================================

const artwork_cache = @import("scanner/artwork_cache.zig");
pub const Artwork = artwork_cache.Artwork;
pub const ArtworkCache = artwork_cache.ArtworkCache;

/// Create new artwork cache with default capacity (100 entries).
/// Returns opaque handle or null on allocation failure.
export fn mt_artwork_cache_new() callconv(.C) ?*ArtworkCache {
    return ArtworkCache.init(gpa.allocator(), artwork_cache.DEFAULT_CACHE_SIZE) catch null;
}

/// Create artwork cache with custom capacity.
/// Returns opaque handle or null on allocation failure.
export fn mt_artwork_cache_new_with_capacity(capacity: usize) callconv(.C) ?*ArtworkCache {
    return ArtworkCache.init(gpa.allocator(), capacity) catch null;
}

/// Get artwork for track, loading from file if not cached.
/// Returns true if artwork was found, false otherwise.
/// The out parameter is populated only when returning true.
export fn mt_artwork_cache_get_or_load(
    cache: ?*ArtworkCache,
    track_id: i64,
    filepath: [*:0]const u8,
    out: *Artwork,
) callconv(.C) bool {
    const c = cache orelse return false;
    if (c.getOrLoad(track_id, filepath)) |artwork| {
        out.* = artwork;
        return true;
    }
    return false;
}

/// Invalidate cache entry for a specific track.
/// Call this when track metadata is updated.
export fn mt_artwork_cache_invalidate(
    cache: ?*ArtworkCache,
    track_id: i64,
) callconv(.C) void {
    const c = cache orelse return;
    c.invalidate(track_id);
}

/// Clear all cache entries.
export fn mt_artwork_cache_clear(cache: ?*ArtworkCache) callconv(.C) void {
    const c = cache orelse return;
    c.clear();
}

/// Get current number of cached items.
export fn mt_artwork_cache_len(cache: ?*ArtworkCache) callconv(.C) usize {
    const c = cache orelse return 0;
    return c.len();
}

/// Free artwork cache and all associated resources.
export fn mt_artwork_cache_free(cache: ?*ArtworkCache) callconv(.C) void {
    const c = cache orelse return;
    c.deinit();
}

// ============================================================================
// Tests
// ============================================================================

test "FFI metadata extraction" {
    var m: ExtractedMetadata = undefined;
    const success = mt_extract_metadata_into("/nonexistent/path.mp3", &m);
    try std.testing.expect(!success);
    try std.testing.expect(!m.is_valid);
}

test "FFI is_audio_file" {
    try std.testing.expect(mt_is_audio_file("song.mp3"));
    try std.testing.expect(mt_is_audio_file("track.FLAC"));
    try std.testing.expect(!mt_is_audio_file("image.jpg"));
}
