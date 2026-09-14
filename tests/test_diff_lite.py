"""Unit tests for hdiffpatch.diff_lite / hdiffpatch.apply_lite (lite format)."""

import subprocess
import sys
import textwrap

import pytest

import hdiffpatch
from hdiffpatch import apply_lite, diff_lite

# Codecs HPatchLite can decode. "tamp" round-trips through the vendored tamp
# decompressor plugin. The on-device compress-type tag written into the lite
# header is asserted directly in test_diff_lite_header_compression_tag; apply_lite
# auto-detects the codec from that byte (there is no compression argument).
LITE_SUPPORTED = [
    hdiffpatch.COMPRESSION_NONE,
    hdiffpatch.COMPRESSION_ZLIB,
    hdiffpatch.COMPRESSION_LZMA,
    hdiffpatch.COMPRESSION_TAMP,
]

# Expected compress-type byte in the lite header (byte index 2, after the
# b"hI" magic) for each supported codec. Native codecs use their upstream
# hpi_compressType enum values; tamp uses the vendor-specific 0xF0 tag that the
# device-side tamp decompressor plugin keys off.
LITE_HEADER_TAG = {
    hdiffpatch.COMPRESSION_NONE: 0x00,
    hdiffpatch.COMPRESSION_ZLIB: 0x02,
    hdiffpatch.COMPRESSION_LZMA: 0x03,
    hdiffpatch.COMPRESSION_TAMP: 0xF0,
}

# Valid HDiffPatch codecs that HPatchLite cannot decode and must be rejected.
LITE_UNSUPPORTED = [
    hdiffpatch.COMPRESSION_ZSTD,
    hdiffpatch.COMPRESSION_LZMA2,
    hdiffpatch.COMPRESSION_BZIP2,
]


def test_diff_lite_basic(simple_text_data):
    """A lite diff is non-empty bytes that apply_lite reconstructs the target from."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    lite = diff_lite(old_data, new_data)

    assert isinstance(lite, bytes)
    assert len(lite) > 0
    assert apply_lite(old_data, lite) == new_data


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_diff_lite_round_trip(compression, large_repetitive_data):
    """diff_lite -> apply_lite round-trips for each supported codec (auto-detected)."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    lite = diff_lite(old_data, new_data, compression=compression)

    assert isinstance(lite, bytes)
    assert len(lite) > 0
    # apply_lite takes no compression argument: it reads the codec from the header.
    assert apply_lite(old_data, lite) == new_data, f"Lite round-trip failed for {compression}"


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_diff_lite_round_trip_binary(compression, binary_data):
    """Round-trip on binary data for each supported codec."""
    old_data = binary_data["old"]
    new_data = binary_data["new"]

    lite = diff_lite(old_data, new_data, compression=compression)

    assert apply_lite(old_data, lite) == new_data


@pytest.mark.parametrize(
    "config",
    [
        hdiffpatch.ZlibConfig(),
        hdiffpatch.LzmaConfig(),
        hdiffpatch.TampConfig(window=10),
    ],
)
def test_diff_lite_config_objects(config, highly_compressible_data):
    """Supported ``*Config`` objects produce lite diffs apply_lite can reconstruct."""
    old_data = highly_compressible_data["old"]
    new_data = highly_compressible_data["new"]

    lite = diff_lite(old_data, new_data, compression=config)

    assert apply_lite(old_data, lite) == new_data


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_diff_lite_header_compression_tag(compression, large_repetitive_data):
    """The lite header's compress-type byte matches the device dispatch tag.

    hpatch_lite_open reads this byte (offset 2, after the b"hI" magic) and it is
    what apply_lite (and the on-device applier) uses to pick the decompressor.
    Assert the raw byte directly to cover the dispatch contract, including the
    vendor-specific tamp value.
    """
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    lite = diff_lite(old_data, new_data, compression=compression)

    assert lite[:2] == b"hI"
    assert lite[2] == LITE_HEADER_TAG[compression]


