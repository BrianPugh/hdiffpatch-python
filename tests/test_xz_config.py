"""Tests for XzConfig and xz compression."""

import pytest

import hdiffpatch
from hdiffpatch import XzConfig


def test_default_construction():
    """Defaults match the upstream xz plugin (level 7, 8MB window) with a single thread."""
    config = XzConfig()
    assert config.level == 7
    assert config.window == 23
    assert config.threads == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"level": -1},
        {"level": 10},
        {"window": 11},
        {"window": 31},
        {"threads": 0},
        {"threads": 65},
    ],
)
def test_invalid_values(kwargs):
    """Out-of-range parameters are rejected."""
    with pytest.raises(ValueError, match=f"'{next(iter(kwargs))}' must be"):
        XzConfig(**kwargs)


@pytest.mark.parametrize("field", ["level", "window", "threads"])
def test_invalid_type(field):
    """Non-int parameters are rejected."""
    with pytest.raises(TypeError, match=f"'{field}' must be <class 'int'>"):
        XzConfig(**{field: "6"})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "method_name,expected",
    [
        ("fast", XzConfig(level=1, window=12, threads=1)),
        ("balanced", XzConfig(level=6, window=23, threads=4)),
        ("best_compression", XzConfig(level=9, window=25, threads=8)),
        ("minimal_memory", XzConfig(level=6, window=12, threads=1)),
    ],
)
def test_classmethods(method_name, expected):
    """Preset classmethods return the documented configs."""
    assert getattr(XzConfig, method_name)() == expected


@pytest.mark.parametrize(
    "compression",
    [
        hdiffpatch.COMPRESSION_XZ,
        XzConfig(),
        XzConfig.fast(),
        XzConfig.balanced(),
        XzConfig.best_compression(),
        XzConfig.minimal_memory(),
    ],
    ids=repr,
)
def test_round_trip(compression, large_repetitive_data):
    """Diff -> apply round-trips, and the header names the upstream "7zXZ" codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    diff_data = hdiffpatch.diff(old_data, new_data, compression=compression)

    assert diff_data.startswith(b"HDIFF13&7zXZ\x00")
    assert hdiffpatch.apply(old_data, diff_data) == new_data


def test_recompress_to_and_from_xz(large_repetitive_data):
    """Recompress converts into and out of xz."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]
    zstd_diff = hdiffpatch.diff(old_data, new_data, compression="zstd")

    xz_diff = hdiffpatch.recompress(zstd_diff, "xz")
    assert hdiffpatch.apply(old_data, xz_diff) == new_data

    back = hdiffpatch.recompress(xz_diff, "zstd")
    assert back == zstd_diff


def test_level_affects_size(highly_compressible_data):
    """Higher levels do not produce a larger diff on compressible data."""
    old_data = highly_compressible_data["old"]
    new_data = highly_compressible_data["new"]

    fast = hdiffpatch.diff(old_data, new_data, compression=XzConfig(level=0))
    best = hdiffpatch.diff(old_data, new_data, compression=XzConfig(level=9))

    assert len(best) <= len(fast)
