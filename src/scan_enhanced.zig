const std = @import("std");
const py = @import("pydust");

// Audio file extensions we recognize
const AUDIO_EXTENSIONS = [_][]const u8{ ".mp3", ".flac", ".m4a", ".ogg", ".wav", ".wma", ".aac", ".opus", ".m4p", ".mp4" };

// Progress callback type for WebSocket updates
pub const ProgressCallback = struct {
    total_files: u64,
    processed_files: u64,
    current_path: []const u8,
    percentage: f32,
};

// File metadata structure
pub const AudioFileInfo = struct {
    path: []const u8,
    filename: []const u8,
    size: u64,
    modified: f64, // Unix timestamp
    extension: []const u8,
};

// Scan configuration
pub const ScanConfig = struct {
    max_depth: u32 = 10,
    follow_symlinks: bool = false,
    skip_hidden: bool = true,
    batch_size: u32 = 100,
};

// Scan statistics for performance monitoring
pub const ScanStats = struct {
    total_files: u64,
    total_dirs: u64,
    total_size: u64,
    scan_duration_ms: f64,
    files_per_second: f64,
};

// Global context for async operations
const ScanContext = struct {
    allocator: std.mem.Allocator,
    config: ScanConfig,
    stats: ScanStats,
    callback_fn: ?*const fn (progress: ProgressCallback) void,
    batch_buffer: std.ArrayList(AudioFileInfo),
    
    fn init(allocator: std.mem.Allocator, config: ScanConfig) ScanContext {
        return .{
            .allocator = allocator,
            .config = config,
            .stats = .{
                .total_files = 0,
                .total_dirs = 0,
                .total_size = 0,
                .scan_duration_ms = 0,
                .files_per_second = 0,
            },
            .callback_fn = null,
            .batch_buffer = std.ArrayList(AudioFileInfo).init(allocator),
        };
    }
    
    fn deinit(self: *ScanContext) void {
        self.batch_buffer.deinit();
    }
};

// Check if a file has an audio extension
fn isAudioFile(filename: []const u8) bool {
    if (std.mem.lastIndexOf(u8, filename, ".")) |dot_index| {
        const extension = filename[dot_index..];
        
        for (AUDIO_EXTENSIONS) |audio_ext| {
            if (std.ascii.eqlIgnoreCase(extension, audio_ext)) {
                return true;
            }
        }
    }
    return false;
}

// Get file extension
fn getFileExtension(filename: []const u8) []const u8 {
    if (std.mem.lastIndexOf(u8, filename, ".")) |dot_index| {
        return filename[dot_index..];
    }
    return "";
}

// Convert nanosecond timestamp to Unix epoch seconds
fn nanoToUnixSeconds(nano_timestamp: i128) f64 {
    const NANOS_PER_SEC: i128 = 1_000_000_000;
    return @as(f64, @floatFromInt(@divTrunc(nano_timestamp, NANOS_PER_SEC)));
}

