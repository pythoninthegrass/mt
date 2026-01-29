//! Last.fm API types and signature generation.
//!
//! Implements Last.fm API authentication and request signing.

const std = @import("std");

/// Last.fm API method
pub const Method = enum {
    track_updateNowPlaying,
    track_scrobble,
    auth_getSession,
    user_getInfo,

    pub fn toString(self: Method) []const u8 {
        return switch (self) {
            .track_updateNowPlaying => "track.updateNowPlaying",
            .track_scrobble => "track.scrobble",
            .auth_getSession => "auth.getSession",
            .user_getInfo => "user.getInfo",
        };
    }
};

/// API request parameters
pub const Params = struct {
    allocator: std.mem.Allocator,
    map: std.StringHashMap([]const u8),

    pub fn init(allocator: std.mem.Allocator) !Params {
        return Params{
            .allocator = allocator,
            .map = std.StringHashMap([]const u8).init(allocator),
        };
    }

    pub fn deinit(self: *Params) void {
        self.map.deinit();
    }

    pub fn add(self: *Params, key: []const u8, value: []const u8) !void {
        try self.map.put(key, value);
    }
};

/// Generate API signature
pub fn generateSignature(params: *const Params, api_secret: []const u8) ![]const u8 {
    // TODO: Implement signature generation
    // 1. Sort parameters alphabetically by key
    // 2. Concatenate key=value pairs (no delimiters)
    // 3. Append API secret
    // 4. Calculate MD5 hash
    // 5. Return hex-encoded hash
    _ = params;
    _ = api_secret;
    @panic("TODO: Implement generateSignature");
}

/// Scrobble request
pub const ScrobbleRequest = extern struct {
    artist: [512]u8,
    artist_len: u32,
    track: [512]u8,
    track_len: u32,
    album: [512]u8,
    album_len: u32,
    timestamp: i64,
    duration: i32,
    track_number: u32,
};

/// Now playing request
pub const NowPlayingRequest = extern struct {
    artist: [512]u8,
    artist_len: u32,
    track: [512]u8,
    track_len: u32,
    album: [512]u8,
    album_len: u32,
    duration: i32,
    track_number: u32,
};

// ============================================================================
// Tests
// ============================================================================

test "Method toString" {
    try std.testing.expectEqualStrings("track.scrobble", Method.track_scrobble.toString());
}

test "Params add" {
    // TODO: Test parameter addition
    return error.SkipZigTest;
}

test "generateSignature" {
    // TODO: Test signature generation with known fixtures
    // Example from Last.fm docs:
    // api_key=xxx&method=auth.getSession&token=yyy
    // + secret => MD5 hash
    return error.SkipZigTest;
}
