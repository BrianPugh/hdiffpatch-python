from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ._base_config import BaseConfig

CompressionType = Literal["none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp"]

# Constants for convenience
COMPRESSION_NONE: CompressionType = "none"
COMPRESSION_ZLIB: CompressionType = "zlib"
COMPRESSION_LZMA: CompressionType = "lzma"
COMPRESSION_LZMA2: CompressionType = "lzma2"
COMPRESSION_ZSTD: CompressionType = "zstd"
COMPRESSION_BZIP2: CompressionType = "bzip2"
COMPRESSION_TAMP: CompressionType = "tamp"

class HDiffPatchError(Exception):
    """Base exception for HDiffPatch operations."""

    ...

def diff(
    old_data: bytes,
    new_data: bytes,
    compression: CompressionType | BaseConfig | None = None,
    *,
    validate: bool = True,
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

def create_lite_diff(
    old_data: bytes,
    new_data: bytes,
    *,
    compression: CompressionType | BaseConfig | None = None,
    validate: bool = True,
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
    compression : CompressionType, BaseConfig, or None, default=None
        Compression algorithm to use. Only codecs decodable by HPatchLite are
        accepted: ``"none"``, ``"zlib"``, ``"lzma"``, and ``"tamp"`` (the latter
        via a device-side decompressor plugin). Passing ``"zstd"``, ``"lzma2"``,
        or ``"bzip2"`` (as a name or ``*Config``) raises ``HDiffPatchError``.
    validate : bool, default=True
        If True, validates that the lite diff reconstructs new_data from old_data
        using the vendored HPatchLite applier.

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
        If the codec is not supported by HPatchLite, if diff creation fails, or
        if roundtrip validation fails.
    """
    ...

def _check_lite_diff(
    old_data: bytes,
    new_data: bytes,
    lite_diff: bytes,
    compression: CompressionType | BaseConfig | None = None,
) -> bool:
    """Verify a lite diff by reconstructing new_data via the HPatchLite applier.

    Internal helper (not part of the public API).

    Parameters
    ----------
    old_data : bytes
        The original data.
    new_data : bytes
        The expected reconstructed data.
    lite_diff : bytes
        The lite-format diff produced by ``create_lite_diff``.
    compression : CompressionType, BaseConfig, or None, default=None
        The compression the diff was created with, used to select the matching
        decompressor.

    Returns
    -------
    bool
        True if the lite diff reconstructs new_data from old_data.

    Raises
    ------
    TypeError
        If any of old_data, new_data, or lite_diff are not bytes.
    """
    ...
