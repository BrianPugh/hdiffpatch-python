"""XzConfig class for configuring xz compression parameters."""

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class XzConfig(BaseConfig):
    """Configuration for xz compression parameters.

    xz wraps an LZMA2 stream in the xz container format (``.xz``), so it takes
    the same parameters as :class:`Lzma2Config`.

    Parameters
    ----------
    level : int, default=7
        Compression level (0-9). Higher values give better
        compression but are slower. 0 = fastest, 9 = best compression.
    window : int, default=23
        Window size as log2. Must be between 12 and 30.
        Larger windows give better compression but use more memory.
        (23 = 8MB window)
    threads : int, default=1
        Number of threads (1-64).

    Examples
    --------
    Fast compression with minimal memory usage (4KB window)

    >>> config = XzConfig(level=1, window=12, threads=1)

    Best compression for large files with multiple threads (32MB window)

    >>> config = XzConfig(level=9, window=25, threads=8)
    """

    level: int = attrs.field(
        default=7,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(9),
        ),
    )
    window: int = attrs.field(
        default=23,  # 8MB (2^23)
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(12),
            attrs.validators.le(30),
        ),
    )
    threads: int = attrs.field(
        default=1,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(64),
        ),
    )

    @classmethod
    def fast(cls) -> "XzConfig":
        """Create an XzConfig optimized for speed.

        Returns
        -------
        XzConfig
            Configuration optimized for speed
        """
        return cls(level=1, window=12, threads=1)

    @classmethod
    def balanced(cls) -> "XzConfig":
        """Create an XzConfig with balanced speed/compression.

        Returns
        -------
        XzConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, window=23, threads=4)

    @classmethod
    def best_compression(cls) -> "XzConfig":
        """Create an XzConfig optimized for best compression.

        Returns
        -------
        XzConfig
            Configuration optimized for best compression
        """
        return cls(level=9, window=25, threads=8)

    @classmethod
    def minimal_memory(cls) -> "XzConfig":
        """Create an XzConfig with minimal memory usage.

        Returns
        -------
        XzConfig
            Configuration with minimal memory usage
        """
        return cls(level=6, window=12, threads=1)
