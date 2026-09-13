"""Unit tests for hdiffpatch.create_lite_diff (HPatchLite lite-format diffs)."""

import pytest

import hdiffpatch
from hdiffpatch._c_extension import _check_lite_diff

# Codecs HPatchLite can decode. "tamp" round-trips through the vendored tamp
# decompressor plugin. The on-device compress-type tag written into the lite
# header is asserted directly in test_create_lite_diff_header_compression_tag;
# check_lite_diff itself treats that byte as opaque and does not validate it.
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


def test_create_lite_diff_basic(simple_text_data):
    """A lite diff is non-empty bytes that reconstructs the target."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data)

    assert isinstance(lite, bytes)
    assert len(lite) > 0
    assert _check_lite_diff(old_data, new_data, lite)


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_create_lite_diff_round_trip(compression, large_repetitive_data):
    """Round-trip via the vendored HPatchLite applier for each supported codec."""
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data, compression=compression)

    assert isinstance(lite, bytes)
    assert len(lite) > 0
    assert _check_lite_diff(old_data, new_data, lite, compression=compression), (
        f"Lite round-trip failed for {compression}"
    )


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_create_lite_diff_round_trip_binary(compression, binary_data):
    """Round-trip on binary data for each supported codec."""
    old_data = binary_data["old"]
    new_data = binary_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data, compression=compression)

    assert _check_lite_diff(old_data, new_data, lite, compression=compression)


@pytest.mark.parametrize(
    "config",
    [
        hdiffpatch.ZlibConfig(),
        hdiffpatch.LzmaConfig(),
        hdiffpatch.TampConfig(window=10),
    ],
)
def test_create_lite_diff_config_objects(config, highly_compressible_data):
    """Supported ``*Config`` objects produce valid lite diffs."""
    old_data = highly_compressible_data["old"]
    new_data = highly_compressible_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data, compression=config)

    assert _check_lite_diff(old_data, new_data, lite, compression=config)


@pytest.mark.parametrize("compression", LITE_SUPPORTED)
def test_create_lite_diff_header_compression_tag(compression, large_repetitive_data):
    """The lite header's compress-type byte matches the device dispatch tag.

    hpatch_lite_open reads this byte (offset 2, after the b"hI" magic) opaquely
    and does not validate it, so the round-trip validator cannot catch a wrong
    tag. Assert the raw byte directly to cover the device dispatch contract,
    including the vendor-specific tamp value.
    """
    old_data = large_repetitive_data["old"]
    new_data = large_repetitive_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data, compression=compression)

    assert lite[:2] == b"hI"
    assert lite[2] == LITE_HEADER_TAG[compression]


def test_create_lite_diff_validate_default_catches_round_trip(simple_text_data):
    """validate=True (the default) verifies reconstruction via HPatchLite."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    # Should not raise; validation runs the real applier internally.
    lite_validated = hdiffpatch.create_lite_diff(old_data, new_data, validate=True)
    lite_unvalidated = hdiffpatch.create_lite_diff(old_data, new_data, validate=False)

    # Both paths emit the same bytes; validation only adds a check.
    assert lite_validated == lite_unvalidated
    assert _check_lite_diff(old_data, new_data, lite_unvalidated)


@pytest.mark.parametrize("compression", LITE_UNSUPPORTED)
def test_create_lite_diff_rejects_unsupported_codec(compression, simple_text_data):
    """Codecs HPatchLite cannot decode are rejected with a clear error."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    with pytest.raises(hdiffpatch.HDiffPatchError, match="not supported by HPatchLite"):
        hdiffpatch.create_lite_diff(old_data, new_data, compression=compression)


@pytest.mark.parametrize(
    "config",
    [
        hdiffpatch.ZStdConfig(),
        hdiffpatch.Lzma2Config(),
        hdiffpatch.BZip2Config(),
    ],
)
def test_create_lite_diff_rejects_unsupported_config(config, simple_text_data):
    """Unsupported ``*Config`` objects are rejected with a clear error."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    with pytest.raises(hdiffpatch.HDiffPatchError, match="not supported by HPatchLite"):
        hdiffpatch.create_lite_diff(old_data, new_data, compression=config)


def test_create_lite_diff_invalid_compression_type(simple_text_data):
    """A totally invalid compression name raises ValueError."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    with pytest.raises(ValueError, match="Invalid compression type"):
        hdiffpatch.create_lite_diff(old_data, new_data, compression="not_a_codec")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_old,bad_new", [("str", b"bytes"), (b"bytes", "str"), (123, 456)])
def test_create_lite_diff_type_errors(bad_old, bad_new):
    """Non-bytes inputs raise TypeError."""
    with pytest.raises(TypeError):
        hdiffpatch.create_lite_diff(bad_old, bad_new)


def test_check_lite_diff_detects_wrong_target(simple_text_data):
    """The validator returns False when the diff does not match the target."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data)

    # Use a wrong target of the *same length* as new_data so validation gets
    # past the header size check and actually exercises the reconstructed-byte
    # comparison (a different-length target would be rejected earlier).
    wrong_target = bytes(b ^ 0xFF for b in new_data)
    assert len(wrong_target) == len(new_data)
    assert wrong_target != new_data
    assert not _check_lite_diff(old_data, wrong_target, lite)


def test_create_lite_diff_not_standard_apply_compatible(simple_text_data):
    """Lite output is not consumable by the standard apply()."""
    old_data = simple_text_data["old"]
    new_data = simple_text_data["new"]

    lite = hdiffpatch.create_lite_diff(old_data, new_data)

    with pytest.raises(hdiffpatch.HDiffPatchError):
        hdiffpatch.apply(old_data, lite)


def test_create_lite_diff_in_public_api():
    """create_lite_diff is exported from the package namespace."""
    assert "create_lite_diff" in hdiffpatch.__all__
    assert hdiffpatch.create_lite_diff is not None
