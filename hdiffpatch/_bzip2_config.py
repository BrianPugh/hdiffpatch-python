"""BZip2Config class for configuring bzip2 compression parameters."""

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class BZip2Config(BaseConfig):
    """Configuration for bzip2 compression parameters.

    This class allows control over bzip2 compression behavior via the
    compression level, which trades speed for compression ratio and
    memory usage.

    Parameters
    ----------
    level : int, default=9
        Compression level (1-9). Higher values give better
        compression but are slower. 1 = fastest, 9 = best compression.

    Examples
    --------
    Fast compression

    >>> config = BZip2Config(level=1)

    Best compression

    >>> config = BZip2Config(level=9)
    """

    level: int = attrs.field(
        default=9,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(9),
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
        return cls(level=1)

    @classmethod
    def balanced(cls) -> "BZip2Config":
        """Create a BZip2Config with balanced speed/compression.

        Returns
        -------
        BZip2Config
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6)

    @classmethod
    def best_compression(cls) -> "BZip2Config":
        """Create a BZip2Config optimized for best compression.

        Returns
        -------
        BZip2Config
            Configuration optimized for best compression
        """
        return cls(level=9)

    @classmethod
    def minimal_memory(cls) -> "BZip2Config":
        """Create a BZip2Config with minimal memory usage.

        Returns
        -------
        BZip2Config
            Configuration with minimal memory usage
        """
        return cls(level=1)