def test_diff_lite_validate_default_catches_round_trip(simple_text_data):
    """validate=True (the default) verifies reconstruction via HPatchLite."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    # Should not raise; validation runs the real applier internally.
    lite_validated = diff_lite(old_data, new_data, validate=True)
    lite_unvalidated = diff_lite(old_data, new_data, validate=False)

    # Both paths emit the same bytes; validation only adds a check.
    assert lite_validated == lite_unvalidated
    assert apply_lite(old_data, lite_unvalidated) == new_data


@pytest.mark.parametrize("compression", LITE_UNSUPPORTED)
def test_diff_lite_rejects_unsupported_codec(compression, simple_text_data):
    """Codecs HPatchLite cannot decode are rejected with a clear error."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    with pytest.raises(hdiffpatch.HDiffPatchError, match="not supported by HPatchLite"):
        diff_lite(old_data, new_data, compression=compression)


@pytest.mark.parametrize(
    "config",
    [
        hdiffpatch.ZStdConfig(),
        hdiffpatch.Lzma2Config(),
        hdiffpatch.BZip2Config(),
    ],
)
def test_diff_lite_rejects_unsupported_config(config, simple_text_data):
    """Unsupported ``*Config`` objects are rejected with a clear error."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    with pytest.raises(hdiffpatch.HDiffPatchError, match="not supported by HPatchLite"):
        diff_lite(old_data, new_data, compression=config)


def test_diff_lite_invalid_compression_type(simple_text_data):
    """A totally invalid compression name raises ValueError."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    with pytest.raises(ValueError, match="Invalid compression type"):
        diff_lite(old_data, new_data, compression="not_a_codec")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_old,bad_new", [("str", b"bytes"), (b"bytes", "str"), (123, 456)])
def test_diff_lite_type_errors(bad_old, bad_new):
    """Non-bytes inputs raise TypeError."""
    with pytest.raises(TypeError):
        diff_lite(bad_old, bad_new)


def test_apply_lite_detects_wrong_old(simple_text_data, binary_data):
    """Applying a lite diff against the wrong old data does not yield the target.

    The patch reconstructs some bytes from whatever old data it is given, but the
    result must not equal new_data unless the correct old_data was used.
    """
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    lite = diff_lite(old_data, new_data)

    # Correct old data reconstructs the target exactly.
    assert apply_lite(old_data, lite) == new_data

    # A wrong (same-length) old image must not reconstruct new_data. Either the
    # applier rejects the mismatched source or it produces different bytes.
    wrong_old = bytes(b ^ 0xFF for b in old_data)
    assert wrong_old != old_data
    try:
        result = apply_lite(wrong_old, lite)
    except hdiffpatch.HDiffPatchError:
        pass
    else:
        assert result != new_data


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_apply_lite_auto_detects_codec(compression, large_repetitive_data):
    """apply_lite reconstructs without being told the codec, for every codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    lite = diff_lite(old_data, new_data, compression=compression)

    # No compression argument is passed; the header is self-describing.
    assert apply_lite(old_data, lite) == new_data


def test_apply_lite_rejects_invalid_diff(simple_text_data):
    """A corrupt / non-lite diff buffer raises HDiffPatchError, not a crash."""
    old_data = simple_text_data["old"]

    with pytest.raises(hdiffpatch.HDiffPatchError):
        apply_lite(old_data, b"not a valid lite diff header")


@pytest.mark.parametrize("bad_old,bad_diff", [("str", b"bytes"), (b"bytes", "str"), (123, 456)])
def test_apply_lite_type_errors(bad_old, bad_diff):
    """Non-bytes inputs raise TypeError."""
    with pytest.raises(TypeError):
        apply_lite(bad_old, bad_diff)


def test_diff_lite_not_standard_apply_compatible(simple_text_data):
    """Lite output is not consumable by the standard apply()."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    lite = diff_lite(old_data, new_data)

    with pytest.raises(hdiffpatch.HDiffPatchError):
        hdiffpatch.apply(old_data, lite)


def test_diff_lite_in_public_api():
    """diff_lite is exported from the package namespace."""
    assert "diff_lite" in hdiffpatch.__all__
    assert hdiffpatch.diff_lite is not None


def test_apply_lite_in_public_api():
    """apply_lite is exported from the package namespace."""
    assert "apply_lite" in hdiffpatch.__all__
    assert hdiffpatch.apply_lite is not None


# --- memory-exhaustion regression (apply_lite_shim._write_new output cap) ---

# Size of the old image the bomb replays, and how many times it replays it. A
# valid lite header declares newSize == 0, but the patch stream instructs the
# applier to copy OLD_SIZE bytes out of old_data BOMB_COVERS times. Without the
# per-write cap the reconstruction buffer grows to OLD_SIZE * BOMB_COVERS before
# hpatch_lite_patch's final newSize check fires; with the cap the first
# over-large write is rejected immediately.
_BOMB_OLD_SIZE = 1 << 20  # 1 MiB
_BOMB_COVERS = 512  # -> ~512 MiB of output if the cap is missing


