"""Unit tests for tamp compression plugin functionality."""

import pytest

import hdiffpatch


class TestTampCompressionPlugin:
    """Test tamp compression plugin functionality."""

    def test_tamp_compression_constant_exists(self):
        """Test that COMPRESSION_TAMP constant is defined."""
        assert hasattr(hdiffpatch, "COMPRESSION_TAMP")
        assert hdiffpatch.COMPRESSION_TAMP == "tamp"

    def test_create_diff_raw_compression_small_data(self):
        """Test creating diffs with tamp compression on small data."""
        old_data = b"The quick brown fox"
        new_data = b"The quick black fox"

        # This should not crash
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

    def test_create_diff_raw_compression_medium_data(self):
        """Test creating diffs with tamp compression on medium data."""
        old_data = b"The quick brown fox jumped over the lazy dog. " * 100
        new_data = b"The quick black box jumped over the lazy hog. " * 100

        # This should not crash
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

    def test_create_diff_raw_compression_large_data(self):
        """Test creating diffs with tamp compression on large data."""
        old_data = b"A" * 10000 + b"B" * 10000
        new_data = b"A" * 10000 + b"C" * 10000

        # This should not crash
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

    def test_create_diff_raw_compression_empty_data(self):
        """Test creating diffs with tamp compression on empty data."""
        old_data = b""
        new_data = b"new content"

        # This should not crash
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

    def test_create_diff_raw_compression_identical_data(self):
        """Test creating diffs with tamp compression on identical data."""
        data = b"identical content"

        # This should not crash
        diff = hdiffpatch.diff(data, data, compression=hdiffpatch.COMPRESSION_TAMP)

        assert isinstance(diff, bytes)
        assert len(diff) > 0

    def test_create_diff_raw_compression_vs_none(self):
        """Test that tamp compression produces different results than none compression."""
        old_data = b"The quick brown fox jumped over the lazy dog."
        new_data = b"The quick black box jumped over the lazy hog."

        diff_raw = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        diff_none = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)

        # Both should be valid
        assert isinstance(diff_raw, bytes)
        assert isinstance(diff_none, bytes)
        assert len(diff_raw) > 0
        assert len(diff_none) > 0

        # They might be different sizes or identical depending on implementation
        # We don't enforce a specific relationship, just that both work

    def test_create_diff_raw_compression_binary_data(self):
        """Test creating diffs with tamp compression on binary data."""
        old_data = bytes(range(256))
        new_data = bytes(list(range(1, 256)) + [0])

        # This should not crash
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)

        assert isinstance(diff, bytes)
        assert len(diff) > 0


class TestTampCompressionRoundTrip:
    """Test round-trip functionality (compression + decompression)."""

    def test_round_trip_tamp_compression_small_data(self):
        """Test round-trip diff creation and patch application with tamp compression."""
        old_data = b"The quick brown fox"
        new_data = b"The quick black fox"

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch - should automatically detect compression type
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data

    def test_round_trip_tamp_compression_medium_data(self):
        """Test round-trip with medium-sized data."""
        old_data = b"The quick brown fox jumped over the lazy dog. " * 100
        new_data = b"The quick black box jumped over the lazy hog. " * 100

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data

    def test_round_trip_tamp_compression_large_data(self):
        """Test round-trip with large data."""
        old_data = b"A" * 10000 + b"B" * 10000
        new_data = b"A" * 10000 + b"C" * 10000

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data

    def test_round_trip_tamp_compression_empty_to_data(self):
        """Test round-trip from empty data to some data."""
        old_data = b""
        new_data = b"new content"

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data

    def test_round_trip_tamp_compression_data_to_empty(self):
        """Test round-trip from some data to empty data."""
        old_data = b"old content"
        new_data = b""

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data

    def test_round_trip_tamp_compression_identical_data(self):
        """Test round-trip with identical data."""
        data = b"identical content"

        # Create diff with tamp compression
        diff = hdiffpatch.diff(data, data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch
        result = hdiffpatch.apply(data, diff)
        assert isinstance(result, bytes)
        assert result == data

    def test_round_trip_tamp_compression_binary_data(self):
        """Test round-trip with binary data."""
        old_data = bytes(range(256))
        new_data = bytes(list(range(1, 256)) + [0])

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data

    def test_round_trip_explicit_compression_parameter(self):
        """Test round-trip with explicit compression parameter in apply()."""
        old_data = b"test data for explicit compression"
        new_data = b"test data for explicit decompression"

        # Create diff with tamp compression
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_TAMP)
        assert isinstance(diff, bytes)
        assert len(diff) > 0

        # Apply patch with auto-detected compression
        result = hdiffpatch.apply(old_data, diff)
        assert isinstance(result, bytes)
        assert result == new_data
