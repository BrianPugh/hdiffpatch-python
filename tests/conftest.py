"""Pytest configuration and fixtures for hdiffpatch tests."""

import pytest

import hdiffpatch


@pytest.fixture
def simple_text_data():
    """Simple text data for basic tests."""
    return {
        "old": b"The quick brown fox jumped over the lazy dog.",
        "new": b"The quick black box jumped over the lazy hog.",
    }


@pytest.fixture
def identical_data():
    """Identical data for same-data tests."""
    data = b"This is the same data in both old and new."
    return {"old": data, "new": data}


@pytest.fixture
def empty_data():
    """Empty data for edge case tests."""
    return {"old": b"", "new": b""}


@pytest.fixture
def large_repetitive_data():
    """Large repetitive data for compression tests."""
    return {
        "old": b"The quick brown fox jumped over the lazy dog. " * 100,
        "new": b"The quick black box jumped over the lazy hog. " * 100,
    }


@pytest.fixture
def binary_data():
    """Binary data for binary diff tests."""
    return {
        "old": bytes(range(256)),  # All byte values 0-255
        "new": bytes(range(1, 255)) + b"\x00\xff",  # Shifted by 1, wrapped
    }


@pytest.fixture
def highly_compressible_data():
    """Highly compressible data for compression effectiveness tests."""
    return {
        "old": b"A" * 1000 + b"B" * 1000 + b"C" * 1000,
        "new": b"A" * 1000 + b"X" * 1000 + b"C" * 1000,  # Only middle section changes
    }


@pytest.fixture
def compression_types():
    """List of all supported compression types."""
    return [
        hdiffpatch.COMPRESSION_ZLIB,
        hdiffpatch.COMPRESSION_ZSTD,
        hdiffpatch.COMPRESSION_LZMA,
        hdiffpatch.COMPRESSION_LZMA2,
        hdiffpatch.COMPRESSION_BZIP2,
        hdiffpatch.COMPRESSION_TAMP,
    ]


@pytest.fixture
def all_compression_types():
    """List of all compression types including NONE."""
    return [
        hdiffpatch.COMPRESSION_NONE,
        hdiffpatch.COMPRESSION_ZLIB,
        hdiffpatch.COMPRESSION_ZSTD,
        hdiffpatch.COMPRESSION_LZMA,
        hdiffpatch.COMPRESSION_LZMA2,
        hdiffpatch.COMPRESSION_BZIP2,
        hdiffpatch.COMPRESSION_TAMP,
    ]


@pytest.fixture
def unicode_data():
    """Unicode data encoded as UTF-8."""
    old_text = "Hello, 世界! 🌍"
    new_text = "Hello, 地球! 🌎"
    return {
        "old": old_text.encode("utf-8"),
        "new": new_text.encode("utf-8"),
    }


@pytest.fixture
def random_data():
    """Random data for stress testing (uses fixed seed for reproducibility)."""
    import random

    random.seed(42)  # noqa: S311
    return {
        "old": bytes([random.randint(0, 255) for _ in range(1000)]),  # noqa: S311
        "new": bytes([random.randint(0, 255) for _ in range(1000)]),  # noqa: S311
    }
