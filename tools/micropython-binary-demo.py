"""MicroPython binary compression comparison demo.

This script reads the two UF2 firmware files from tests/binaries and generates
compressed diffs using all available compression algorithms. It also compresses
the newer firmware file standalone for comparison.

The output is formatted for easy inclusion in README documentation.
"""

import sys
from pathlib import Path
from typing import cast

# Add the project root to the path so we can import hdiffpatch
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import hdiffpatch


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def compress_data_with_config(data: bytes, compression_config) -> bytes:
    """Compress data using the specified compression configuration."""
    # Create a dummy diff from empty data to utilize compression
    empty_data = b""
    diff = hdiffpatch.diff(empty_data, data, compression=compression_config)
    return diff


def main():
    """Main demo function."""
    # Paths to the UF2 files
    binaries_dir = project_root / "tests" / "binaries"
    old_firmware_path = binaries_dir / "RPI_PICO-20241129-v1.24.1.uf2"
    new_firmware_path = binaries_dir / "RPI_PICO-20250415-v1.25.0.uf2"

    # Check if files exist
    if not old_firmware_path.exists():
        print(f"Error: {old_firmware_path} not found")
        return 1
    if not new_firmware_path.exists():
        print(f"Error: {new_firmware_path} not found")
        return 1

    # Read firmware files
    print("Reading firmware files...")
    old_firmware = old_firmware_path.read_bytes()
    new_firmware = new_firmware_path.read_bytes()

    print(f"Old firmware size: {format_size(len(old_firmware))}")
    print(f"New firmware size: {format_size(len(new_firmware))}")
    print()

    # All available compression types with 12-bit window size (4096 bytes) where supported
    compression_configs = [
        ("none", hdiffpatch.COMPRESSION_NONE),
        ("zlib", hdiffpatch.ZlibConfig(window=12)),
        ("zstd", hdiffpatch.ZStdConfig(window=12)),
        ("lzma", hdiffpatch.LzmaConfig(window=12)),
        ("lzma2", hdiffpatch.Lzma2Config(window=12)),
        ("bzip2", hdiffpatch.BZip2Config()),  # No window size parameter
        ("tamp", hdiffpatch.TampConfig(window=12)),
    ]

    # Create uncompressed diff first
    print("Creating uncompressed diff...")
    uncompressed_diff = hdiffpatch.diff(old_firmware, new_firmware, compression=hdiffpatch.COMPRESSION_NONE)

    # Generate all compressed diffs using recompress
    print("Generating compressed diffs...")
    results = []

    for compression_name, compression_config in compression_configs:
        diff_data = hdiffpatch.recompress(uncompressed_diff, compression=compression_config)

        results.append(
            {
                "compression": compression_name,
                "diff_size": len(diff_data),
                "description": f"{compression_name.upper()} compressed diff",
            }
        )

    # Also compress just the newer firmware file for comparison
    print("Compressing newer firmware with different algorithms...")
    standalone_results = []

    for compression_name, compression_config in compression_configs:
        if compression_name == "none":
            # No compression - just the raw file
            compressed_size = len(new_firmware)
        else:
            # We'll create a diff from empty to the firmware (effectively compression)
            compressed_data = compress_data_with_config(new_firmware, compression_config)
            compressed_size = len(compressed_data)

        standalone_results.append(
            {
                "compression": compression_name,
                "size": compressed_size,
                "description": f"{compression_name.upper()} compressed firmware",
            }
        )

    # Print formatted results
    print("\n" + "=" * 80)
    print("MICROPYTHON FIRMWARE COMPRESSION COMPARISON (12-bit window)")
    print("=" * 80)
    print()
    print("Firmware Details:")
    print(f"  Old: RPI_PICO-20241129-v1.24.1.uf2 ({format_size(len(old_firmware))})")
    print(f"  New: RPI_PICO-20250415-v1.25.0.uf2 ({format_size(len(new_firmware))})")
    print()

    # Diff sizes table
    print("Diff Patch Sizes:")
    print("-" * 50)
    print(f"{'Algorithm':<10} {'Size':<12} {'vs Uncompressed':<15}")
    print("-" * 50)

    uncompressed_size = results[0]["diff_size"]  # First result is uncompressed

    for result in results:
        size_str = format_size(result["diff_size"])
        if result["compression"] == "none":
            ratio_str = "baseline"
        else:
            ratio = (result["diff_size"] / uncompressed_size) * 100
            ratio_str = f"{ratio:.1f}%"

        print(f"{result['compression']:<10} {size_str:<12} {ratio_str:<15}")

    print()

    # Standalone compression table
    print("Standalone Firmware Compression:")
    print("-" * 50)
    print(f"{'Algorithm':<10} {'Size':<12} {'vs Original':<15}")
    print("-" * 50)

    original_size = len(new_firmware)

    for result in standalone_results:
        size_str = format_size(result["size"])
        if result["compression"] == "none":
            ratio_str = "100.0%"
        else:
            ratio = (result["size"] / original_size) * 100
            ratio_str = f"{ratio:.1f}%"

        print(f"{result['compression']:<10} {size_str:<12} {ratio_str:<15}")

    print()
    print("Summary:")
    print("-" * 50)

    # Find best compression for diffs
    best_diff = min(results[1:], key=lambda x: x["diff_size"])  # Skip 'none'
    diff_savings = ((uncompressed_size - best_diff["diff_size"]) / uncompressed_size) * 100

    print(
        f"Best diff compression: {best_diff['compression'].upper()} "
        f"({format_size(best_diff['diff_size'])}, {diff_savings:.1f}% smaller)"
    )

    # Find best compression for standalone
    best_standalone = min(standalone_results[1:], key=lambda x: x["size"])  # Skip 'none'
    standalone_savings = ((original_size - best_standalone["size"]) / original_size) * 100

    print(
        f"Best standalone compression: {best_standalone['compression'].upper()} "
        f"({format_size(best_standalone['size'])}, {standalone_savings:.1f}% smaller)"
    )

    # Show diff vs standalone advantage
    best_diff_ratio = (best_diff["diff_size"] / best_standalone["size"]) * 100
    print(f"Diff advantage: {100 - best_diff_ratio:.1f}% smaller than compressed firmware")

    return 0


if __name__ == "__main__":
    sys.exit(main())
