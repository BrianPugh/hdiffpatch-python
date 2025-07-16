"""Unit tests for recompress functionality with comprehensive round-trip validation."""

from typing import cast

import pytest

import hdiffpatch


class TestRecompressRoundTrip:
    """Test recompress function with mandatory round-trip validation."""

    def _validate_round_trip(self, old_data, new_data, compression_from, compression_to):
        """Helper to validate full round-trip: diff → recompress → apply → verify.

        Parameters
        ----------
        old_data : bytes
            Original data
        new_data : bytes
            Modified data
        compression_from : str
            Source compression type
        compression_to : str
            Target compression type

        Returns
        -------
        tuple
            (original_diff, recompressed_diff, final_result)
        """
        # Create diff with source compression
        original_diff = hdiffpatch.diff(old_data, new_data, compression=compression_from)
        assert isinstance(original_diff, bytes)
        assert len(original_diff) > 0

        # Verify original diff works
        original_result = hdiffpatch.apply(old_data, original_diff)
        assert original_result == new_data, f"Original diff failed for {compression_from}"

        # Recompress to target compression
        recompressed_diff = hdiffpatch.recompress(original_diff, compression=compression_to)
        assert isinstance(recompressed_diff, bytes)
        assert len(recompressed_diff) > 0

        # Apply recompressed diff and verify result
        final_result = hdiffpatch.apply(old_data, recompressed_diff)
        assert final_result == new_data, f"Round-trip failed: {compression_from} → {compression_to}"

        return original_diff, recompressed_diff, final_result

    @pytest.mark.parametrize(
        "compression_from",
        [
            hdiffpatch.COMPRESSION_NONE,
            hdiffpatch.COMPRESSION_ZLIB,
            hdiffpatch.COMPRESSION_ZSTD,
            hdiffpatch.COMPRESSION_LZMA,
            hdiffpatch.COMPRESSION_LZMA2,
            hdiffpatch.COMPRESSION_BZIP2,
            hdiffpatch.COMPRESSION_TAMP,
        ],
    )
    @pytest.mark.parametrize(
        "compression_to",
        [
            hdiffpatch.COMPRESSION_NONE,
            hdiffpatch.COMPRESSION_ZLIB,
            hdiffpatch.COMPRESSION_ZSTD,
            hdiffpatch.COMPRESSION_LZMA,
            hdiffpatch.COMPRESSION_LZMA2,
            hdiffpatch.COMPRESSION_BZIP2,
            hdiffpatch.COMPRESSION_TAMP,
        ],
    )
    def test_recompress_all_permutations(self, compression_from, compression_to, simple_text_data):
        """Test all compression type permutations with round-trip validation."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        self._validate_round_trip(old_data, new_data, compression_from, compression_to)

    def test_recompress_to_uncompressed(self, compression_types, simple_text_data):
        """Test recompressing all compressed types to uncompressed."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        for compression_from in compression_types:
            self._validate_round_trip(old_data, new_data, compression_from, hdiffpatch.COMPRESSION_NONE)

    def test_recompress_from_uncompressed(self, compression_types, simple_text_data):
        """Test recompressing uncompressed to all compressed types."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        for compression_to in compression_types:
            self._validate_round_trip(old_data, new_data, hdiffpatch.COMPRESSION_NONE, compression_to)

    def test_recompress_with_different_data_types(self, all_compression_types):
        """Test recompress with various data types."""
        test_cases = [
            # Binary data
            (bytes(range(256)), bytes(range(1, 255)) + b"\x00\xff"),
            # Highly compressible data
            (b"A" * 1000 + b"B" * 1000, b"A" * 1000 + b"X" * 1000),
            # Unicode data
            ("Hello, 世界! 🌍".encode(), "Hello, 地球! 🌎".encode()),
            # Empty to non-empty
            (b"", b"new data"),
            # Non-empty to empty
            (b"old data", b""),
        ]

        for old_data, new_data in test_cases:
            # Test a subset of permutations for each data type
            compression_pairs = [
                (hdiffpatch.COMPRESSION_NONE, hdiffpatch.COMPRESSION_ZLIB),
                (hdiffpatch.COMPRESSION_ZLIB, hdiffpatch.COMPRESSION_ZSTD),
                (hdiffpatch.COMPRESSION_ZSTD, hdiffpatch.COMPRESSION_NONE),
            ]

            for compression_from, compression_to in compression_pairs:
                self._validate_round_trip(old_data, new_data, compression_from, compression_to)


class TestRecompressAdvancedRoundTrip:
    """Advanced recompress scenarios with round-trip validation."""

    def test_recompress_chain(self, simple_text_data):
        """Test multi-step recompression chain."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        # Create chain: none → zlib → zstd → lzma → none
        diff1 = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)
        result1 = hdiffpatch.apply(old_data, diff1)
        assert result1 == new_data

        diff2 = hdiffpatch.recompress(diff1, compression=hdiffpatch.COMPRESSION_ZLIB)
        result2 = hdiffpatch.apply(old_data, diff2)
        assert result2 == new_data

        diff3 = hdiffpatch.recompress(diff2, compression=hdiffpatch.COMPRESSION_ZSTD)
        result3 = hdiffpatch.apply(old_data, diff3)
        assert result3 == new_data

        diff4 = hdiffpatch.recompress(diff3, compression=hdiffpatch.COMPRESSION_LZMA)
        result4 = hdiffpatch.apply(old_data, diff4)
        assert result4 == new_data

        diff5 = hdiffpatch.recompress(diff4, compression=hdiffpatch.COMPRESSION_NONE)
        result5 = hdiffpatch.apply(old_data, diff5)
        assert result5 == new_data

    def test_recompress_identical_format(self, all_compression_types, simple_text_data):
        """Test recompressing to the same format."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        for compression_type in all_compression_types:
            # Create diff
            original_diff = hdiffpatch.diff(old_data, new_data, compression=compression_type)

            # Recompress to same format
            recompressed_diff = hdiffpatch.recompress(original_diff, compression=compression_type)

            # Both should produce same result
            original_result = hdiffpatch.apply(old_data, original_diff)
            recompressed_result = hdiffpatch.apply(old_data, recompressed_diff)

            assert original_result == new_data
            assert recompressed_result == new_data
            assert original_result == recompressed_result

    def test_recompress_with_config_objects(self, simple_text_data):
        """Test recompress with configuration objects."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        # Create diff with default zlib
        original_diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)

        # Test recompressing to ZlibConfig
        zlib_config = hdiffpatch.ZlibConfig(level=9)
        recompressed_diff = hdiffpatch.recompress(original_diff, compression=zlib_config)
        result = hdiffpatch.apply(old_data, recompressed_diff)
        assert result == new_data

        # Test recompressing to ZStdConfig
        zstd_config = hdiffpatch.ZStdConfig(level=3)
        recompressed_diff2 = hdiffpatch.recompress(original_diff, compression=zstd_config)
        result2 = hdiffpatch.apply(old_data, recompressed_diff2)
        assert result2 == new_data


