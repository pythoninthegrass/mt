//! mt-core: Zig implementation of music library business logic
//!
//! This library provides the core functionality for the mt music player,
//! exposed via C ABI for FFI from Rust/Tauri.

const std = @import("std");

pub const scanner = @import("scanner/scanner.zig");
pub const metadata = @import("scanner/metadata.zig");
pub const fingerprint = @import("scanner/fingerprint.zig");
pub const types = @import("types.zig");

// Re-export FFI functions at library root
pub usingnamespace @import("ffi.zig");

test {
    std.testing.refAllDecls(@This());
}
