"""Tests for TuzConfig and tinyuz compression."""

import random

import pytest

import hdiffpatch
from hdiffpatch import TuzConfig


def test_default_construction():
    """Defaults match the upstream tinyuz plugin (16MB dictionary, longest match length)."""
    config = TuzConfig()
    assert config.dict_size == 1 << 24
    assert config.max_save_length == 65535
    assert config.threads == 1
    assert config.literal_line is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dict_size": 0},
        {"dict_size": (1 << 30) + 1},
        {"max_save_length": 126},
        {"max_save_length": 65536},
        {"threads": 0},
        {"threads": 65},
    ],
)
def test_invalid_values(kwargs):
    """Out-of-range parameters are rejected."""
    with pytest.raises(ValueError, match=f"'{next(iter(kwargs))}' must be"):
        TuzConfig(**kwargs)


@pytest.mark.parametrize("field", ["dict_size", "max_save_length", "threads", "literal_line"])
def test_invalid_type(field):
    """Wrongly typed parameters are rejected."""
    with pytest.raises(TypeError, match=f"'{field}' must be"):
        TuzConfig(**{field: "6"})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "method_name,expected",
    [
        ("fast", TuzConfig(dict_size=1 << 16, max_save_length=1023)),
        ("balanced", TuzConfig(dict_size=1 << 20)),
        ("best_compression", TuzConfig(dict_size=1 << 24, literal_line=True)),
        ("minimal_memory", TuzConfig(dict_size=1 << 10)),
    ],
)
def test_classmethods(method_name, expected):
    """Preset classmethods return the documented configs."""
    assert getattr(TuzConfig, method_name)() == expected


@pytest.mark.parametrize(
    "compression",
    [
        hdiffpatch.COMPRESSION_TUZ,
        TuzConfig.fast(),
        TuzConfig.balanced(),
        TuzConfig.best_compression(),
        TuzConfig.minimal_memory(),
        TuzConfig(dict_size=255, max_save_length=127),  # dictionary sizes need not be powers of 2
        TuzConfig(threads=4),
    ],
    ids=repr,
)
def test_round_trip(compression, large_repetitive_data):
    """Diff -> apply round-trips, and the header names the upstream "tuz" codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    diff_data = hdiffpatch.diff(old_data, new_data, compression=compression)

    assert diff_data.startswith(b"HDIFF13&tuz\x00")
    assert hdiffpatch.apply(old_data, diff_data) == new_data


def test_literal_line_shrinks_incompressible_data():
    """Literal lines store runs of incompressible bytes more compactly."""
    rng = random.Random(0)  # noqa: S311
    old_data = rng.randbytes(20_000)
    new_data = old_data[:5_000] + b"abc" * 300 + old_data[6_000:] + rng.randbytes(20_000)

    plain = hdiffpatch.diff(old_data, new_data, compression=TuzConfig())
    literal = hdiffpatch.diff(old_data, new_data, compression=TuzConfig(literal_line=True))

    assert len(literal) < len(plain)
    assert hdiffpatch.apply(old_data, literal) == new_data


def test_multithreaded_recompress():
    """Multithreaded tinyuz writes its output from worker threads, including through recompress."""
    rng = random.Random(0)  # noqa: S311
    old_data = rng.randbytes(1 << 16)
    new_data = old_data + b"The quick brown fox jumped over the lazy dog. " * 50_000
    diff_data = hdiffpatch.diff(old_data, new_data)

    recompressed = hdiffpatch.recompress(diff_data, TuzConfig(dict_size=4096, threads=4))

    assert hdiffpatch.apply(old_data, recompressed) == new_data
