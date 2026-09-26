"""Tests for the ``big_cache_match`` option of diff / diff_lite."""

from pathlib import Path

import pytest

import hdiffpatch

BINARIES = Path(__file__).parent / "binaries"


@pytest.fixture(scope="module")
def firmware():
    old = (BINARIES / "RPI_PICO-20241129-v1.24.1.uf2").read_bytes()
    new = (BINARIES / "RPI_PICO-20250415-v1.25.0.uf2").read_bytes()
    return old, new


@pytest.mark.parametrize("compression", ["none", "lzma"])
def test_diff_big_cache_match_is_byte_identical(firmware, compression):
    old, new = firmware
    baseline = hdiffpatch.diff(old, new, compression)
    cached = hdiffpatch.diff(old, new, compression, big_cache_match=True)
    assert cached == baseline


@pytest.mark.parametrize("compression", ["none", "tamp"])
def test_diff_lite_big_cache_match_is_byte_identical(firmware, compression):
    old, new = firmware
    baseline = hdiffpatch.diff_lite(old, new, compression=compression)
    cached = hdiffpatch.diff_lite(old, new, compression=compression, big_cache_match=True)
    assert cached == baseline


@pytest.mark.parametrize(
    ("old", "new"),
    [(b"", b"abc"), (b"abc", b""), (b"abcd", b"abce"), (b"x" * 10000, b"x" * 9999 + b"y")],
)
def test_big_cache_match_small_inputs(old, new):
    """Inputs shorter than the cache's hash width must still round-trip."""
    assert hdiffpatch.apply(old, hdiffpatch.diff(old, new, big_cache_match=True)) == new
    assert hdiffpatch.apply_lite(old, hdiffpatch.diff_lite(old, new, big_cache_match=True)) == new
