#!/usr/bin/env python
"""Generate synthetic music libraries for benchmarking.

Supports three dataset types:
- shape: Tiny files with minimal audio headers (filesystem/DB stress)
- clone: APFS clones of real audio files (realistic mutagen parsing)
- pathological: Edge cases (deep nesting, unicode, corrupt files)
"""
import argparse
import platform
import random
import shutil
import subprocess
import sys
from pathlib import Path
from tests.bench.logging_config import setup_benchmark_logger

# Setup logging
logger = setup_benchmark_logger("make_synth_library")


def write_minimal_mp3_header(path: Path) -> None:
    """Write minimal valid MP3 ID3v2 header."""
    # ID3v2.3 header: "ID3" + version + flags + size
    header = b"ID3\x03\x00\x00\x00\x00\x00\x00"
    path.write_bytes(header)


def write_minimal_flac_header(path: Path) -> None:
    """Write minimal valid FLAC header."""
    # FLAC magic "fLaC" + minimal STREAMINFO block
    header = b"fLaC" + b"\x00" * 38
    path.write_bytes(header)


def write_minimal_m4a_header(path: Path) -> None:
    """Write minimal valid M4A/MP4 header."""
    # Minimal MP4: ftyp atom
    ftyp = b"\x00\x00\x00\x20ftyp"  # 32 bytes ftyp atom
    ftyp += b"M4A " + b"\x00" * 16
    path.write_bytes(ftyp)


def choose_extension(ext_ratios: dict[str, float]) -> str:
    """Choose random extension based on distribution.

    Args:
        ext_ratios: Dict of extension to ratio (e.g., {"mp3": 0.75})

    Returns:
        Extension string like "mp3"
    """
    rand = random.random()
    cumulative = 0.0
    for ext, ratio in ext_ratios.items():
        cumulative += ratio
        if rand < cumulative:
            return ext
    return list(ext_ratios.keys())[-1]


def generate_shape_dataset(
    output_root: Path,
    track_count: int = 41000,
    ext_ratios: dict[str, float] | None = None,
) -> None:
    """Generate shape-only dataset (tiny files, filesystem stress).

    Args:
        output_root: Root directory for synthetic library
        track_count: Number of tracks to generate
        ext_ratios: Extension distribution ratios
    """
    if ext_ratios is None:
        ext_ratios = {"mp3": 0.75, "flac": 0.15, "m4a": 0.08, "ogg": 0.02}

    print(f"Generating shape dataset: {track_count:,} tracks")
    print(f"Output: {output_root}")
    print(f"Extension ratios: {ext_ratios}")
    print("\nNote: Shape dataset files have minimal headers that will cause")
    print("      mutagen parsing errors (e.g., 'can't sync to MPEG frame').")
    print("      This is expected - the dataset tests filesystem/DB performance,")
    print("      not metadata parsing. Files will be added with filename-only metadata.\n")

    logger.info(f"Generating shape dataset: {track_count:,} tracks")
    logger.info(f"Output: {output_root}")
    logger.info(f"Extension ratios: {ext_ratios}")

    # Clean output directory
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    # Calculate structure
    artists = 500  # ~82 tracks per artist
    albums_per_artist = 5  # ~16 tracks per album

    track_num = 0
    for artist_idx in range(artists):
        if track_num >= track_count:
            break

        artist_dir = output_root / f"Artist_{artist_idx:03d}"
        artist_dir.mkdir(exist_ok=True)

        for album_idx in range(albums_per_artist):
            if track_num >= track_count:
                break

            album_dir = artist_dir / f"Album_{album_idx:02d}"
            album_dir.mkdir(exist_ok=True)

            tracks_in_album = 16
            for track_idx in range(tracks_in_album):
                if track_num >= track_count:
                    break

                ext = choose_extension(ext_ratios)
                track_path = album_dir / f"{track_idx:02d} - Track_{track_num:05d}.{ext}"

                # Write minimal header based on extension
                if ext == "mp3":
                    write_minimal_mp3_header(track_path)
                elif ext == "flac":
                    write_minimal_flac_header(track_path)
                elif ext == "m4a":
                    write_minimal_m4a_header(track_path)
                else:
                    # Generic tiny file
                    track_path.write_bytes(b"\x00" * 10)

                track_num += 1

                if track_num % 5000 == 0:
                    print(f"  Generated {track_num:,} tracks...")
                    logger.info(f"Generated {track_num:,} tracks...")

    print(f"✓ Shape dataset complete: {track_num:,} tracks")
    logger.info(f"Shape dataset complete: {track_num:,} tracks")
    logger.info(f"SUMMARY: shape | {track_num:,} tracks generated")


