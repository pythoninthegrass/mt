const std = @import("std");
const py = @import("pydust");

// Audio file extensions we recognize
const AUDIO_EXTENSIONS = [_][]const u8{
    ".mp3", ".flac", ".m4a", ".ogg", ".wav", ".wma", ".aac", ".opus", ".m4p", ".mp4"
};

// File information structure that will be returned to Python
pub const FileInfo = py.class(struct {
    path: py.PyString,
    name: py.PyString,
    size: u64,
    modified_time: f64,

    const Self = @This();

    pub fn __init__(self: *Self, path: py.PyString, name: py.PyString, size: u64, modified_time: f64) void {
        self.path = path;
        self.name = name;
        self.size = size;
        self.modified_time = modified_time;
    }
});

// Scan statistics structure
pub const ScanStats = py.class(struct {
    total_files: u64,
    total_size: u64,
    scan_time_ms: u64,
    directories_scanned: u64,

    const Self = @This();

    pub fn __init__(self: *Self) void {
        self.total_files = 0;
        self.total_size = 0;
        self.scan_time_ms = 0;
        self.directories_scanned = 0;
    }

    pub fn files_per_second(self: *Self) f64 {
        if (self.scan_time_ms == 0) return 0.0;
        return @as(f64, @floatFromInt(self.total_files)) / (@as(f64, @floatFromInt(self.scan_time_ms)) / 1000.0);
    }

    pub fn mb_per_second(self: *Self) f64 {
        if (self.scan_time_ms == 0) return 0.0;
        const mb_size = @as(f64, @floatFromInt(self.total_size)) / (1024.0 * 1024.0);
        return mb_size / (@as(f64, @floatFromInt(self.scan_time_ms)) / 1000.0);
    }
});

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

// Recursive directory scanner
fn scanDirectoryRecursive(
    allocator: std.mem.Allocator,
    path: []const u8,
    file_list: *std.ArrayList(FileInfo),
    stats: *ScanStats
) !void {
    var dir = std.fs.openDirAbsolute(path, .{ .iterate = true }) catch |err| {
        // Skip directories we can't access (permissions, etc.)
        if (err == error.AccessDenied or err == error.FileNotFound) {
            return;
        }
        return err;
    };
    defer dir.close();

    stats.directories_scanned += 1;

    var walker = dir.walk(allocator) catch |err| {
        return err;
    };
    defer walker.deinit();

    while (walker.next() catch null) |entry| {
        switch (entry.kind) {
            .file => {
                if (isAudioFile(entry.basename)) {
                    const stat = entry.dir.statFile(entry.basename) catch continue;

                    // Convert timestamps
                    const modified_time = nanoToUnixSeconds(stat.mtime);

                    // Create Python strings for path and filename
                    const full_path = try std.fmt.allocPrint(allocator, "{s}/{s}", .{ path, entry.path });
                    defer allocator.free(full_path);

                    const path_str = try py.PyString.fromSlice(full_path);
                    const name_str = try py.PyString.fromSlice(entry.basename);

                    // Create FileInfo object
                    const file_info = try py.init(FileInfo, .{
                        .path = path_str,
                        .name = name_str,
                        .size = stat.size,
                        .modified_time = modified_time,
                    });

                    try file_list.append(file_info);

                    stats.total_files += 1;
                    stats.total_size += stat.size;
                }
            },
            .directory => {
                // Skip hidden directories and common non-music directories
                if (entry.basename[0] == '.' or
                    std.mem.eql(u8, entry.basename, "__pycache__") or
                    std.mem.eql(u8, entry.basename, "Thumbs.db") or
                    std.mem.eql(u8, entry.basename, ".DS_Store")) {
                    continue;
                }

                // Continue recursion
                const subdir_path = try std.fmt.allocPrint(allocator, "{s}/{s}", .{ path, entry.path });
                defer allocator.free(subdir_path);

                try scanDirectoryRecursive(allocator, subdir_path, file_list, stats);
            },
            else => {},
        }
    }
}

// Main scanning function exposed to Python
pub fn scan_music_directory(root_path: py.PyString) !py.PyObject {
    const start_time = std.time.nanoTimestamp();

    // Convert Python string to Zig slice
    const path_slice = root_path.asSlice();

    // Use page allocator for simplicity (could optimize with arena allocator)
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer if (gpa.deinit() == .leak) {
        std.debug.print("Memory leak detected!\n", .{});
    };
    const allocator = gpa.allocator();

    // Initialize collections
    var file_list = std.ArrayList(FileInfo).init(allocator);
    defer file_list.deinit();

    var stats = try py.init(ScanStats, .{});

    // Perform the scan
    try scanDirectoryRecursive(allocator, path_slice, &file_list, stats);

    // Calculate timing
    const end_time = std.time.nanoTimestamp();
    stats.scan_time_ms = @intCast(@divTrunc(end_time - start_time, 1_000_000));

    // Convert file list to Python list
    const py_list = try py.PyList.empty();
    for (file_list.items) |file_info| {
        try py_list.append(file_info);
    }

    // Return a tuple of (files, stats)
    const result_tuple = try py.PyTuple.new(2);
    try result_tuple.setItem(0, py_list);
    try result_tuple.setItem(1, stats);

    return result_tuple;
}

// Fast file counting function (useful for quick estimates)
pub fn count_audio_files(root_path: py.PyString) !u64 {
    const path_slice = root_path.asSlice();

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
pub fn is_audio_file(filename: py.PyString) bool {
    return isAudioFile(filename.asSlice());
}

// Get list of supported audio extensions
pub fn get_supported_extensions() !py.PyList {
    const py_list = try py.PyList.empty();

    for (AUDIO_EXTENSIONS) |ext| {
        const ext_str = try py.PyString.fromSlice(ext);
        try py_list.append(ext_str);
    }

    return py_list;
}

// Benchmark function to compare with Python implementations
pub fn benchmark_directory(root_path: py.PyString, iterations: u32) !py.PyObject {
    if (iterations == 0) return py.PyFloat.from(0.0);

    const path_slice = root_path.asSlice();

    var total_time_ns: u64 = 0;
    var total_files: u64 = 0;

    var i: u32 = 0;
    while (i < iterations) : (i += 1) {
        const start_time = std.time.nanoTimestamp();
        const file_count = try count_audio_files(root_path);
        const end_time = std.time.nanoTimestamp();

        total_time_ns += @intCast(end_time - start_time);
        total_files = file_count; // All iterations should find the same number
    }

    const avg_time_ms = @as(f64, @floatFromInt(total_time_ns)) / @as(f64, @floatFromInt(iterations)) / 1_000_000.0;
    const files_per_second = if (avg_time_ms > 0)
        @as(f64, @floatFromInt(total_files)) / (avg_time_ms / 1000.0)
    else
        0.0;

    // Return benchmark results as a dict
    const result_dict = try py.PyDict.empty();
    try result_dict.setItem("avg_time_ms", py.PyFloat.from(avg_time_ms));
    try result_dict.setItem("total_files", py.PyLong.from(@intCast(total_files)));
    try result_dict.setItem("files_per_second", py.PyFloat.from(files_per_second));
    try result_dict.setItem("iterations", py.PyLong.from(@intCast(iterations)));

    return result_dict;
}

// Register this module with Python
comptime {
    py.rootmodule(@This());
}
