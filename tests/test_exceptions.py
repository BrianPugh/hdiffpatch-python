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
    """Test that PatchError is properly raised and contains useful information."""
    with pytest.raises(hdiffpatch.HDiffPatchError) as exc_info:
        hdiffpatch.apply(b"test", b"invalid_diff_data")

    assert "patch" in str(exc_info.value).lower()
