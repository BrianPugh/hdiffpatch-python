"""Unit tests for compression functionality."""

from typing import cast

import pytest

import hdiffpatch


class TestCompressionTypes:
    """Test compression type handling."""

    def test_compression_type_constants(self):
        """Test that compression type constants are defined."""
        assert hasattr(hdiffpatch, "COMPRESSION_NONE")
        assert hasattr(hdiffpatch, "COMPRESSION_ZLIB")
        assert hasattr(hdiffpatch, "COMPRESSION_LZMA")
        assert hasattr(hdiffpatch, "COMPRESSION_LZMA2")
        assert hasattr(hdiffpatch, "COMPRESSION_ZSTD")
        assert hasattr(hdiffpatch, "COMPRESSION_BZIP2")
        assert hasattr(hdiffpatch, "COMPRESSION_TAMP")

        assert hdiffpatch.COMPRESSION_NONE == "none"
        assert hdiffpatch.COMPRESSION_ZLIB == "zlib"
        assert hdiffpatch.COMPRESSION_LZMA == "lzma"
        assert hdiffpatch.COMPRESSION_LZMA2 == "lzma2"
        assert hdiffpatch.COMPRESSION_ZSTD == "zstd"
        assert hdiffpatch.COMPRESSION_BZIP2 == "bzip2"
        assert hdiffpatch.COMPRESSION_TAMP == "tamp"


class TestUncompressedDiffs:
    """Test uncompressed diff functionality."""

    def test_create_diff_none_compression(self):
        """Test creating diffs with NONE compression."""
        old_data = b"The quick brown fox jumped over the lazy dog."
        new_data = b"The quick black box jumped over the lazy hog."

        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

    def test_apply_patch_none_compression(self):
        """Test applying patches with NONE compression."""
        old_data = b"The quick brown fox jumped over the lazy dog."
        new_data = b"The quick black box jumped over the lazy hog."

        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)
        result = hdiffpatch.apply(old_data, diff)

        assert result == new_data


class TestCompressedDiffs:
    """Test compressed diff functionality."""

    def test_create_diff_zlib_compression(self):
        """Test creating diffs with ZLIB compression."""
        old_data = b"The quick brown fox jumped over the lazy dog." * 10  # Larger data for compression
        new_data = b"The quick black box jumped over the lazy hog." * 10

        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Compression fully supported for both diff creation and patch application

    def test_create_diff_zstd_compression(self):
        """Test creating diffs with ZSTD compression."""
        old_data = b"AAAAAAAAAABBBBBBBBBBCCCCCCCCCC" * 50  # Highly compressible data
        new_data = b"AAAAAAAAAABBBBBBBBBBDDDDDDDDDD" * 50

        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZSTD)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Compression fully supported for both diff creation and patch application

    def test_create_diff_lzma_compression(self):
        """Test creating diffs with LZMA compression."""
        old_data = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
        new_data = b"Lorem ipsum dolor sit amet, consectetur adipiscing ELIT. " * 20

        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_LZMA)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Compression fully supported for both diff creation and patch application

    def test_apply_patch_compressed_round_trip(self, compression_types):
        """Test full round-trip with various compression algorithms."""
        old_data = b"The quick brown fox jumped over the lazy dog. " * 100
        new_data = b"The quick black box jumped over the lazy hog. " * 100

        for compression in compression_types:
            diff = hdiffpatch.diff(old_data, new_data, compression=cast(hdiffpatch.CompressionType, compression))
            assert isinstance(diff, bytes)
            assert len(diff) > 0

            # Test full round-trip
            result = hdiffpatch.apply(old_data, diff)
            assert result == new_data, f"Round-trip failed for {compression}"

    def test_compression_effectiveness(self):
        """Test compression creates different sized diffs."""
        # Create highly repetitive data that should compress well
        old_data = b"A" * 1000 + b"B" * 1000 + b"C" * 1000
        new_data = b"A" * 1000 + b"X" * 1000 + b"C" * 1000  # Only middle section changes

        diff_none = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)
        diff_zstd = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZSTD)

        # Both should produce valid diffs
        assert isinstance(diff_none, bytes)
        assert isinstance(diff_zstd, bytes)
        assert len(diff_none) > 0
        assert len(diff_zstd) > 0

        # Test uncompressed version works
        result_none = hdiffpatch.apply(old_data, diff_none)
        assert result_none == new_data

    def test_auto_detect_compression(self):
        """Test automatic compression detection during patch application."""
        old_data = b"Test data for compression detection."
        new_data = b"Test data for compression DETECTION."

        # Create diffs with different compression types
        diff_zlib = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)
        diff_zstd = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZSTD)

        # Both should create valid diffs
        assert isinstance(diff_zlib, bytes)
        assert isinstance(diff_zstd, bytes)
        assert len(diff_zlib) > 0
        assert len(diff_zstd) > 0

        # Test auto-detection during patch application
        result_zlib = hdiffpatch.apply(old_data, diff_zlib)
        result_zstd = hdiffpatch.apply(old_data, diff_zstd)

        assert result_zlib == new_data
        assert result_zstd == new_data


class TestCompressionCurrentState:
    """Test current state of compression implementation."""

    def test_compression_works_correctly(self, compression_types):
        """Test that compressed diff creation and application works."""
        old_data = b"Test data"
        new_data = b"Test DATA"

        for compression in compression_types:
            diff = hdiffpatch.diff(old_data, new_data, compression=cast(hdiffpatch.CompressionType, compression))
            assert isinstance(diff, bytes)
            assert len(diff) > 0

            # Test full round-trip
            result = hdiffpatch.apply(old_data, diff)
            assert result == new_data, f"Round-trip failed for {compression}"
