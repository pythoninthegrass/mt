//! Settings, scrobble tracking, and watched folders database operations.

const std = @import("std");
const models = @import("models.zig");

/// Database connection handle (opaque)
pub const DbHandle = opaque {};

// ============================================================================
// Settings Operations
// ============================================================================

/// Get setting value by key
pub fn getSetting(db: *DbHandle, key: [*:0]const u8, allocator: std.mem.Allocator) !?[]const u8 {
    // TODO: Implement query
    // - Execute SELECT value FROM settings WHERE key = ?
    // - Return value or null
    _ = db;
    _ = key;
    _ = allocator;
    @panic("TODO: Implement getSetting");
}

/// Set setting value
pub fn setSetting(db: *DbHandle, key: [*:0]const u8, value: [*:0]const u8) !void {
    // TODO: Implement upsert
    // - INSERT OR REPLACE INTO settings (key, value)
    _ = db;
    _ = key;
    _ = value;
    @panic("TODO: Implement setSetting");
}

/// Delete setting
pub fn deleteSetting(db: *DbHandle, key: [*:0]const u8) !void {
    // TODO: Implement deletion
    // - DELETE FROM settings WHERE key = ?
    _ = db;
    _ = key;
    @panic("TODO: Implement deleteSetting");
}

// ============================================================================
// Scrobble Tracking Operations
// ============================================================================

/// Record track play for scrobbling
pub fn recordPlay(db: *DbHandle, track_id: i64, timestamp: i64) !void {
    // TODO: Implement play recording
    // - INSERT INTO scrobbles (track_id, timestamp)
    // - Update track play_count and last_played_at
    _ = db;
    _ = track_id;
    _ = timestamp;
    @panic("TODO: Implement recordPlay");
}

/// Get pending scrobbles
pub fn getPendingScrobbles(db: *DbHandle, allocator: std.mem.Allocator) ![]ScrobbleRecord {
    // TODO: Implement query
    // - Execute SELECT * FROM scrobbles WHERE submitted = 0
    _ = db;
    _ = allocator;
    @panic("TODO: Implement getPendingScrobbles");
}

pub const ScrobbleRecord = extern struct {
    id: i64,
    track_id: i64,
    timestamp: i64,
    submitted: bool,
};

/// Mark scrobble as submitted
pub fn markScrobbleSubmitted(db: *DbHandle, scrobble_id: i64) !void {
    // TODO: Implement update
    // - UPDATE scrobbles SET submitted = 1 WHERE id = ?
    _ = db;
    _ = scrobble_id;
    @panic("TODO: Implement markScrobbleSubmitted");
}

// ============================================================================
// Watched Folders Operations
// ============================================================================

pub const WatchedFolder = extern struct {
    id: i64,
    path: [4096]u8,
    path_len: u32,
    scan_mode: u8, // 0=manual, 1=auto, 2=watch
    enabled: bool,
    last_scan: i64,
};

/// Get all watched folders
pub fn getWatchedFolders(db: *DbHandle, allocator: std.mem.Allocator) ![]WatchedFolder {
    // TODO: Implement query
    // - Execute SELECT * FROM watched_folders
    _ = db;
    _ = allocator;
    @panic("TODO: Implement getWatchedFolders");
}

/// Add watched folder
pub fn addWatchedFolder(db: *DbHandle, path: [*:0]const u8, scan_mode: u8) !i64 {
    // TODO: Implement insertion
    // - INSERT INTO watched_folders (path, scan_mode)
    // - Return folder ID
    _ = db;
    _ = path;
    _ = scan_mode;
    @panic("TODO: Implement addWatchedFolder");
}

/// Remove watched folder
pub fn removeWatchedFolder(db: *DbHandle, folder_id: i64) !void {
    // TODO: Implement deletion
    // - DELETE FROM watched_folders WHERE id = ?
    _ = db;
    _ = folder_id;
    @panic("TODO: Implement removeWatchedFolder");
}

/// Update watched folder scan mode
pub fn updateWatchedFolderMode(db: *DbHandle, folder_id: i64, scan_mode: u8) !void {
    // TODO: Implement update
    // - UPDATE watched_folders SET scan_mode = ? WHERE id = ?
    _ = db;
    _ = folder_id;
    _ = scan_mode;
    @panic("TODO: Implement updateWatchedFolderMode");
}

// ============================================================================
// Tests
// ============================================================================

test "Settings operations" {
    // TODO: Test get/set/delete settings
    return error.SkipZigTest;
}

test "Scrobble tracking" {
    // TODO: Test record play and pending scrobbles
    return error.SkipZigTest;
}

test "Watched folders" {
    // TODO: Test add/remove/update watched folders
    return error.SkipZigTest;
}
