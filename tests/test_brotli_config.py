"""Tests for BrotliConfig and brotli compression."""

import pytest

import hdiffpatch
from hdiffpatch import BrotliConfig


def test_default_construction():
    """Defaults match the upstream brotli plugin (quality 9, 16MB window)."""
    config = BrotliConfig()
    assert config.level == 9
    assert config.window == 24


@pytest.mark.parametrize(
    "kwargs",
    [
        {"level": -1},
        {"level": 12},
        {"window": 9},
        {"window": 31},
    ],
)
def test_invalid_values(kwargs):
    """Out-of-range parameters are rejected."""
    with pytest.raises(ValueError, match=f"'{next(iter(kwargs))}' must be"):
        BrotliConfig(**kwargs)


@pytest.mark.parametrize("field", ["level", "window"])
def test_invalid_type(field):
    """Non-int parameters are rejected."""
    with pytest.raises(TypeError, match=f"'{field}' must be <class 'int'>"):
        BrotliConfig(**{field: "6"})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "method_name,expected",
    [
        ("fast", BrotliConfig(level=1, window=18)),
        ("balanced", BrotliConfig(level=6, window=22)),
        ("best_compression", BrotliConfig(level=11, window=24)),
        ("minimal_memory", BrotliConfig(level=6, window=10)),
    ],
)
def test_classmethods(method_name, expected):
    """Preset classmethods return the documented configs."""
    assert getattr(BrotliConfig, method_name)() == expected


@pytest.mark.parametrize(
    "compression",
    [
        hdiffpatch.COMPRESSION_BROTLI,
        BrotliConfig.fast(),
        BrotliConfig.balanced(),
        BrotliConfig.best_compression(),
        BrotliConfig.minimal_memory(),
        BrotliConfig(level=0, window=30),  # large-window request, shrunk to the input
    ],
    ids=repr,
)
def test_round_trip(compression, large_repetitive_data):
    """Diff -> apply round-trips, and the header names the "brotli" codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    diff_data = hdiffpatch.diff(old_data, new_data, compression=compression)

    assert diff_data.startswith(b"HDIFF13&brotli\x00")
    assert hdiffpatch.apply(old_data, diff_data) == new_data


def test_level_affects_size(highly_compressible_data):
    """Higher quality does not produce a larger diff on compressible data."""
    old_data = highly_compressible_data["old"]
    new_data = highly_compressible_data["new"]

    fast = hdiffpatch.diff(old_data, new_data, compression=BrotliConfig(level=0))
    best = hdiffpatch.diff(old_data, new_data, compression=BrotliConfig(level=11))

    assert len(best) <= len(fast)


def test_recompress_to_and_from_brotli(large_repetitive_data):
    """Recompress converts into and out of brotli."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]
    zstd_diff = hdiffpatch.diff(old_data, new_data, compression="zstd")

    brotli_diff = hdiffpatch.recompress(zstd_diff, "brotli")
    assert hdiffpatch.apply(old_data, brotli_diff) == new_data
    assert hdiffpatch.recompress(brotli_diff, "zstd") == zstd_diff
