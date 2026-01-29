//! Database models and schema definitions.
//!
//! Defines all database tables and their corresponding Zig structs.

const std = @import("std");

/// Track model
pub const Track = extern struct {
    id: i64,
    filepath: [4096]u8,
    filepath_len: u32,
    title: [512]u8,
    title_len: u32,
    artist: [512]u8,
    artist_len: u32,
    album: [512]u8,
    album_len: u32,
    album_artist: [512]u8,
    album_artist_len: u32,
    track_number: [32]u8,
    track_number_len: u32,
    disc_number: u32,
    year: u32,
    genre: [256]u8,
    genre_len: u32,
    duration_secs: f64,
    bitrate: u32,
    sample_rate: u32,
    channels: u8,
    file_size: i64,
    file_mtime_ns: i64,
    created_at: i64,
    updated_at: i64,
    play_count: u32,
    last_played_at: i64,
    rating: u8,
    is_favorite: bool,
};

/// Playlist model
pub const Playlist = extern struct {
    id: i64,
    name: [512]u8,
    name_len: u32,
    description: [2048]u8,
    description_len: u32,
    created_at: i64,
    updated_at: i64,
    track_count: u32,
};

/// Queue item model
pub const QueueItem = extern struct {
    id: i64,
    track_id: i64,
    position: u32,
    added_at: i64,
};

/// Setting model
pub const Setting = extern struct {
    key: [256]u8,
    key_len: u32,
    value: [4096]u8,
    value_len: u32,
    updated_at: i64,
};

/// Schema version
pub const SCHEMA_VERSION: u32 = 1;

/// SQL schema definitions
pub const SCHEMA_SQL = struct {
    // TODO: Add CREATE TABLE statements for all tables
    pub const tracks_table =
        \\CREATE TABLE IF NOT EXISTS tracks (
        \\  id INTEGER PRIMARY KEY AUTOINCREMENT,
        \\  filepath TEXT NOT NULL UNIQUE,
        \\  title TEXT,
        \\  artist TEXT,
        \\  album TEXT,
        \\  album_artist TEXT,
        \\  track_number TEXT,
        \\  disc_number INTEGER,
        \\  year INTEGER,
        \\  genre TEXT,
        \\  duration_secs REAL,
        \\  bitrate INTEGER,
        \\  sample_rate INTEGER,
        \\  channels INTEGER,
        \\  file_size INTEGER,
        \\  file_mtime_ns INTEGER,
        \\  created_at INTEGER DEFAULT (strftime('%s', 'now')),
        \\  updated_at INTEGER DEFAULT (strftime('%s', 'now')),
        \\  play_count INTEGER DEFAULT 0,
        \\  last_played_at INTEGER,
        \\  rating INTEGER DEFAULT 0,
        \\  is_favorite BOOLEAN DEFAULT 0
        \\);
    ;

    // TODO: Add other table schemas (playlists, queue, settings, etc.)
};

// ============================================================================
// Tests
// ============================================================================

test "Track struct size" {
    // TODO: Verify struct sizes are reasonable for FFI
    return error.SkipZigTest;
}

test "Schema SQL validity" {
    // TODO: Test SQL statements are well-formed
    return error.SkipZigTest;
}
