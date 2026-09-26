"""Unit tests for hdiffpatch.recompress_lite (lite format)."""

from pathlib import Path

import pytest

import hdiffpatch
from hdiffpatch import (
    HDiffPatchError,
    LzmaConfig,
    TampConfig,
    ZlibConfig,
    apply_lite,
    diff_lite,
    recompress_lite,
)

BINARIES = Path(__file__).parent / "binaries"

LITE_TARGETS = [
    hdiffpatch.COMPRESSION_NONE,
    hdiffpatch.COMPRESSION_ZLIB,
    hdiffpatch.COMPRESSION_LZMA,
    hdiffpatch.COMPRESSION_TAMP,
    ZlibConfig(window=9),
    ZlibConfig.fast(),
    LzmaConfig(window=12),
    LzmaConfig(level=1, window=16),
    TampConfig(window=8),
    TampConfig(window=12, lazy_matching=False),
]

LITE_SOURCES = [
    hdiffpatch.COMPRESSION_NONE,
    hdiffpatch.COMPRESSION_ZLIB,
    hdiffpatch.COMPRESSION_LZMA,
    hdiffpatch.COMPRESSION_TAMP,
]


@pytest.fixture(scope="module")
def firmware_pair():
    """A real firmware update pair (two MicroPython UF2 images)."""
    return {
        "old": (BINARIES / "RPI_PICO-20241129-v1.24.1.uf2").read_bytes(),
        "new": (BINARIES / "RPI_PICO-20250415-v1.25.0.uf2").read_bytes(),
    }


@pytest.mark.parametrize("target", LITE_TARGETS, ids=repr)
@pytest.mark.parametrize("source", LITE_SOURCES)
def test_recompress_lite_matches_diff_lite(source, target, large_repetitive_data):
    """Recompressing from any lite codec is byte-identical to diffing with the target codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    expected = diff_lite(old_data, new_data, compression=target)
    result = recompress_lite(diff_lite(old_data, new_data, compression=source), target)

    assert result == expected
    assert apply_lite(old_data, result) == new_data


@pytest.mark.parametrize("target", LITE_TARGETS, ids=repr)
def test_recompress_lite_firmware(target, firmware_pair):
    """Byte identity holds on a real firmware pair, and the result applies."""
    old_data = firmware_pair["old"]
    new_data = firmware_pair["new"]
    raw = diff_lite(old_data, new_data)

    result = recompress_lite(raw, target)

    assert result == diff_lite(old_data, new_data, compression=target)
    assert apply_lite(old_data, result) == new_data
    assert recompress_lite(result, None) == raw


@pytest.mark.parametrize("target", LITE_TARGETS, ids=repr)
def test_recompress_lite_incompressible(target, random_data):
    """When compression cannot shrink the body, the output falls back to uncompressed like diff_lite."""
    old_data = random_data["old"]
    new_data = random_data["new"]

    result = recompress_lite(diff_lite(old_data, new_data), target)

    assert result == diff_lite(old_data, new_data, compression=target)
    assert apply_lite(old_data, result) == new_data


@pytest.mark.parametrize("strip", [None, "none", "NONE"])
def test_recompress_lite_strip(strip, large_repetitive_data):
    """None and "none" both strip compression back to the uncompressed diff."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]
    compressed = diff_lite(old_data, new_data, compression="lzma")

    assert recompress_lite(compressed, strip) == diff_lite(old_data, new_data)


