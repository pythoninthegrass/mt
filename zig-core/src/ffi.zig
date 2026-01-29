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
// Artwork Cache FFI (TODO: Implement)
// ============================================================================

// TODO: Uncomment and implement after ArtworkCache is complete
// const artwork_cache = @import("scanner/artwork_cache.zig");

// Create new artwork cache with default capacity
// Returns opaque handle or null on failure
// export fn mt_artwork_cache_new() callconv(.C) ?*artwork_cache.CacheHandle {
//     // TODO: Implement
//     return null;
// }

// Create artwork cache with custom capacity
// export fn mt_artwork_cache_new_with_capacity(capacity: usize) callconv(.C) ?*artwork_cache.CacheHandle {
//     // TODO: Implement
//     _ = capacity;
//     return null;
// }

// Get artwork for track, loading from file if not cached
// Returns true if artwork was found, false otherwise
// export fn mt_artwork_cache_get_or_load(
//     cache: *artwork_cache.CacheHandle,
//     track_id: i64,
//     filepath: [*:0]const u8,
//     out: *artwork_cache.Artwork,
// ) callconv(.C) bool {
//     // TODO: Implement
//     _ = cache;
//     _ = track_id;
//     _ = filepath;
//     _ = out;
//     return false;
// }

// Invalidate cache entry for a track
// export fn mt_artwork_cache_invalidate(
//     cache: *artwork_cache.CacheHandle,
//     track_id: i64,
// ) callconv(.C) void {
//     // TODO: Implement
//     _ = cache;
//     _ = track_id;
// }

// Clear all cache entries
// export fn mt_artwork_cache_clear(cache: *artwork_cache.CacheHandle) callconv(.C) void {
//     // TODO: Implement
//     _ = cache;
// }

// Get current cache size
// export fn mt_artwork_cache_len(cache: *artwork_cache.CacheHandle) callconv(.C) usize {
//     // TODO: Implement
//     _ = cache;
//     return 0;
// }

// Free artwork cache
// export fn mt_artwork_cache_free(cache: ?*artwork_cache.CacheHandle) callconv(.C) void {
//     // TODO: Implement
//     _ = cache;
// }

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
