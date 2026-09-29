from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ._base_config import BaseConfig

CompressionType = Literal[
    "none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp", "xz", "lz4", "lz4hc", "tuz", "brotli", "lzham"
]
# The subset of CompressionType that has a lite compress-type byte.
LiteCompressionType = Literal[
    "none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp", "lz4", "lz4hc", "tuz", "brotli", "lzham"
]

# Constants for convenience
COMPRESSION_NONE: CompressionType = "none"
COMPRESSION_ZLIB: CompressionType = "zlib"
COMPRESSION_LZMA: CompressionType = "lzma"
COMPRESSION_LZMA2: CompressionType = "lzma2"
COMPRESSION_ZSTD: CompressionType = "zstd"
COMPRESSION_BZIP2: CompressionType = "bzip2"
COMPRESSION_TAMP: CompressionType = "tamp"
COMPRESSION_XZ: CompressionType = "xz"
COMPRESSION_LZ4: CompressionType = "lz4"
COMPRESSION_LZ4HC: CompressionType = "lz4hc"
COMPRESSION_TUZ: CompressionType = "tuz"
COMPRESSION_BROTLI: CompressionType = "brotli"
COMPRESSION_LZHAM: CompressionType = "lzham"

class HDiffPatchError(Exception):
    """Base exception for HDiffPatch operations."""

    ...

def diff(
    old_data: bytes,
    new_data: bytes,
    compression: CompressionType | BaseConfig | None = None,
    *,
    validate: bool = True,
    big_cache_match: bool = False,
) -> bytes:
    """Create a binary diff between old and new data using HDiffPatch.

    Parameters
    ----------
    old_data : bytes
        The original data
    new_data : bytes
        The new data to diff against
    compression : CompressionType, BaseConfig, or None, default=None
        Compression algorithm to use
    validate : bool, default=True
        If True, validates that applying the diff to old_data produces new_data
    big_cache_match : bool, default=False
        If True, builds an extra match cache over ``old_data`` (a bloom filter of
        roughly 0.5-1 byte per byte of ``old_data``) so candidate matches are
        rejected without a suffix-array search. Diff creation gets faster and
        the output is byte-identical; see the Performance docs for measurements
        and trade-offs.

    Returns
    -------
    bytes
        The diff data as bytes

    Raises
    ------
    TypeError
        If old_data or new_data are not bytes
    HDiffPatchError
        If diff creation fails or roundtrip validation fails
    """
    ...

def apply(
    old_data: bytes,
    diff_data: bytes,
) -> bytes:
    """Apply a patch to old data to produce new data using HDiffPatch.

    The compression type is automatically detected from the diff data header.

    Parameters
    ----------
    old_data : bytes
        The original data
    diff_data : bytes
        The diff/patch data

    Returns
    -------
    bytes
        The patched data as bytes

    Raises
    ------
    TypeError
        If old_data or diff_data are not bytes
    HDiffPatchError
        If patch application fails
    MemoryError
        If memory allocation fails
    """
    ...

def recompress(
    diff_data: bytes,
    compression: CompressionType | BaseConfig | None,
) -> bytes:
    """Recompress a diff with a different compression algorithm.

    This function can recompress diffs in HDiffPatch's compressed diff format, which includes
    diffs created by hdiffz (both compressed and uncompressed). The input format is automatically
    detected and the diff is recompressed with the specified compression algorithm.

    Supports both single-compressed and regular compressed diff formats. Works with diffs
    created by hdiffz tool and the hdiffpatch.diff() function when explicit compression is used.

    Parameters
    ----------
    diff_data : bytes
        The diff data to recompress
    compression : CompressionType, BaseConfig, or None
        Target compression algorithm to use. Pass ``"none"`` (or ``None``)
        to strip compression from the diff.

    Returns
    -------
    bytes
        The recompressed diff data

    Raises
    ------
    TypeError
        If diff_data is not bytes
    HDiffPatchError
        If recompression fails or input format is unsupported
    ValueError
        If compression type is invalid
    """
    ...

