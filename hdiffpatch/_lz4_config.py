"""Lz4Config and Lz4HCConfig classes for configuring LZ4 compression parameters."""

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class Lz4Config(BaseConfig):
    """Configuration for LZ4 (fast mode) compression parameters.

    Parameters
    ----------
    level : int, default=50
        Compression level (1-50). Higher values give better compression but
        are slower. 50 = best compression (LZ4 acceleration 1), 1 = fastest
        (LZ4 acceleration 50).

    Examples
    --------
    Fastest compression

    >>> config = Lz4Config(level=1)

    Best compression in fast mode

    >>> config = Lz4Config(level=50)
    """

    level: int = attrs.field(
        default=50,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(50),
        ),
    )

    @classmethod
    def fast(cls) -> "Lz4Config":
        """Create an Lz4Config optimized for speed.

        Returns
        -------
        Lz4Config
            Configuration optimized for speed
        """
        return cls(level=1)

    @classmethod
    def balanced(cls) -> "Lz4Config":
        """Create an Lz4Config with balanced speed/compression.

        Returns
        -------
        Lz4Config
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=40)

    @classmethod
    def best_compression(cls) -> "Lz4Config":
        """Create an Lz4Config optimized for best compression.

        Returns
        -------
        Lz4Config
            Configuration optimized for best compression
        """
        return cls(level=50)

    @classmethod
    def minimal_memory(cls) -> "Lz4Config":
        """Create an Lz4Config with minimal memory usage.

        The level does not change LZ4's memory use, so this is the default level.

        Returns
        -------
        Lz4Config
            Configuration with minimal memory usage
        """
        return cls(level=50)


@attrs.frozen
class Lz4HCConfig(BaseConfig):
    """Configuration for LZ4 high-compression (LZ4HC) parameters.

    LZ4HC output is a regular LZ4 stream, so it decodes with the same
    decompressor as :class:`Lz4Config`; only compression is slower.

    Parameters
    ----------
    level : int, default=11
        Compression level (3-12). Higher values give better compression but
        are slower. 12 = best compression.

    Examples
    --------
    Fast high-compression

    >>> config = Lz4HCConfig(level=3)

    Best compression

    >>> config = Lz4HCConfig(level=12)
    """

    level: int = attrs.field(
        default=11,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(3),
            attrs.validators.le(12),
        ),
    )

    @classmethod
    def fast(cls) -> "Lz4HCConfig":
        """Create an Lz4HCConfig optimized for speed.

        Returns
        -------
        Lz4HCConfig
            Configuration optimized for speed
        """
        return cls(level=3)

    @classmethod
    def balanced(cls) -> "Lz4HCConfig":
        """Create an Lz4HCConfig with balanced speed/compression.

        Returns
        -------
        Lz4HCConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=9)

    @classmethod
    def best_compression(cls) -> "Lz4HCConfig":
        """Create an Lz4HCConfig optimized for best compression.

        Returns
        -------
        Lz4HCConfig
            Configuration optimized for best compression
        """
        return cls(level=12)

    @classmethod
    def minimal_memory(cls) -> "Lz4HCConfig":
        """Create an Lz4HCConfig with minimal memory usage.

        The level does not change LZ4's memory use, so this is the default level.

        Returns
        -------
        Lz4HCConfig
            Configuration with minimal memory usage
        """
        return cls(level=11)
