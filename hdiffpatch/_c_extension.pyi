from typing import TYPE_CHECKING, Literal, Union

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
    compression: Union[CompressionType, BaseConfig, None] = None,
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
    compression: Union[CompressionType, BaseConfig, None] = None,
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
    compression : CompressionType, BaseConfig, or None, default=None
        Target compression algorithm to use

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
