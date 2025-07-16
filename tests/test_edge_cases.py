"""Unit tests for edge cases and special scenarios."""

import pytest

import hdiffpatch


def test_very_large_diff(random_data):
    """Test with data that would create a large diff."""
    old_data = random_data["old"]
    new_data = random_data["new"]

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data


def test_null_bytes():
    """Test handling of null bytes in data."""
    old_data = b"Hello\x00World\x00Test"
    new_data = b"Hello\x00Earth\x00Test"

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data


def test_unicode_encoded_data(unicode_data):
    """Test with UTF-8 encoded Unicode data."""
    old_data = unicode_data["old"]
    new_data = unicode_data["new"]

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data


@pytest.mark.parametrize(
    "old_data,new_data",
    [
        # Pattern changes (same size)
        (b"ABCDEFG" * 10, b"ABCXYZG" * 10),
        # Same-length substitutions
        (b"Hello World", b"Hallo World"),  # Single char change
        (b"The quick brown fox", b"The quick white fox"),  # Same length word substitution
    ],
)
def test_patterns_and_repetition(old_data, new_data):
    """Test with various patterns and repetitive data."""
    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)
    assert result == new_data, f"Failed for {old_data!r} -> {new_data!r}"


def test_all_control_characters():
    """Test with all ASCII control characters."""
    old_data = bytes(range(32))  # All control characters
    new_data = bytes(range(16, 48))  # Shifted control + printable

    diff = hdiffpatch.diff(old_data, new_data)
    result = hdiffpatch.apply(old_data, diff)

    assert result == new_data
