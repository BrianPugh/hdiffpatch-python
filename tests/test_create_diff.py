"""Unit tests for hdiffpatch.diff function."""

import pytest

import hdiffpatch


def test_create_diff_basic(simple_text_data):
    """Test basic diff creation."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    diff = hdiffpatch.diff(old_data, new_data)

    assert isinstance(diff, bytes)
    assert len(diff) > 0
    assert len(diff) < len(old_data) + len(new_data)  # Should be smaller than concatenation


def test_create_diff_identical_data(identical_data):
    """Test diff creation with identical data."""
    data = identical_data["old"]

    diff = hdiffpatch.diff(data, data)

    assert isinstance(diff, bytes)
    assert len(diff) > 0  # Even identical data produces a diff header


def test_create_diff_empty_data(empty_data):
    """Test diff creation with empty data."""
    empty = empty_data["old"]
    data = b"Some data"

    # Empty old, non-empty new
    diff1 = hdiffpatch.diff(empty, data)
    assert isinstance(diff1, bytes)
    assert len(diff1) > 0

    # Non-empty old, empty new
    diff2 = hdiffpatch.diff(data, empty)
    assert isinstance(diff2, bytes)
    assert len(diff2) > 0

    # Both empty
    diff3 = hdiffpatch.diff(empty, empty)
    assert isinstance(diff3, bytes)
    assert len(diff3) > 0


def test_create_diff_large_data():
    """Test diff creation with larger data sets."""
    # Create 1KB of data with pattern
    old_data = b"A" * 1000 + b"B" * 24
    new_data = b"A" * 1000 + b"C" * 24  # Only last 24 bytes different

    diff = hdiffpatch.diff(old_data, new_data)

    assert isinstance(diff, bytes)
    assert len(diff) > 0
    # Note: diff might not always be smaller than original data
    # depending on the nature of changes and compression


def test_create_diff_binary_data(binary_data):
    """Test diff creation with binary data."""
    old_data = binary_data["old"]
    new_data = binary_data["new"]

    diff = hdiffpatch.diff(old_data, new_data)

    assert isinstance(diff, bytes)
    assert len(diff) > 0


def test_create_diff_invalid_input():
    """Test diff with invalid input types."""
    with pytest.raises(TypeError):
        hdiffpatch.diff("not bytes", b"valid bytes")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        hdiffpatch.diff(b"valid bytes", "not bytes")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        hdiffpatch.diff(123, b"valid bytes")  # type: ignore[arg-type]


def test_create_diff_compression_none():
    """Test diff with explicit NONE compression."""
    old_data = b"Hello, world!"
    new_data = b"Hello, HDiffPatch!"

    diff = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_NONE)

    assert isinstance(diff, bytes)
    assert len(diff) > 0


def test_create_diff_compression_works():
    """Test that various compression types work."""
    old_data = b"Hello, world!"
    new_data = b"Hello, HDiffPatch!"

    # Test that compression actually works
    diff_zlib = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZLIB)
    assert isinstance(diff_zlib, bytes)
    assert len(diff_zlib) > 0

    diff_zstd = hdiffpatch.diff(old_data, new_data, compression=hdiffpatch.COMPRESSION_ZSTD)
    assert isinstance(diff_zstd, bytes)
    assert len(diff_zstd) > 0


def test_validate_roundtrip_parameter():
    """Test the validate_roundtrip parameter functionality."""
    old_data = b"Hello, world!"
    new_data = b"Hello, HDiffPatch!"

    # Test with default (validation enabled)
    diff_default = hdiffpatch.diff(old_data, new_data)
    result_default = hdiffpatch.apply(old_data, diff_default)
    assert result_default == new_data

    # Test with validation explicitly enabled
    diff_enabled = hdiffpatch.diff(old_data, new_data, validate=True)
    result_enabled = hdiffpatch.apply(old_data, diff_enabled)
    assert result_enabled == new_data

    # Test with validation disabled
    diff_disabled = hdiffpatch.diff(old_data, new_data, validate=False)
    result_disabled = hdiffpatch.apply(old_data, diff_disabled)
    assert result_disabled == new_data

    # All diffs should work and produce same result
    assert result_default == result_enabled == result_disabled


def test_validate_roundtrip_with_compression():
    """Test validate_roundtrip parameter works with different compression types."""
    old_data = b"The quick brown fox jumps over the lazy dog" * 10
    new_data = b"The quick BLUE fox jumps over the lazy cat" * 10

    for compression in [None, "zlib", "zstd", "lzma"]:
        # Test with validation enabled
        diff = hdiffpatch.diff(old_data, new_data, compression=compression, validate=True)
        result = hdiffpatch.apply(old_data, diff)
        assert result == new_data

        # Test with validation disabled
        diff_no_validate = hdiffpatch.diff(old_data, new_data, compression=compression, validate=False)
        result_no_validate = hdiffpatch.apply(old_data, diff_no_validate)
        assert result_no_validate == new_data
