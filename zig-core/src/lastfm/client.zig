//! Last.fm API client with rate limiting and configuration.

const std = @import("std");
const types = @import("types.zig");

/// Rate limiter state
pub const RateLimiter = struct {
    mutex: std.Thread.Mutex,
    last_request: i64, // nanoseconds since epoch
    min_interval_ns: i64, // minimum nanoseconds between requests

    pub fn init(requests_per_second: f64) RateLimiter {
        // TODO: Implement rate limiter initialization
        // - Calculate min_interval_ns from requests_per_second
        // - Initialize mutex
        _ = requests_per_second;
        @panic("TODO: Implement RateLimiter.init");
    }

    pub fn waitForSlot(self: *RateLimiter) void {
        // TODO: Implement rate limiting
        // - Lock mutex
        // - Check time since last_request
        // - Sleep if necessary to enforce min_interval_ns
        // - Update last_request
        // - Unlock mutex
        _ = self;
        @panic("TODO: Implement RateLimiter.waitForSlot");
    }
};

/// Client configuration
pub const Config = struct {
    api_key: []const u8,
    api_secret: []const u8,
    session_key: ?[]const u8,
    rate_limiter: RateLimiter,
};

/// Last.fm API client
pub const Client = struct {
    allocator: std.mem.Allocator,
    config: Config,

    pub fn init(allocator: std.mem.Allocator, api_key: []const u8, api_secret: []const u8) !*Client {
        // TODO: Implement client initialization
        // - Store API credentials
        // - Initialize rate limiter (5 requests per second per Last.fm docs)
        _ = allocator;
        _ = api_key;
        _ = api_secret;
        @panic("TODO: Implement Client.init");
    }

    pub fn deinit(self: *Client) void {
        // TODO: Implement cleanup
        _ = self;
        @panic("TODO: Implement Client.deinit");
    }

    pub fn setSessionKey(self: *Client, session_key: []const u8) void {
        // TODO: Store session key for authenticated requests
        _ = self;
        _ = session_key;
    }

    pub fn scrobble(self: *Client, request: *const types.ScrobbleRequest) !void {
        // TODO: Implement scrobble API call
        // 1. Build request parameters
        // 2. Generate API signature
        // 3. Wait for rate limiter slot
        // 4. Make HTTP POST request
        // 5. Parse response
        // 6. Handle errors
        _ = self;
        _ = request;
        @panic("TODO: Implement Client.scrobble");
    }

    pub fn updateNowPlaying(self: *Client, request: *const types.NowPlayingRequest) !void {
        // TODO: Implement now playing update
        // Similar to scrobble but uses different endpoint
        _ = self;
        _ = request;
        @panic("TODO: Implement Client.updateNowPlaying");
    }

    fn makeRequest(self: *Client, method: types.Method, params: *types.Params) ![]const u8 {
        // TODO: Implement generic API request
        // 1. Add api_key and method to params
        // 2. Add session_key if authenticated
        // 3. Generate signature
        // 4. Wait for rate limit
        // 5. Build HTTP request
        // 6. Execute request
        // 7. Return response body
        _ = self;
        _ = method;
        _ = params;
        @panic("TODO: Implement Client.makeRequest");
    }
};

// ============================================================================
// Tests
// ============================================================================

test "RateLimiter initialization" {
    // TODO: Test rate limiter setup
    return error.SkipZigTest;
}

test "RateLimiter enforces rate" {
    // TODO: Test that requests are delayed appropriately
    return error.SkipZigTest;
}

test "Client scrobble" {
    // TODO: Test scrobble with mock HTTP
    return error.SkipZigTest;
}

test "Client updateNowPlaying" {
    // TODO: Test now playing with mock HTTP
    return error.SkipZigTest;
}
