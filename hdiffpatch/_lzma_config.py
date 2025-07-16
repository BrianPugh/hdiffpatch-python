"""LzmaConfig and Lzma2Config classes for configuring LZMA compression parameters."""

from typing import Union

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class LzmaConfig(BaseConfig):
    """Configuration for LZMA compression parameters.

    This class allows fine-grained control over LZMA compression behavior,
    including compression level, dictionary size, and thread usage.

    Parameters
    ----------
    level : int, default=9
        Compression level (0-9). Higher values give better
        compression but are slower. 0 = no compression, 9 = best compression.
    window : int, default=23
        Window size as log2. Must be between 12 and 30.
        Larger windows give better compression but use more memory.
        (23 = 8MB window)
    thread_num : int, default=1
        Number of threads (1-2). LZMA supports up to 2 threads.

    Examples
    --------
    Fast compression with minimal memory usage (4KB window)

    >>> config = LzmaConfig(level=1, window=12, thread_num=1)

    Best compression for large files (32MB window)

    >>> config = LzmaConfig(level=9, window=25, thread_num=2)

    Balanced compression (8MB window)

    >>> config = LzmaConfig(level=6, window=23, thread_num=1)
    """

    level: int = attrs.field(
        default=9,
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
    thread_num: int = attrs.field(
        default=1,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(2),
        ),
    )

    @classmethod
    def fast(cls) -> "LzmaConfig":
        """Create an LzmaConfig optimized for speed.

        Returns
        -------
        LzmaConfig
            Configuration optimized for speed
        """
        return cls(level=1, window=12, thread_num=1)

    @classmethod
    def balanced(cls) -> "LzmaConfig":
        """Create an LzmaConfig with balanced speed/compression.

        Returns
        -------
        LzmaConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, window=23, thread_num=1)

    @classmethod
    def best_compression(cls) -> "LzmaConfig":
        """Create an LzmaConfig optimized for best compression.

        Returns
        -------
        LzmaConfig
            Configuration optimized for best compression
        """
        return cls(level=9, window=25, thread_num=2)

    @classmethod
    def minimal_memory(cls) -> "LzmaConfig":
        """Create an LzmaConfig with minimal memory usage.

        Returns
        -------
        LzmaConfig
            Configuration with minimal memory usage
        """
        return cls(level=6, window=12, thread_num=1)


@attrs.frozen
class Lzma2Config(BaseConfig):
    """Configuration for LZMA2 compression parameters.

    This class allows fine-grained control over LZMA2 compression behavior,
    including compression level, dictionary size, and thread usage.

    Parameters
    ----------
    level : int, default=9
        Compression level (0-9). Higher values give better
        compression but are slower. 0 = no compression, 9 = best compression.
    window : int, default=23
        Window size as log2. Must be between 12 and 30.
        Larger windows give better compression but use more memory.
        (23 = 8MB window)
    thread_num : int, default=1
        Number of threads (1-64). LZMA2 supports up to 64 threads.

    Examples
    --------
    Fast compression with minimal memory usage (4KB window)

    >>> config = Lzma2Config(level=1, window=12, thread_num=1)

    Best compression for large files with multiple threads (32MB window)

    >>> config = Lzma2Config(level=9, window=25, thread_num=8)

    Balanced compression with moderate threading (8MB window)

    >>> config = Lzma2Config(level=6, window=23, thread_num=4)
    """

    level: int = attrs.field(
        default=9,
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
    thread_num: int = attrs.field(
        default=1,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(64),
        ),
    )

    @classmethod
    def fast(cls) -> "Lzma2Config":
        """Create an Lzma2Config optimized for speed.

        Returns
        -------
        Lzma2Config
            Configuration optimized for speed
        """
        return cls(level=1, window=12, thread_num=1)

    @classmethod
    def balanced(cls) -> "Lzma2Config":
        """Create an Lzma2Config with balanced speed/compression.

        Returns
        -------
        Lzma2Config
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, window=23, thread_num=4)

    @classmethod
    def best_compression(cls) -> "Lzma2Config":
        """Create an Lzma2Config optimized for best compression.

        Returns
        -------
        Lzma2Config
            Configuration optimized for best compression
        """
        return cls(level=9, window=25, thread_num=8)

    @classmethod
    def minimal_memory(cls) -> "Lzma2Config":
        """Create an Lzma2Config with minimal memory usage.

        Returns
        -------
        Lzma2Config
            Configuration with minimal memory usage
        """
        return cls(level=6, window=12, thread_num=1)