def _to_inplace(lite: bytes, extra_safe_size: int) -> bytes:
    """Rewrite an uncompressed version-1 lite header as the inplace (version-2) variant."""
    assert lite[2] == 0x00
    flags = lite[3]
    size_bytes = flags & 7
    extra = extra_safe_size.to_bytes((extra_safe_size.bit_length() + 7) // 8, "little")
    header = bytes([0x68, 0x49, 0x00, (2 << 6) | flags & 0x3F, len(extra)])
    return header + lite[4 : 4 + size_bytes] + extra + lite[4 + size_bytes :]


@pytest.mark.parametrize("target", LITE_SOURCES)
def test_recompress_lite_preserves_inplace_header(target, large_repetitive_data):
    """The inplace variant keeps its version code and extraSafeSize through recompression."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]
    raw = diff_lite(old_data, new_data)
    inplace = _to_inplace(raw, 0x1234)

    result = recompress_lite(inplace, target)

    assert result[3] >> 6 == 2
    assert result[4] == 2
    assert result[2] == diff_lite(old_data, new_data, compression=target)[2]
    assert recompress_lite(result, None) == inplace


@pytest.mark.parametrize(
    "compression",
    [
        hdiffpatch.COMPRESSION_ZSTD,
        hdiffpatch.COMPRESSION_LZMA2,
        hdiffpatch.COMPRESSION_BZIP2,
        hdiffpatch.ZStdConfig(),
        hdiffpatch.Lzma2Config(),
        hdiffpatch.BZip2Config(),
    ],
    ids=repr,
)
def test_recompress_lite_rejects_unsupported_codec(compression, simple_text_data):
    """Codecs HPatchLite cannot decode are rejected, as in diff_lite."""
    lite = diff_lite(simple_text_data["old"], simple_text_data["new"])
    with pytest.raises(HDiffPatchError, match="not supported by HPatchLite"):
        recompress_lite(lite, compression)


def test_recompress_lite_invalid_compression_type(simple_text_data):
    """An unknown codec name raises ValueError."""
    lite = diff_lite(simple_text_data["old"], simple_text_data["new"])
    with pytest.raises(ValueError, match="Invalid compression type"):
        recompress_lite(lite, "bogus")  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("bad", ["not bytes", bytearray(b"hI\x00\x40"), None, 123])
def test_recompress_lite_type_errors(bad):
    """Non-bytes input raises TypeError."""
    with pytest.raises(TypeError):
        recompress_lite(bad, "lzma")  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    "garbage",
    [
        b"",
        b"hI",
        b"not a lite diff at all",
        bytes([0x68, 0x49, 0x00, 0xC0]),  # unknown version code 3
        bytes([0x68, 0x49, 0x03, 0x41]),  # declares a newSize byte but is truncated
        bytes([0x68, 0x49, 0x77, 0x40, 0x00]),  # compress type with no decompressor
    ],
)
def test_recompress_lite_rejects_garbage_header(garbage):
    """Malformed headers raise HDiffPatchError."""
    with pytest.raises(HDiffPatchError):
        recompress_lite(garbage, "zlib")


@pytest.mark.parametrize("source", ["zlib", "lzma", "tamp"])
def test_recompress_lite_rejects_corrupt_body(source, large_repetitive_data):
    """A truncated compressed body raises HDiffPatchError."""
    lite = diff_lite(large_repetitive_data["old"], large_repetitive_data["new"], compression=source)
    with pytest.raises(HDiffPatchError):
        recompress_lite(lite[: len(lite) // 2], None)


@pytest.mark.parametrize("cut", [1, 7, 100])
def test_recompress_lite_rejects_truncated_uncompressed_body(cut, large_repetitive_data):
    """An uncompressed body stores no length, so truncation is caught by walking its covers."""
    lite = diff_lite(large_repetitive_data["old"], large_repetitive_data["new"])
    with pytest.raises(HDiffPatchError, match="Corrupt lite diff body"):
        recompress_lite(lite[:-cut], "lzma")


def test_recompress_lite_rejects_padded_uncompressed_body(large_repetitive_data):
    """Trailing bytes after the last cover are corruption too, as for the device applier."""
    lite = diff_lite(large_repetitive_data["old"], large_repetitive_data["new"])
    with pytest.raises(HDiffPatchError, match="Corrupt lite diff body"):
        recompress_lite(lite + b"\x00", "lzma")


def test_recompress_lite_huge_claimed_size():
    """A header claiming a ~4 GiB body is rejected without allocating the claimed size."""
    header = bytes([0x68, 0x49, 0x03, 0x40 | (4 << 3) | 1, 0x10]) + (0xFFFFFFF0).to_bytes(4, "little")
    with pytest.raises(HDiffPatchError):
        recompress_lite(header + b"\x5d\x00\x00\x01\x00" + b"\x00" * 64, None)


def test_recompress_lite_in_public_api():
    """recompress_lite is exported from the package."""
    assert "recompress_lite" in hdiffpatch.__all__
    assert hdiffpatch.recompress_lite is recompress_lite
