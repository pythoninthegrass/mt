#!/usr/bin/env python3
"""Simple test for the enhanced Zig scanning module."""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.scan_async import ZigScannerAsync


async def test_enhanced_scanner():
    """Test the enhanced Zig scanner."""
    print("Testing Enhanced Zig Scanner")
    print("=" * 40)

    scanner = ZigScannerAsync()

    # Check if enhanced scanner is available
    if hasattr(scanner.zig_scanner, 'scan_music_directory_enhanced'):
        print("✓ Enhanced Zig scanner is available")
    else:
        print("✗ Enhanced Zig scanner not available")
        return

    # Use a test directory
    test_path = Path.home() / "Music"
    if not test_path.exists():
        test_path = Path.cwd()

    print(f"Testing with directory: {test_path}")

    # Test system info
    cpu_count = scanner.get_system_info()
    print(f"System CPU count: {cpu_count}")

    # Test file discovery
    print("\nTesting file discovery...")
    start_time = time.time()
    count = await scanner.discover_files(str(test_path), return_list=False)
    elapsed = time.time() - start_time
    print(f"Found {count} audio files in {elapsed:.2f} seconds")

    # Test basic scan
    print("\nTesting directory scan...")
    start_time = time.time()
    stats = await scanner.scan_directory_async(
        root_path=str(test_path),
        max_depth=3,  # Limit depth for faster testing
    )
    elapsed = time.time() - start_time

    print("Scan Results:")
    print(f"  Total files: {stats.total_files}")
    print(f"  Total size: {stats.total_size / (1024**2):.2f} MB")
    print(f"  Scan duration: {stats.scan_duration_ms:.2f} ms")
    print(f"  Files per second: {stats.files_per_second:.2f}")
    print(f"  Total Python time: {elapsed:.2f} seconds")

    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_scanner())
