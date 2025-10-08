#!/usr/bin/env python3
"""Test script for the enhanced Zig scanning module."""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.scan_async import ZigScannerAsync


async def test_basic_scan():
    """Test basic scanning functionality."""
    print("\n=== Testing Basic Scan ===")

    scanner = ZigScannerAsync()

    # Use a test directory (current directory or specify a path)
    test_path = Path.home() / "Music"  # Adjust as needed
    if not test_path.exists():
        test_path = Path.cwd()

    print(f"Scanning: {test_path}")

    # Progress callback
    async def progress_callback(progress):
        print(
            f"Progress: {progress.percentage:.1f}% - {progress.processed_files} files ({progress.files_per_second:.1f} files/sec)"
        )

    start_time = time.time()
    stats = await scanner.scan_directory_async(
        root_path=str(test_path),
        progress_callback=progress_callback,
    )
    elapsed = time.time() - start_time

    print("\nScan Results:")
    print(f"  Total files: {stats.total_files}")
    print(f"  Total directories: {stats.total_dirs}")
    print(f"  Total size: {stats.total_size / (1024**3):.2f} GB")
    print(f"  Scan duration: {stats.scan_duration_ms:.2f} ms")
    print(f"  Files per second: {stats.files_per_second:.2f}")
    print(f"  Python elapsed time: {elapsed:.2f} seconds")

    return stats


async def test_file_discovery():
    """Test fast file discovery."""
    print("\n=== Testing File Discovery ===")

    scanner = ZigScannerAsync()
    test_path = Path.home() / "Music"
    if not test_path.exists():
        test_path = Path.cwd()

    print(f"Discovering files in: {test_path}")

    # Test count only
    start_time = time.time()
    count = await scanner.discover_files(str(test_path), return_list=False)
    elapsed = time.time() - start_time

    print(f"Found {count} audio files in {elapsed:.2f} seconds")
    print("Note: Using enhanced Zig scanner for file discovery")

    return count


async def test_metadata_extraction():
    """Test metadata extraction."""
    print("\n=== Testing Metadata Extraction ===")

    scanner = ZigScannerAsync()
    test_path = Path.home() / "Music"
    if not test_path.exists():
        test_path = Path.cwd()

    # Get some files to test
    files = await scanner.discover_files(str(test_path), return_list=True)

    if not files:
        print("No audio files found to test metadata extraction")
        return

    # Test batch metadata extraction (first 5 files)
    test_files = files[:5]
    print(f"Extracting metadata for {len(test_files)} files...")

    start_time = time.time()
    metadata_list = await scanner.extract_metadata_batch(test_files)
    elapsed = time.time() - start_time

    print(f"Extracted metadata in {elapsed:.3f} seconds")

    for metadata in metadata_list:
        print(f"\n{metadata.filename}:")
        print(f"  Path: {metadata.path}")
        print(f"  Size: {metadata.size / (1024**2):.2f} MB")
        print(f"  Modified: {time.ctime(metadata.modified)}")
        print(f"  Extension: {metadata.extension}")


async def test_benchmark():
    """Test benchmarking functionality."""
    print("\n=== Testing Benchmark ===")

    scanner = ZigScannerAsync()
    test_path = Path.home() / "Music"
    if not test_path.exists():
        test_path = Path.cwd()

    print(f"Benchmarking: {test_path}")
    print("Running 3 iterations with warmup...")

    results = await scanner.benchmark_performance(
        root_path=str(test_path),
        iterations=3,
        warmup=True,
    )

    print("\nBenchmark Results:")
    print(f"  Iterations: {results['iterations']}")
    print(f"  Total files: {results['total_files']}")
    print(f"  Average time: {results['avg_time_ms']:.2f} ms")
    print(f"  Min time: {results['min_time_ms']:.2f} ms")
    print(f"  Max time: {results['max_time_ms']:.2f} ms")

    if 'std_dev_ms' in results:
        print(f"  Std deviation: {results.get('std_dev_ms', 0):.2f} ms")

    print(f"  Files/second: {results['files_per_second']:.2f}")

    if 'timings' in results:
        print(f"  Individual timings: {[f'{t:.2f}' for t in results['timings']]}")


async def test_system_info():
    """Test system info retrieval."""
    print("\n=== Testing System Info ===")

    scanner = ZigScannerAsync()
    cpu_count = scanner.get_system_info()

    print("System Information:")
    print(f"  cpu_count: {cpu_count}")
    print("  Note: Enhanced scanner returns simplified data (CPU count only)")


async def test_websocket_simulation():
    """Simulate WebSocket communication."""
    print("\n=== Testing WebSocket Simulation ===")

    scanner = ZigScannerAsync()
    test_path = Path.home() / "Music"
    if not test_path.exists():
        test_path = Path.cwd()

    print(f"Simulating WebSocket scan of: {test_path}")

    # Mock WebSocket class for testing
    class MockWebSocket:
        async def send_json(self, data):
            msg_type = data.get('type', 'unknown')
            if msg_type == 'scan_progress':
                progress = data['data']
                print(f"[WS] Progress: {progress['percentage']:.1f}% - {progress['current_path']}")

    mock_ws = MockWebSocket()

    # Progress callback for WebSocket
    async def ws_progress(progress):
        await mock_ws.send_json(
            {
                'type': 'scan_progress',
                'data': {
                    'total_files': progress.total_files,
                    'processed_files': progress.processed_files,
                    'current_path': progress.current_path,
                    'percentage': progress.percentage,
                    'files_per_second': progress.files_per_second,
                    'estimated_time_remaining': progress.estimated_time_remaining,
                },
            }
        )

    stats = await scanner.scan_directory_async(
        root_path=str(test_path),
        batch_size=50,  # Smaller batches for more frequent updates
        websocket=mock_ws,
        progress_callback=ws_progress,
    )

    print(f"\nWebSocket scan completed: {stats.total_files} files")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Enhanced Zig Scanner Test Suite")
    print("=" * 60)

    try:
        # Check if Zig module is available
        try:
            from core import _scan_enhanced

            print("✓ Enhanced Zig module available")
        except ImportError:
            print("✗ Enhanced Zig module not available - using Python fallback")
            try:
                from core import _scan

                print("✓ Basic Zig module available")
            except ImportError:
                print("✗ No Zig module available - using pure Python")

        # Run tests
        await test_system_info()
        await test_file_discovery()
        await test_basic_scan()
        await test_metadata_extraction()
        await test_benchmark()
        await test_websocket_simulation()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