class TestRecompressFormatRoundTrip:
    """Test recompress with different diff formats."""

    def test_recompress_compressed_format(self, simple_text_data):
        """Test recompressing diffs in compressed format."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        # Create compressed diff (should be in compressed format)
        compressed_diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)

        # Recompress to different format
        recompressed = hdiffpatch.recompress(compressed_diff, compression=hdiffpatch.COMPRESSION_ZSTD)

        # Validate round-trip
        result = hdiffpatch.apply(old_data, recompressed)
        assert result == new_data

    def test_recompress_uncompressed_format(self, simple_text_data):
        """Test recompressing diffs in uncompressed format."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        # Create uncompressed diff (should be in compressed format with no compression)
        uncompressed_diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)

        # Recompress to compressed format
        recompressed = hdiffpatch.recompress(uncompressed_diff, compression=hdiffpatch.COMPRESSION_ZLIB)

        # Validate round-trip
        result = hdiffpatch.apply(old_data, recompressed)
        assert result == new_data


class TestRecompressEdgeCases:
    """Edge cases and error handling with round-trip validation where applicable."""

    def test_recompress_invalid_input_type(self):
        """Test recompress with invalid input types."""
        with pytest.raises(TypeError, match="Argument 'diff_data' has incorrect type"):
            hdiffpatch.recompress("not bytes")  # pyright: ignore[reportArgumentType]

        with pytest.raises(TypeError, match="Argument 'diff_data' has incorrect type"):
            hdiffpatch.recompress(123)  # pyright: ignore[reportArgumentType]

    def test_recompress_invalid_compression_type(self, simple_text_data):
        """Test recompress with invalid compression types."""
        old_data = simple_text_data["old"]
        new_data = simple_text_data["new"]

        # Create valid diff
        diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)

        # Test invalid compression type
        with pytest.raises(ValueError, match="Invalid compression type"):
            hdiffpatch.recompress(diff, compression="invalid")  # pyright: ignore[reportArgumentType]

    def test_recompress_corrupted_data(self):
        """Test recompress with corrupted diff data."""
        corrupted_data = b"this is not a valid diff"

        with pytest.raises(hdiffpatch.HDiffPatchError, match="Failed to detect diff format"):
            hdiffpatch.recompress(corrupted_data, compression=hdiffpatch.COMPRESSION_ZLIB)

    def test_recompress_empty_data(self):
        """Test recompress with empty data."""
        with pytest.raises(hdiffpatch.HDiffPatchError):
            hdiffpatch.recompress(b"", compression=hdiffpatch.COMPRESSION_ZLIB)

    def test_recompress_large_data(self, large_repetitive_data):
        """Test recompress with large data."""
        old_data = large_repetitive_data["old"]
        new_data = large_repetitive_data["new"]

        # Create large diff
        large_diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)

        # Recompress to different format
        recompressed = hdiffpatch.recompress(large_diff, compression=hdiffpatch.COMPRESSION_ZSTD)

        # Validate round-trip
        result = hdiffpatch.apply(old_data, recompressed)
        assert result == new_data


