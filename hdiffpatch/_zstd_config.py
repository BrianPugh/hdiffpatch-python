"""ZStdConfig class for configuring zstd compression parameters."""

from typing import Optional

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class ZStdConfig(BaseConfig):
    """Configuration for zstd compression parameters.

    This class allows control over zstd compression behavior,
    including compression level, window size, and threading.

    Parameters
    ----------
    level : int, default=3
        Compression level (1-22). Higher values give better
        compression but are slower. 1 = fastest, 22 = best compression.
    window : int or None, default=None
        Window size as log2. Must be between 10 and 27.
        Larger windows give better compression but use more memory.
        None uses zstd default based on compression level.
    workers : int, default=0
        Number of worker threads (0-200). 0 = single-threaded.

    Examples
    --------
    Fast compression with minimal memory usage

    >>> config = ZStdConfig(level=1, workers=0)

    Best compression for large files with multiple threads

    >>> config = ZStdConfig(level=22, workers=4)

    Balanced compression with custom window size

    >>> config = ZStdConfig(level=6, window=20, workers=2)
    """

    level: int = attrs.field(
        default=3,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(22),
        ),
    )
    window: Optional[int] = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(int),
                attrs.validators.ge(10),
                attrs.validators.le(27),
            )
        ),
    )
    workers: int = attrs.field(
        default=0,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(200),
        ),
    )

    @classmethod
    def fast(cls) -> "ZStdConfig":
        """Create a ZStdConfig optimized for speed.

        Returns
        -------
        ZStdConfig
            Configuration optimized for speed
        """
        return cls(level=1, workers=0)

    @classmethod
    def balanced(cls) -> "ZStdConfig":
        """Create a ZStdConfig with balanced speed/compression.

        Returns
        -------
        ZStdConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, workers=2)

    @classmethod
    def best_compression(cls) -> "ZStdConfig":
        """Create a ZStdConfig optimized for best compression.

        Returns
        -------
        ZStdConfig
            Configuration optimized for best compression
        """
        return cls(level=22, window=27, workers=4)

    @classmethod
    def minimal_memory(cls) -> "ZStdConfig":
        """Create a ZStdConfig with minimal memory usage.

        Returns
        -------
        ZStdConfig
            Configuration with minimal memory usage
        """
        return cls(level=3, window=10, workers=0)