// Enhanced directory scanner with progress callbacks
fn scanDirectoryEnhanced(
    ctx: *ScanContext,
    path: []const u8,
    depth: u32,
    progress_callback: ?*const fn (ctx: *ScanContext, current_path: []const u8) void
) !void {
    // Check max depth
    if (depth > ctx.config.max_depth) return;
    
    var dir = std.fs.openDirAbsolute(path, .{ .iterate = true }) catch |err| {
        if (err == error.AccessDenied or err == error.FileNotFound) {
            return;
        }
        return err;
    };
    defer dir.close();
    
    ctx.stats.total_dirs += 1;
    
    var walker = dir.walk(ctx.allocator) catch |err| {
        return err;
    };
    defer walker.deinit();
    
    while (walker.next() catch null) |entry| {
        switch (entry.kind) {
            .file => {
                if (isAudioFile(entry.basename)) {
                    // Get file metadata
                    const full_path = try std.fmt.allocPrint(ctx.allocator, "{s}/{s}", .{ path, entry.path });
                    defer ctx.allocator.free(full_path);
                    
                    const stat = dir.statFile(entry.path) catch continue;
                    
                    const file_info = AudioFileInfo{
                        .path = full_path,
                        .filename = entry.basename,
                        .size = stat.size,
                        .modified = nanoToUnixSeconds(stat.mtime),
                        .extension = getFileExtension(entry.basename),
                    };
                    
                    // Add to batch buffer
                    try ctx.batch_buffer.append(file_info);
                    
                    ctx.stats.total_files += 1;
                    ctx.stats.total_size += stat.size;
                    
                    // Call progress callback if provided
                    if (progress_callback) |callback| {
                        callback(ctx, entry.path);
                    }
                    
                    // Flush batch if full
                    if (ctx.batch_buffer.items.len >= ctx.config.batch_size) {
                        // TODO: Send batch to Python for processing
                        ctx.batch_buffer.clearRetainingCapacity();
                    }
                }
            },
            .directory => {
                // Skip hidden directories if configured
                if (ctx.config.skip_hidden and entry.basename[0] == '.') {
                    continue;
                }
                
                // Skip common non-music directories
                if (std.mem.eql(u8, entry.basename, "__pycache__") or
                    std.mem.eql(u8, entry.basename, "node_modules") or
                    std.mem.eql(u8, entry.basename, ".git"))
                {
                    continue;
                }
                
                // Recurse into subdirectory
                const subdir_path = try std.fmt.allocPrint(ctx.allocator, "{s}/{s}", .{ path, entry.path });
                defer ctx.allocator.free(subdir_path);
                
                try scanDirectoryEnhanced(ctx, subdir_path, depth + 1, progress_callback);
            },
            .sym_link => {
                if (ctx.config.follow_symlinks) {
                    // Follow symlink if configured
                    const link_path = try std.fmt.allocPrint(ctx.allocator, "{s}/{s}", .{ path, entry.path });
                    defer ctx.allocator.free(link_path);
                    
                    // Check if it points to a directory
                    const stat = std.fs.cwd().statFile(link_path) catch continue;
                    if (stat.kind == .directory) {
                        try scanDirectoryEnhanced(ctx, link_path, depth + 1, progress_callback);
                    } else if (stat.kind == .file and isAudioFile(entry.basename)) {
                        ctx.stats.total_files += 1;
                        ctx.stats.total_size += stat.size;
                    }
                }
            },
            else => {},
        }
    }
}

// Async-compatible scan function with configuration
pub fn scan_music_directory_async(args: struct {
    root_path: []const u8,
    max_depth: u32 = 10,
    follow_symlinks: bool = false,
    skip_hidden: bool = true,
    batch_size: u32 = 100,
}) !py.PyObject {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer if (gpa.deinit() == .leak) {
        std.debug.print("Memory leak detected!\n", .{});
    };
    const allocator = gpa.allocator();
    
    const config = ScanConfig{
        .max_depth = args.max_depth,
        .follow_symlinks = args.follow_symlinks,
        .skip_hidden = args.skip_hidden,
        .batch_size = args.batch_size,
    };
    
    var ctx = ScanContext.init(allocator, config);
    defer ctx.deinit();
    
    const start_time = std.time.milliTimestamp();
    
    // Progress callback for WebSocket updates
    const progress_fn = struct {
        fn callback(context: *ScanContext, current_path: []const u8) void {
            _ = current_path;
            const progress = ProgressCallback{
                .total_files = context.stats.total_files,
                .processed_files = context.stats.total_files,
                .current_path = current_path,
                .percentage = 0.0, // Will be calculated by Python
            };
            _ = progress;
            // TODO: Call Python callback through pydust
        }
    }.callback;
    
    scanDirectoryEnhanced(&ctx, args.root_path, 0, progress_fn) catch |err| {
        std.debug.print("Scan error: {}\n", .{err});
        return err;
    };
    
    const end_time = std.time.milliTimestamp();
    ctx.stats.scan_duration_ms = @as(f64, @floatFromInt(end_time - start_time));
    
    if (ctx.stats.scan_duration_ms > 0) {
        ctx.stats.files_per_second = @as(f64, @floatFromInt(ctx.stats.total_files)) / (ctx.stats.scan_duration_ms / 1000.0);
    }
    
    // Return stats as Python dict
    const pydict = try py.PyDict.new();
    try pydict.setItem("total_files", try py.PyLong.from(ctx.stats.total_files));
    try pydict.setItem("total_dirs", try py.PyLong.from(ctx.stats.total_dirs));
    try pydict.setItem("total_size", try py.PyLong.from(ctx.stats.total_size));
    try pydict.setItem("scan_duration_ms", try py.PyFloat.from(ctx.stats.scan_duration_ms));
    try pydict.setItem("files_per_second", try py.PyFloat.from(ctx.stats.files_per_second));
    
    return pydict.asObject();
}

