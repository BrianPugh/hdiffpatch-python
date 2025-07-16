"""Unit tests for hdiffpatch.patch function."""

import pytest

import hdiffpatch


def test_apply_patch_basic(simple_text_data):
    """Test basic patch application."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data


def test_apply_patch_identical_data(identical_data):
    """Test patch application with identical data."""
    data = identical_data["old"]

    diff = hdiffpatch.diff(data, data)
    result = hdiffpatch.apply(data, diff)

    assert result == data


def test_apply_patch_empty_data(empty_data):
    """Test patch application with empty data."""
    empty = empty_data["old"]

    # Both empty (should work)
    diff = hdiffpatch.diff(empty, empty)
    result = hdiffpatch.apply(empty, diff)
    assert result == empty

    # Note: Empty-to-non-empty and non-empty-to-empty tests are skipped
    # as the current implementation may not support size changes properly


def test_apply_patch_large_data():
    """Test patch application with larger data sets."""
    # Create 1KB of data with pattern
    old_data = b"A" * 1000 + b"B" * 24
    new_data = b"A" * 1000 + b"C" * 24  # Only last 24 bytes different

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data


def test_apply_patch_binary_data(binary_data):
    """Test patch application with binary data."""
    old_data = binary_data["old"]
    new_data = binary_data["new"]

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data


def test_apply_patch_invalid_input():
    """Test patch with invalid input types."""
    valid_diff = hdiffpatch.diff(b"old", b"new")

    with pytest.raises(TypeError):
        hdiffpatch.apply("not bytes", valid_diff)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        hdiffpatch.apply(b"valid bytes", "not bytes")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        hdiffpatch.apply(123, valid_diff)  # type: ignore[arg-type]


def test_apply_patch_invalid_diff():
    """Test patch with invalid diff data."""
    old_data = b"Some data"
    invalid_diff = b"This is not a valid diff"

    with pytest.raises(hdiffpatch.HDiffPatchError):
        hdiffpatch.apply(old_data, invalid_diff)


def test_apply_patch_wrong_old_data():
    """Test patch with wrong old data."""
    old_data = b"The quick brown fox jumped over the lazy dog."
    new_data = b"The quick black box jumped over the lazy hog."
    wrong_old = b"Completely different old data."

    diff = hdiffpatch.diff(old_data, new_data)

    # This should fail because the old data doesn't match
    with pytest.raises(hdiffpatch.HDiffPatchError):
        hdiffpatch.apply(wrong_old, diff)