def diff_lite(
    old_data: bytes,
    new_data: bytes,
    *,
    compression: LiteCompressionType | BaseConfig | None = None,
    validate: bool = True,
    big_cache_match: bool = False,
) -> bytes:
    """Create an HPatchLite "lite"-format binary diff between old and new data.

    Lite diffs are the compact format consumed by HDiffPatch's tiny on-device
    applier (``hpatch_lite_patch``). This output is **not** interchangeable with
    ``diff``/``apply``; it can only be applied by an HPatchLite-family patcher.

    Parameters
    ----------
    old_data : bytes
        The original data.
    new_data : bytes
        The new data to diff against.
    compression : LiteCompressionType, BaseConfig, or None, default=None
        Compression algorithm to use. Any codec with a compress-type byte in the
        lite header is accepted: ``"none"``, ``"zlib"``, ``"lzma"``,
        ``"lzma2"``, ``"zstd"``, ``"bzip2"``, ``"lz4"``, ``"lz4hc"``, ``"tuz"``,
        ``"brotli"``, ``"lzham"``, and ``"tamp"`` (the latter under the
        vendor-specific byte ``0xF0``). A device can only apply the codecs whose
        decoders it links.
    validate : bool, default=True
        If True, validates that the lite diff reconstructs new_data from old_data
        using the vendored HPatchLite applier.
    big_cache_match : bool, default=False
        If True, builds an extra match cache over ``old_data`` (a bloom filter of
        roughly 0.5-1 byte per byte of ``old_data``) so candidate matches are
        rejected without a suffix-array search. Diff creation gets faster and
        the output is byte-identical; see the Performance docs for measurements
        and trade-offs.

    Returns
    -------
    bytes
        The lite-format diff data as bytes.

    Raises
    ------
    TypeError
        If old_data or new_data are not bytes.
    ValueError
        If compression is not a recognized compression type.
    HDiffPatchError
        If the codec has no lite compress-type byte, if diff creation fails, or
        if roundtrip validation fails.
    """
    ...

def apply_lite(old_data: bytes, lite_diff: bytes) -> bytes:
    """Apply an HPatchLite "lite"-format patch to reconstruct the new data.

    The lite-format counterpart of ``apply``. Drives the vendored HPatchLite
    applier (``hpatch_lite_open`` + ``hpatch_lite_patch``) -- the same code path
    a device runs -- to reconstruct the new bytes from ``old_data`` and a
    ``lite_diff`` produced by ``diff_lite``.

    The compression codec is auto-detected from the self-describing lite header
    (upstream codecs by their ``hpi_compressType`` values, tamp by the
    vendor-specific ``0xF0`` byte), so there is no ``compression`` argument.

    Parameters
    ----------
    old_data : bytes
        The original data the patch was created against.
    lite_diff : bytes
        The lite-format diff produced by ``diff_lite``.

    Returns
    -------
    bytes
        The reconstructed new data.

    Raises
    ------
    TypeError
        If old_data or lite_diff are not bytes.
    HDiffPatchError
        If the header is invalid, names a codec whose decompressor is not
        available, or the patch fails to reconstruct the data.
    """
    ...

def recompress_lite(
    lite_diff: bytes,
    compression: LiteCompressionType | BaseConfig | None,
) -> bytes:
    """Recompress an HPatchLite "lite"-format diff with a different compression algorithm.

    This is the lite-format counterpart of ``recompress``. Only the diff
    body is re-encoded; the match search is not redone, so for a diff made by
    ``diff_lite`` the output is byte-identical to calling ``diff_lite`` with
    ``compression`` directly.
    A common pattern is to create the diff once uncompressed
    (``diff_lite(old, new)``) and then derive each compressed variant from it.

    The input's codec is auto-detected from the lite header. Inplace-variant
    headers (version code 2, carrying ``extraSafeSize``) are preserved.

    Parameters
    ----------
    lite_diff : bytes
        A lite-format diff, compressed with any lite codec or uncompressed.
    compression : LiteCompressionType, BaseConfig, or None
        Target compression, with the same accepted forms as ``diff_lite``:
        any lite codec name or a matching ``*Config``. ``None``/``"none"``
        stores the body uncompressed.

    Returns
    -------
    bytes
        The recompressed lite-format diff.

    Raises
    ------
    TypeError
        If lite_diff is not bytes.
    ValueError
        If compression is not a recognized compression type.
    HDiffPatchError
        If the codec has no lite compress-type byte, or if the lite diff's
        header or body is malformed.
    """
    ...
