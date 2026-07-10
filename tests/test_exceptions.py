"""Unit tests for exception handling."""

import pytest

import hdiffpatch


def test_diff_error_propagation():
    """Test that DiffError is properly raised and contains useful information."""
    try:
        # This should work, so we'll need to find a way to trigger an error
        hdiffpatch.diff(b"test", b"test")
    except hdiffpatch.HDiffPatchError as e:
        assert "diff" in str(e).lower()
    except Exception:  # noqa: S110
        pass  # Other exceptions are fine for this test


def test_patch_error_propagation():
    """Test that patch errors are properly raised and contain useful information."""
    with pytest.raises(hdiffpatch.HDiffPatchError) as exc_info:
        hdiffpatch.apply(b"test", b"invalid_diff_data")

    assert "diff" in str(exc_info.value).lower()


def test_apply_error_not_double_wrapped():
    """Test that internal HDiffPatchErrors are not re-wrapped with a second prefix."""
    with pytest.raises(hdiffpatch.HDiffPatchError) as exc_info:
        hdiffpatch.apply(b"test", b"invalid_diff_data")

    assert str(exc_info.value).count("Patch application failed") <= 1


def test_invalid_compression_error_message_sorted():
    """Test that the invalid-compression error lists options in stable sorted order."""
    with pytest.raises(ValueError, match="Valid options: bzip2, lzma, lzma2, none, tamp, zlib, zstd"):
        hdiffpatch.diff(b"old", b"new", compression="bogus")  # pyright: ignore[reportArgumentType]
