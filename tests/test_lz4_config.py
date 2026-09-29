"""Tests for Lz4Config / Lz4HCConfig and LZ4 compression."""

import pytest

import hdiffpatch
from hdiffpatch import Lz4Config, Lz4HCConfig


def test_default_construction():
    """Defaults match the upstream LZ4 plugins."""
    assert Lz4Config().level == 50
    assert Lz4HCConfig().level == 11


@pytest.mark.parametrize(
    "config_cls,level",
    [
        (Lz4Config, 0),
        (Lz4Config, 51),
        (Lz4HCConfig, 2),
        (Lz4HCConfig, 13),
    ],
)
def test_invalid_level(config_cls, level):
    """Out-of-range levels are rejected."""
    with pytest.raises(ValueError, match="'level' must be"):
        config_cls(level=level)


@pytest.mark.parametrize("config_cls", [Lz4Config, Lz4HCConfig])
def test_invalid_type(config_cls):
    """Non-int levels are rejected."""
    with pytest.raises(TypeError, match="'level' must be <class 'int'>"):
        config_cls(level="6")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "method_name,expected",
    [
        ("fast", Lz4Config(level=1)),
        ("balanced", Lz4Config(level=40)),
        ("best_compression", Lz4Config(level=50)),
        ("minimal_memory", Lz4Config(level=50)),
    ],
)
def test_lz4_classmethods(method_name, expected):
    """Lz4Config presets return the documented configs."""
    assert getattr(Lz4Config, method_name)() == expected


@pytest.mark.parametrize(
    "method_name,expected",
    [
        ("fast", Lz4HCConfig(level=3)),
        ("balanced", Lz4HCConfig(level=9)),
        ("best_compression", Lz4HCConfig(level=12)),
        ("minimal_memory", Lz4HCConfig(level=11)),
    ],
)
def test_lz4hc_classmethods(method_name, expected):
    """Lz4HCConfig presets return the documented configs."""
    assert getattr(Lz4HCConfig, method_name)() == expected


@pytest.mark.parametrize(
    "compression",
    [
        hdiffpatch.COMPRESSION_LZ4,
        hdiffpatch.COMPRESSION_LZ4HC,
        Lz4Config.fast(),
        Lz4Config.best_compression(),
        Lz4HCConfig.fast(),
        Lz4HCConfig.best_compression(),
    ],
    ids=repr,
)
def test_round_trip(compression, large_repetitive_data):
    """Diff -> apply round-trips; LZ4HC output carries the same "lz4" header name as LZ4."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    diff_data = hdiffpatch.diff(old_data, new_data, compression=compression)

    assert diff_data.startswith(b"HDIFF13&lz4\x00")
    assert hdiffpatch.apply(old_data, diff_data) == new_data


def test_lz4hc_compresses_better_than_fastest_lz4(highly_compressible_data):
    """LZ4HC at its best level is no larger than LZ4 at its fastest."""
    old_data = highly_compressible_data["old"]
    new_data = highly_compressible_data["new"]

    fastest = hdiffpatch.diff(old_data, new_data, compression=Lz4Config.fast())
    best = hdiffpatch.diff(old_data, new_data, compression=Lz4HCConfig.best_compression())

    assert len(best) <= len(fastest)


def test_recompress_lz4hc_to_zstd_and_back(large_repetitive_data):
    """Recompress converts out of and back into LZ4HC byte-identically."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]
    lz4hc_diff = hdiffpatch.diff(old_data, new_data, compression="lz4hc")

    zstd_diff = hdiffpatch.recompress(lz4hc_diff, "zstd")
    assert hdiffpatch.apply(old_data, zstd_diff) == new_data
    assert hdiffpatch.recompress(zstd_diff, "lz4hc") == lz4hc_diff
