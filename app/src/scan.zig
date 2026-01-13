const std = @import("std");
const py = @import("pydust");

// Audio file extensions we recognize
const AUDIO_EXTENSIONS = [_][]const u8{ ".mp3", ".flac", ".m4a", ".ogg", ".wav", ".wma", ".aac", ".opus", ".m4p", ".mp4" };

// Simplified structures - will return basic types for now

// Check if a file has an audio extension
fn isAudioFile(filename: []const u8) bool {
    // Find the last dot
    if (std.mem.lastIndexOf(u8, filename, ".")) |dot_index| {
        const extension = filename[dot_index..];

        // Check against known audio extensions (case insensitive)
        for (AUDIO_EXTENSIONS) |audio_ext| {
            if (std.ascii.eqlIgnoreCase(extension, audio_ext)) {
                return true;
            }
        }
    }
    return false;
}

// Convert nanosecond timestamp to Unix epoch seconds
fn nanoToUnixSeconds(nano_timestamp: i128) f64 {
    const NANOS_PER_SEC: i128 = 1_000_000_000;
    return @as(f64, @floatFromInt(@divTrunc(nano_timestamp, NANOS_PER_SEC)));
}

// Simplified recursive directory scanner - just counts files
fn scanDirectoryRecursive(allocator: std.mem.Allocator, path: []const u8, count: *u64) !void {
    var dir = std.fs.openDirAbsolute(path, .{ .iterate = true }) catch |err| {
        // Skip directories we can't access (permissions, etc.)
        if (err == error.AccessDenied or err == error.FileNotFound) {
            return;
        }
        return err;
    };
    defer dir.close();

    var walker = dir.walk(allocator) catch |err| {
        return err;
    };
    defer walker.deinit();

    while (walker.next() catch null) |entry| {
        switch (entry.kind) {
            .file => {
                if (isAudioFile(entry.basename)) {
                    count.* += 1;
                }
            },
            .directory => {
                // Skip hidden directories and common non-music directories
                if (entry.basename[0] == '.' or
                    std.mem.eql(u8, entry.basename, "__pycache__") or
                    std.mem.eql(u8, entry.basename, "Thumbs.db") or
                    std.mem.eql(u8, entry.basename, ".DS_Store"))
                {
                    continue;
                }

                // Continue recursion
                const subdir_path = try std.fmt.allocPrint(allocator, "{s}/{s}", .{ path, entry.path });
                defer allocator.free(subdir_path);

                try scanDirectoryRecursive(allocator, subdir_path, count);
            },
            else => {},
        }
    }
}

// Main scanning function exposed to Python - returns count of audio files
pub fn scan_music_directory(args: struct { root_path: []const u8 }) u64 {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer if (gpa.deinit() == .leak) {
        std.debug.print("Memory leak detected!\n", .{});
    };
    const allocator = gpa.allocator();

    var count: u64 = 0;
    scanDirectoryRecursive(allocator, args.root_path, &count) catch {
        return 0; // Return 0 on error
    };

    return count;
}

// Fast file counting function (useful for quick estimates)
pub fn count_audio_files(args: struct { root_path: []const u8 }) !u64 {
    const path_slice = args.root_path;

    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer if (gpa.deinit() == .leak) {
        std.debug.print("Memory leak detected in count_audio_files!\n", .{});
    };
    const allocator = gpa.allocator();

    var count: u64 = 0;

    // Simple recursive counting without storing file info
    var dir = std.fs.openDirAbsolute(path_slice, .{ .iterate = true }) catch {
        return 0; // Return 0 if can't access directory
    };
    defer dir.close();

    var walker = dir.walk(allocator) catch {
        return 0;
    };
    defer walker.deinit();

    while (walker.next() catch null) |entry| {
        if (entry.kind == .file and isAudioFile(entry.basename)) {
            count += 1;
        }
    }

    return count;
}

// Utility function to check if a single file is an audio file
pub fn is_audio_file(args: struct { filename: []const u8 }) bool {
    return isAudioFile(args.filename);
}

// Get count of supported audio extensions
pub fn get_supported_extensions_count() u32 {
    return AUDIO_EXTENSIONS.len;
}

// Benchmark function to compare with Python implementations
pub fn benchmark_directory(args: struct { root_path: []const u8, iterations: u32 }) f64 {
    if (args.iterations == 0) return 0.0;

    var total_time_ns: u64 = 0;

    var i: u32 = 0;
    while (i < args.iterations) : (i += 1) {
        const start_time = std.time.nanoTimestamp();
        _ = count_audio_files(.{ .root_path = args.root_path }) catch 0;
        const end_time = std.time.nanoTimestamp();

        total_time_ns += @intCast(end_time - start_time);
    }

    return @as(f64, @floatFromInt(total_time_ns)) / @as(f64, @floatFromInt(args.iterations)) / 1_000_000.0;
}

// Register this module with Python
comptime {
    py.rootmodule(@This());
}
