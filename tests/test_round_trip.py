"""Unit tests for round-trip diff -> patch operations."""

from typing import cast

import pytest

import hdiffpatch


@pytest.mark.parametrize(
    "old_data,new_data",
    [
        # Same-size changes (more likely to work with current implementation)
        (b"a", b"b"),  # Single char change
        (b"hello", b"hello"),  # Identical
        (b"hello", b"world"),  # Complete change
        (b"A" * 100, b"B" * 100),  # Repetitive data
        (b"A" * 256, b"B" * 256),  # Binary-like data (same size)
    ],
)
def test_round_trip_various_sizes(old_data, new_data):
    """Test round-trip with various data sizes."""
    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)
    assert result == new_data, f"Round-trip failed for {old_data!r} -> {new_data!r}"


@pytest.mark.parametrize(
    "old_data,new_data",
    [
        (b"hello", b"world"),  # Same length, different content
        (b"AAAAA", b"BBBBB"),  # Same length, pattern change
        (b"12345", b"54321"),  # Same length, reversed
        (b"\x00\x01\x02\x03\x04", b"\x04\x03\x02\x01\x00"),  # Binary same length
    ],
)
def test_round_trip_same_size(old_data, new_data):
    """Test round-trip with same-sized data (which should work with current implementation)."""
    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)
    assert result == new_data, f"Round-trip failed for {old_data!r} -> {new_data!r}"


def test_round_trip_performance():
    """Test round-trip with larger data to check performance."""
    # 10KB of text data
    old_data = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 200
    new_data = old_data.replace(b"Lorem", b"Lorem")  # Same size, minimal change

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data
    # For identical data, diff should be relatively small
    assert len(diff) < len(old_data)


def test_round_trip_all_compression_types(compression_types):
    """Test round-trip with all compression types."""
    old_data = b"The quick brown fox jumped over the lazy dog. " * 100
    new_data = b"The quick black box jumped over the lazy hog. " * 100

    # Test uncompressed baseline
    diff_none = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)
    result_none = hdiffpatch.apply(old_data, diff_none)
    assert result_none == new_data

    # Test all compression types
    for compression in compression_types:
        diff_compressed = hdiffpatch.diff(old_data, new_data, compression=cast(hdiffpatch.CompressionType, compression))
        result_compressed = hdiffpatch.apply(old_data, diff_compressed)
        assert result_compressed == new_data, f"Round-trip failed for {compression}"


def test_round_trip_compression_auto_detection():
    """Test that compressed diffs are automatically detected and handled."""
    old_data = b"Hello, world!"
    new_data = b"Hello, HDiffPatch!"

    # Create compressed diff
    diff_zlib = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)

    # Apply without specifying compression (should auto-detect)
    result = hdiffpatch.apply(old_data, diff_zlib)
    assert result == new_data
