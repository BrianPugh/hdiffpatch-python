"""BZip2Config class for configuring bzip2 compression parameters."""

from typing import Union

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class BZip2Config(BaseConfig):
    """Configuration for bzip2 compression parameters.

    This class allows fine-grained control over bzip2 compression behavior,
    including compression level and work factor for controlling compression
    speed and memory usage.

    Parameters
    ----------
    level : int, default=9
        Compression level (1-9). Higher values give better
        compression but are slower. 1 = fastest, 9 = best compression.
    work_factor : int, default=30
        Work factor (0-250). Controls how the compression algorithm
        behaves when dealing with worst-case scenarios. 0 = use default,
        higher values use more time but may achieve better compression.

    Examples
    --------
    Fast compression with minimal memory usage

    >>> config = BZip2Config(level=1, work_factor=0)

    Best compression with default work factor

    >>> config = BZip2Config(level=9)

    Balanced compression with increased work factor

    >>> config = BZip2Config(level=6, work_factor=100)
    """

    level: int = attrs.field(
        default=9,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(9),
        ),
    )
    work_factor: int = attrs.field(
        default=30,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(250),
        ),
    )

    @classmethod
    def fast(cls) -> "BZip2Config":
        """Create a BZip2Config optimized for speed.

        Returns
        -------
        BZip2Config
            Configuration optimized for speed
        """
        return cls(level=1, work_factor=0)

    @classmethod
    def balanced(cls) -> "BZip2Config":
        """Create a BZip2Config with balanced speed/compression.

        Returns
        -------
        BZip2Config
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, work_factor=30)

    @classmethod
    def best_compression(cls) -> "BZip2Config":
        """Create a BZip2Config optimized for best compression.

        Returns
        -------
        BZip2Config
            Configuration optimized for best compression
        """
        return cls(level=9, work_factor=100)

    @classmethod
    def minimal_memory(cls) -> "BZip2Config":
        """Create a BZip2Config with minimal memory usage.

        Returns
        -------
        BZip2Config
            Configuration with minimal memory usage
        """
        return cls(level=1, work_factor=0)