def clone_file(src: Path, dst: Path) -> None:
    """Platform-aware file cloning.

    Args:
        src: Source file path
        dst: Destination file path
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    system = platform.system()
    if system == "Darwin":
        # macOS: APFS clone (copy-on-write)
        subprocess.run(["cp", "-c", str(src), str(dst)], check=True)
    elif system == "Linux":
        # Linux: hardlink fallback
        dst.hardlink_to(src)
    else:
        # Windows: regular copy
        shutil.copy2(src, dst)


def collect_seed_files(seed_dirs: list[Path]) -> list[Path]:
    """Collect audio files from seed directories.

    Args:
        seed_dirs: List of directories to search for audio files

    Returns:
        List of audio file paths
    """
    seed_files = []
    extensions = ["*.mp3", "*.flac", "*.m4a", "*.ogg", "*.wav"]

    for seed_dir in seed_dirs:
        if not seed_dir.exists():
            print(f"Warning: Seed directory not found: {seed_dir}")
            continue

        for ext_pattern in extensions:
            seed_files.extend(seed_dir.rglob(ext_pattern))

    return seed_files


def sample_by_size_distribution(files: list[Path], target_count: int = 400) -> list[Path]:
    """Sample files by size distribution for variety.

    Args:
        files: List of file paths
        target_count: Number of files to sample

    Returns:
        Sampled list of files
    """
    if len(files) <= target_count:
        return files

    # Get file sizes
    file_sizes = [(f, f.stat().st_size) for f in files if f.exists()]
    file_sizes.sort(key=lambda x: x[1])

    # Sample across size distribution
    sampled = []
    step = len(file_sizes) // target_count
    for i in range(0, len(file_sizes), max(step, 1)):
        if len(sampled) >= target_count:
            break
        sampled.append(file_sizes[i][0])

    return sampled


def generate_clone_dataset(
    output_root: Path,
    seed_dirs: list[Path],
    track_count: int = 41000,
) -> None:
    """Generate clone-based dataset (APFS clones of real files).

    Args:
        output_root: Root directory for synthetic library
        seed_dirs: Directories containing real audio files
        track_count: Number of tracks to generate
    """
    print(f"Generating clone dataset: {track_count:,} tracks")
    print(f"Output: {output_root}")
    print(f"Seed directories: {[str(d) for d in seed_dirs]}")

    logger.info(f"Generating clone dataset: {track_count:,} tracks")
    logger.info(f"Output: {output_root}")
    logger.info(f"Seed directories: {[str(d) for d in seed_dirs]}")

    # Collect seed files
    seed_files = collect_seed_files(seed_dirs)
    if not seed_files:
        print("Error: No seed files found in provided directories")
        logger.error("No seed files found in provided directories")
        sys.exit(1)

    print(f"Found {len(seed_files)} seed files")
    logger.info(f"Found {len(seed_files)} seed files")

    # Sample for variety
    seed_files = sample_by_size_distribution(seed_files, target_count=400)
    print(f"Sampled {len(seed_files)} seed files for cloning")
    logger.info(f"Sampled {len(seed_files)} seed files for cloning")

    # Clean output directory
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    # Clone to target count
    track_num = 0
    seed_idx = 0

    while track_num < track_count:
        seed = seed_files[seed_idx % len(seed_files)]
        seed_idx += 1

        # Create artist/album structure
        artist_idx = track_num // 100
        album_idx = track_num // 16

        artist_dir = output_root / f"Artist_{artist_idx:03d}"
        album_dir = artist_dir / f"Album_{album_idx:02d}"
        album_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        track_idx = track_num % 16
        dst = album_dir / f"{track_idx:02d} - {seed.stem}_{track_num:05d}{seed.suffix}"

        # Clone file
        try:
            clone_file(seed, dst)
            track_num += 1

            if track_num % 5000 == 0:
                print(f"  Cloned {track_num:,} tracks...")
                logger.info(f"Cloned {track_num:,} tracks...")
        except Exception as e:
            print(f"Warning: Failed to clone {seed}: {e}")
            logger.warning(f"Failed to clone {seed}: {e}")
            continue

    print(f"✓ Clone dataset complete: {track_num:,} tracks")
    logger.info(f"Clone dataset complete: {track_num:,} tracks")
    logger.info(f"SUMMARY: clone | {track_num:,} tracks generated")


def generate_pathological_dataset(output_root: Path) -> None:
    """Generate pathological edge case dataset.

    Args:
        output_root: Root directory for synthetic library
    """
    print("Generating pathological dataset")
    print(f"Output: {output_root}")

    logger.info("Generating pathological dataset")
    logger.info(f"Output: {output_root}")

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    track_num = 0

    # 1. Flat directory with 2000+ files (compilation stress)
    print("  Creating flat directory (2000 files)...")
    flat_dir = output_root / "Compilation_Flat"
    flat_dir.mkdir()
    for i in range(2000):
        track_path = flat_dir / f"Track_{i:04d}.mp3"
        write_minimal_mp3_header(track_path)
        track_num += 1

    # 2. Deep nesting (15 levels)
    print("  Creating deep nesting (15 levels)...")
    deep_dir = output_root
    for level in range(15):
        deep_dir = deep_dir / f"Level_{level:02d}"
        deep_dir.mkdir(exist_ok=True)
    for i in range(10):
        track_path = deep_dir / f"Deep_Track_{i:02d}.mp3"
        write_minimal_mp3_header(track_path)
        track_num += 1

    # 3. Unicode and emoji filenames
    print("  Creating unicode filenames...")
    unicode_dir = output_root / "Unicode_Tests"
    unicode_dir.mkdir()
    unicode_names = [
        "Track_日本語.mp3",
        "Track_Émilie.mp3",
        "Track_🎵_Music.mp3",
        "Track_Привет.mp3",
        "Track_العربية.mp3",
    ]
    for name in unicode_names:
        track_path = unicode_dir / name
        write_minimal_mp3_header(track_path)
        track_num += 1

    # 4. Very long filenames (250 chars)
    print("  Creating long filenames...")
    long_dir = output_root / "Long_Names"
    long_dir.mkdir()
    for i in range(10):
        long_name = f"Track_{'A' * 200}_{i:02d}.mp3"
        track_path = long_dir / long_name
        write_minimal_mp3_header(track_path)
        track_num += 1

    # 5. Corrupt/truncated files
    print("  Creating corrupt files...")
    corrupt_dir = output_root / "Corrupt_Files"
    corrupt_dir.mkdir()
    for i in range(10):
        track_path = corrupt_dir / f"Corrupt_{i:02d}.mp3"
        track_path.write_bytes(b"CORRUPT" * 10)
        track_num += 1

    # 6. Wrong extensions
    print("  Creating wrong extension files...")
    wrong_ext_dir = output_root / "Wrong_Extensions"
    wrong_ext_dir.mkdir()
    for i in range(5):
        # FLAC content with .mp3 extension
        track_path = wrong_ext_dir / f"Wrong_{i:02d}.mp3"
        write_minimal_flac_header(track_path)
        track_num += 1

    print(f"✓ Pathological dataset complete: {track_num:,} files")
    logger.info(f"Pathological dataset complete: {track_num:,} files")
    logger.info(f"SUMMARY: pathological | {track_num:,} files generated")


def main():
    """Main entry point."""
    try:
        run_generator()
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_generator():
    """Run synthetic library generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic music libraries for benchmarking"
    )
    parser.add_argument(
        "--mode",
        choices=["shape", "clone", "pathological", "all"],
        default="shape",
        help="Dataset generation mode",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("/tmp/mt-bench/library"),
        help="Output root directory (default: /tmp/mt-bench/library)",
    )
    parser.add_argument(
        "--tracks",
        type=int,
        default=41000,
        help="Number of tracks to generate (default: 41000)",
    )
    parser.add_argument(
        "--seed-dir",
        type=Path,
        action="append",
        dest="seed_dirs",
        help="Seed directory for clone mode (can be specified multiple times)",
    )
    parser.add_argument(
        "--ext-ratio",
        type=str,
        default="mp3=0.75,flac=0.15,m4a=0.08,ogg=0.02",
        help="Extension ratios (default: mp3=0.75,flac=0.15,m4a=0.08,ogg=0.02)",
    )

    args = parser.parse_args()

    # Parse extension ratios
    ext_ratios = {}
    for pair in args.ext_ratio.split(","):
        ext, ratio = pair.split("=")
        ext_ratios[ext.strip()] = float(ratio)

    # Safety check
    if "/.mt/" in str(args.out_root) or "/Music/" in str(args.out_root):
        print("Error: Output path looks like production directory")
        print(f"Got: {args.out_root}")
        print("Use /tmp/mt-bench/ for safety")
        sys.exit(1)

    # Generate datasets
    if args.mode == "shape":
        generate_shape_dataset(args.out_root, args.tracks, ext_ratios)

    elif args.mode == "clone":
        if not args.seed_dirs:
            print("Error: --seed-dir required for clone mode")
            sys.exit(1)
        generate_clone_dataset(args.out_root, args.seed_dirs, args.tracks)

    elif args.mode == "pathological":
        pathological_root = args.out_root / "pathological"
        generate_pathological_dataset(pathological_root)

    elif args.mode == "all":
        print("\n=== Generating all datasets ===\n")

        # Shape
        shape_root = args.out_root / "shape"
        generate_shape_dataset(shape_root, args.tracks, ext_ratios)
        print()

        # Clone
        if args.seed_dirs:
            clone_root = args.out_root / "clone"
            generate_clone_dataset(clone_root, args.seed_dirs, args.tracks)
            print()
        else:
            print("Skipping clone dataset (no --seed-dir provided)")

        # Pathological
        pathological_root = args.out_root / "pathological"
        generate_pathological_dataset(pathological_root)

    print("\n✓ All done!")


if __name__ == "__main__":
    main()