// Fast file discovery (just paths, no metadata)
pub fn discover_audio_files(args: struct { 
    root_path: []const u8,
    return_list: bool = false,
}) !py.PyObject {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer if (gpa.deinit() == .leak) {
        std.debug.print("Memory leak detected!\n", .{});
    };
    const allocator = gpa.allocator();
    
    var file_paths = std.ArrayList([]const u8).init(allocator);
    defer file_paths.deinit();
    
    var dir = std.fs.openDirAbsolute(args.root_path, .{ .iterate = true }) catch {
        const pylist = try py.PyList.new(0);
        return pylist.asObject();
    };
    defer dir.close();
    
    var walker = dir.walk(allocator) catch {
        const pylist = try py.PyList.new(0);
        return pylist.asObject();
    };
    defer walker.deinit();
    
    while (walker.next() catch null) |entry| {
        if (entry.kind == .file and isAudioFile(entry.basename)) {
            if (args.return_list) {
                const full_path = try std.fmt.allocPrint(allocator, "{s}/{s}", .{ args.root_path, entry.path });
                try file_paths.append(full_path);
            }
        }
    }
    
    if (args.return_list) {
        const pylist = try py.PyList.new(@intCast(file_paths.items.len));
        for (file_paths.items, 0..) |path, i| {
            const pystr = try py.PyString.from(path);
            try pylist.setItem(@intCast(i), pystr.asObject());
        }
        return pylist.asObject();
    } else {
        const count = file_paths.items.len;
        return try py.PyLong.from(count);
    }
}

// Extract metadata for a single file (for coordination with Python)
pub fn extract_file_metadata(args: struct { file_path: []const u8 }) !py.PyObject {
    const stat = std.fs.cwd().statFile(args.file_path) catch |err| {
        std.debug.print("Failed to stat file {s}: {}\n", .{ args.file_path, err });
        return py.PyNone.get();
    };
    
    const basename = std.fs.path.basename(args.file_path);
    
    // Create Python dict with metadata
    const pydict = try py.PyDict.new();
    try pydict.setItem("path", try py.PyString.from(args.file_path));
    try pydict.setItem("filename", try py.PyString.from(basename));
    try pydict.setItem("size", try py.PyLong.from(stat.size));
    try pydict.setItem("modified", try py.PyFloat.from(nanoToUnixSeconds(stat.mtime)));
    try pydict.setItem("extension", try py.PyString.from(getFileExtension(basename)));
    
    return pydict.asObject();
}