class TestRecompressEffectiveness:
    """Test recompress effectiveness and practical validation."""

    def test_recompress_size_comparison(self, highly_compressible_data):
        """Test compression effectiveness across different algorithms."""
        old_data = highly_compressible_data["old"]
        new_data = highly_compressible_data["new"]

        # Create baseline uncompressed diff
        uncompressed_diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)

        # Recompress to different algorithms
        zlib_diff = hdiffpatch.recompress(uncompressed_diff, compression=hdiffpatch.COMPRESSION_ZLIB)
        zstd_diff = hdiffpatch.recompress(uncompressed_diff, compression=hdiffpatch.COMPRESSION_ZSTD)

        # All should produce same result
        uncompressed_result = hdiffpatch.apply(old_data, uncompressed_diff)
        zlib_result = hdiffpatch.apply(old_data, zlib_diff)
        zstd_result = hdiffpatch.apply(old_data, zstd_diff)

        assert uncompressed_result == new_data
        assert zlib_result == new_data
        assert zstd_result == new_data
        assert uncompressed_result == zlib_result == zstd_result

        # Print sizes for debugging
        print(f"Uncompressed: {len(uncompressed_diff)} bytes")
        print(f"Zlib: {len(zlib_diff)} bytes")
        print(f"Zstd: {len(zstd_diff)} bytes")

    def test_recompress_functional_equivalence(self, all_compression_types, binary_data):
        """Test that all recompressed diffs produce functionally identical results."""
        old_data = binary_data["old"]
        new_data = binary_data["new"]

        # Create baseline diff
        baseline_diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)
        baseline_result = hdiffpatch.apply(old_data, baseline_diff)
        assert baseline_result == new_data

        # Recompress to all formats and verify identical results
        for compression_type in all_compression_types:
            recompressed_diff = hdiffpatch.recompress(baseline_diff, compression=compression_type)
            recompressed_result = hdiffpatch.apply(old_data, recompressed_diff)

            assert recompressed_result == new_data
            assert recompressed_result == baseline_result, f"Functional difference with {compression_type}"

    def test_recompress_performance_validation(self, random_data):
        """Test recompress performance with random data."""
        old_data = random_data["old"]
        new_data = random_data["new"]

        # Test performance-sensitive compression chain
        diff1 = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZSTD)
        diff2 = hdiffpatch.recompress(diff1, compression=hdiffpatch.COMPRESSION_LZMA)
        diff3 = hdiffpatch.recompress(diff2, compression=hdiffpatch.COMPRESSION_ZLIB)

        # All should produce same result
        result1 = hdiffpatch.apply(old_data, diff1)
        result2 = hdiffpatch.apply(old_data, diff2)
        result3 = hdiffpatch.apply(old_data, diff3)

        assert result1 == new_data
        assert result2 == new_data
        assert result3 == new_data
        assert result1 == result2 == result3