def _lite_varint(v: int) -> bytes:
    """Encode ``v`` as HPatchLite's MSB-first base-128 varint (high bit = continue)."""
    parts = []
    while True:
        parts.append(v & 0x7F)
        v >>= 7
        if v == 0:
            break
    parts.reverse()
    return bytes(p | 0x80 for p in parts[:-1]) + bytes([parts[-1]])


def _build_output_size_bomb() -> bytes:
    """Craft a malformed lite diff that replays old_data far past its declared newSize.

    The header declares compress-type ``none`` and newSize/uncompressSize of 0
    bytes each (both values 0). Each cover copies ``_BOMB_OLD_SIZE`` bytes from
    old_data starting at oldPos 0 (isNotNeedSubDiff set, so no sub-diff bytes are
    consumed and the diff stays tiny), with a zero newPos delta so no diff-copy
    bytes are needed either.
    """
    # Header: b"hI" + compressType(none) + flags(versionCode<<6 | uSizeBytes<<3 | newSizeBytes)
    header = bytes([0x68, 0x49, 0x00, 0x40])  # version 1, 0 newSize bytes, 0 uncompressSize bytes

    stream = bytearray()
    stream += _lite_varint(_BOMB_COVERS)  # coverCount
    for i in range(_BOMB_COVERS):
        stream += _lite_varint(_BOMB_OLD_SIZE)  # cover_length
        if i == 0:
            # add-mode, oldPos delta 0 (fits in tag low bits): oldPos = 0
            stream += bytes([0x80])  # isNotNeedSubDiff
        else:
            # subtract-mode with continuation: oldPos = oldPosBack - OLD_SIZE = 0
            stream += bytes([0xE0])  # isNotNeedSubDiff | subtract | continue
            stream += _lite_varint(_BOMB_OLD_SIZE)
        stream += bytes([0x00])  # newPos delta 0

    return header + bytes(stream)


@pytest.mark.skipif(sys.platform == "win32", reason="peak-RSS measurement uses the resource module")
def test_apply_lite_output_size_bomb_does_not_over_allocate():
    """A malformed lite diff must not allocate output far beyond the declared newSize.

    Runs apply_lite in a subprocess on a patch-bomb (tiny diff, ~512 MiB of
    replayed output) and asserts the process's peak RSS growth stays small. Both
    the fixed and unfixed shim ultimately raise HDiffPatchError, so this measures
    the allocation the write-cap prevents rather than the return value.
    """
    bomb = _build_output_size_bomb()

    child = textwrap.dedent(
        f"""
        import resource
        import sys

        import hdiffpatch

        OLD_SIZE = {_BOMB_OLD_SIZE}
        old_data = bytes(OLD_SIZE)
        bomb = sys.stdin.buffer.read()

        # Warm up imports/allocator so the baseline high-water mark is settled.
        warm = hdiffpatch.diff_lite(b"hello", b"hello!")
        assert hdiffpatch.apply_lite(b"hello", warm) == b"hello!"

        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        try:
            hdiffpatch.apply_lite(old_data, bomb)
            outcome = "no_error"
        except hdiffpatch.HDiffPatchError:
            outcome = "rejected"
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        # ru_maxrss is bytes on macOS, KiB on Linux.
        scale = 1 if sys.platform == "darwin" else 1024
        grew_mib = (after - before) * scale / (1024 * 1024)
        print(f"{{outcome}} {{grew_mib:.1f}}")
        """
    )

    proc = subprocess.run(  # noqa: S603  # trusted: sys.executable + a fixed inline script
        [sys.executable, "-c", child],
        input=bomb,
        capture_output=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"child failed: {proc.stderr.decode(errors='replace')}"
    outcome, grew_raw = proc.stdout.decode().split()
    grew_mib = float(grew_raw)

    assert outcome == "rejected", "malformed bomb diff should raise HDiffPatchError"
    # ~512 MiB would be allocated without the cap; allow generous headroom for the
    # allocator while still being far below the uncapped footprint.
    assert grew_mib < 128, f"apply_lite over-allocated on a malformed diff: grew {grew_mib:.1f} MiB"