// Benchmark function with detailed metrics
pub fn benchmark_scan_performance(args: struct {
    root_path: []const u8,
    iterations: u32 = 3,
    warmup: bool = true,
}) !py.PyObject {
    if (args.iterations == 0) {
        return py.PyNone.get();
    }
    
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer if (gpa.deinit() == .leak) {
        std.debug.print("Memory leak detected!\n", .{});
    };
    const allocator = gpa.allocator();
    
    // Warmup run if requested
    if (args.warmup) {
        _ = discover_audio_files(.{ 
            .root_path = args.root_path,
            .return_list = false,
        }) catch {};
    }
    
    var timings = std.ArrayList(f64).init(allocator);
    defer timings.deinit();
    
    var total_files: u64 = 0;
    
    var i: u32 = 0;
    while (i < args.iterations) : (i += 1) {
        const start_time = std.time.nanoTimestamp();
        
        const result = try discover_audio_files(.{
            .root_path = args.root_path,
            .return_list = false,
        });
        
        const end_time = std.time.nanoTimestamp();
        const duration_ms = @as(f64, @floatFromInt(end_time - start_time)) / 1_000_000.0;
        
        try timings.append(duration_ms);
        
        // Get file count from result
        if (py.PyLong.from(result)) |pylong| {
            total_files = try pylong.asU64();
        } else |_| {}
    }
    
    // Calculate statistics
    var sum: f64 = 0;
    var min: f64 = timings.items[0];
    var max: f64 = timings.items[0];
    
    for (timings.items) |timing| {
        sum += timing;
        if (timing < min) min = timing;
        if (timing > max) max = timing;
    }
    
    const avg = sum / @as(f64, @floatFromInt(args.iterations));
    
    // Calculate standard deviation
    var variance: f64 = 0;
    for (timings.items) |timing| {
        const diff = timing - avg;
        variance += diff * diff;
    }
    variance /= @as(f64, @floatFromInt(args.iterations));
    const std_dev = @sqrt(variance);
    
    // Create result dictionary
    const pydict = try py.PyDict.new();
    try pydict.setItem("iterations", try py.PyLong.from(args.iterations));
    try pydict.setItem("total_files", try py.PyLong.from(total_files));
    try pydict.setItem("avg_time_ms", try py.PyFloat.from(avg));
    try pydict.setItem("min_time_ms", try py.PyFloat.from(min));
    try pydict.setItem("max_time_ms", try py.PyFloat.from(max));
    try pydict.setItem("std_dev_ms", try py.PyFloat.from(std_dev));
    
    if (avg > 0) {
        const files_per_second = @as(f64, @floatFromInt(total_files)) / (avg / 1000.0);
        try pydict.setItem("files_per_second", try py.PyFloat.from(files_per_second));
    }
    
    // Include individual timings
    const pytimings = try py.PyList.new(@intCast(timings.items.len));
    for (timings.items, 0..) |timing, j| {
        try pytimings.setItem(@intCast(j), try py.PyFloat.from(timing));
    }
    try pydict.setItem("timings", pytimings.asObject());
    
    return pydict.asObject();
}

// Batch processing support for parallel metadata extraction
pub fn process_file_batch(args: struct { file_paths: py.PyObject }) !py.PyObject {
    // Convert Python list to Zig array
    const pylist = try py.PyList.from(args.file_paths);
    const count = try pylist.len();
    
    const results = try py.PyList.new(@intCast(count));
    
    var i: usize = 0;
    while (i < count) : (i += 1) {
        const item = try pylist.getItem(@intCast(i));
        const pystr = try py.PyString.from(item);
        const path = try pystr.asSlice();
        
        const metadata = try extract_file_metadata(.{ .file_path = path });
        try results.setItem(@intCast(i), metadata);
    }
    
    return results.asObject();
}

// Get system information for performance tuning
pub fn get_system_info() !py.PyObject {
    const pydict = try py.PyDict.new();
    
    // CPU count
    const cpu_count = std.Thread.getCpuCount() catch 1;
    try pydict.setItem("cpu_count", try py.PyLong.from(cpu_count));
    
    // Page size
    const page_size = std.mem.page_size;
    try pydict.setItem("page_size", try py.PyLong.from(page_size));
    
    // Supported extensions count
    try pydict.setItem("supported_extensions", try py.PyLong.from(AUDIO_EXTENSIONS.len));
    
    return pydict.asObject();
}

// Register this module with Python
comptime {
    py.rootmodule(@This());
}