"""Tests for LzhamConfig and LZHAM compression."""

import random

import pytest

import hdiffpatch
from hdiffpatch import LzhamConfig


def test_default_construction():
    """Defaults match the upstream LZHAM plugin (level "better", 16MB dictionary) with a single thread."""
    config = LzhamConfig()
    assert config.level == 3
    assert config.window == 24
    assert config.threads == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"level": -1},
        {"level": 6},
        {"window": 14},
        {"window": 30},
        {"threads": 0},
        {"threads": 65},
    ],
)
def test_invalid_values(kwargs):
    """Out-of-range parameters are rejected."""
    with pytest.raises(ValueError, match=f"'{next(iter(kwargs))}' must be"):
        LzhamConfig(**kwargs)


@pytest.mark.parametrize("field", ["level", "window", "threads"])
def test_invalid_type(field):
    """Non-int parameters are rejected."""
    with pytest.raises(TypeError, match=f"'{field}' must be <class 'int'>"):
        LzhamConfig(**{field: "6"})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "method_name,expected",
    [
        ("fast", LzhamConfig(level=0, window=18)),
        ("balanced", LzhamConfig(level=2, window=22, threads=2)),
        ("best_compression", LzhamConfig(level=5, window=26, threads=4)),
        ("minimal_memory", LzhamConfig(level=3, window=15)),
    ],
)
def test_classmethods(method_name, expected):
    """Preset classmethods return the documented configs."""
    assert getattr(LzhamConfig, method_name)() == expected


@pytest.mark.parametrize(
    "compression",
    [
        hdiffpatch.COMPRESSION_LZHAM,
        LzhamConfig.fast(),
        LzhamConfig.balanced(),
        LzhamConfig.best_compression(),
        LzhamConfig.minimal_memory(),
        *(LzhamConfig(level=level) for level in range(6)),
    ],
    ids=repr,
)
def test_round_trip(compression, large_repetitive_data):
    """Diff -> apply round-trips, and the header names the "lzham" codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    diff_data = hdiffpatch.diff(old_data, new_data, compression=compression)

    assert diff_data.startswith(b"HDIFF13&lzham\x00")
    assert hdiffpatch.apply(old_data, diff_data) == new_data


def test_multithreaded_compression():
    """Multithreaded LZHAM compression round-trips on inputs big enough to use its helper threads."""
    rng = random.Random(0)  # noqa: S311
    old_data = rng.randbytes(1 << 16)
    new_data = old_data + bytes(rng.choice(b"abcdefgh ") for _ in range(2 << 20))

    diff_data = hdiffpatch.diff(old_data, new_data, compression=LzhamConfig(level=4, window=20, threads=8))

    assert hdiffpatch.apply(old_data, diff_data) == new_data


def test_recompress_to_and_from_lzham(large_repetitive_data):
    """Recompress converts into and out of LZHAM."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]
    zstd_diff = hdiffpatch.diff(old_data, new_data, compression="zstd")

    lzham_diff = hdiffpatch.recompress(zstd_diff, "lzham")
    assert hdiffpatch.apply(old_data, lzham_diff) == new_data
    assert hdiffpatch.recompress(lzham_diff, "zstd") == zstd_diff
