"""LzhamConfig class for configuring LZHAM compression parameters."""

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class LzhamConfig(BaseConfig):
    """Configuration for LZHAM compression parameters.

    Parameters
    ----------
    level : int, default=3
        Compression level (0-5). 0-4 are LZHAM's fastest, faster, default,
        better and uber levels; 5 is uber with extreme parsing (slowest, best
        compression).
    window : int, default=24
        Dictionary size as log2 (15-29). Larger dictionaries give better
        compression but use more memory. 64-bit builds accept up to 29 and
        32-bit builds up to 26. The encoder shrinks the dictionary to fit the
        input when the input is smaller.
    threads : int, default=1
        Number of compression threads (1-64). With more than 1 thread the
        compressed bytes can differ from run to run (LZHAM's parse depends on
        thread scheduling), though every output decodes to the same data. The
        string ``"lzham"`` uses the upstream plugin's 4 threads.

    Examples
    --------
    Fast compression with a small dictionary

    >>> config = LzhamConfig(level=0, window=16)

    Best compression

    >>> config = LzhamConfig(level=5, window=26, threads=4)
    """

    level: int = attrs.field(
        default=3,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(5),
        ),
    )
    window: int = attrs.field(
        default=24,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(15),
            attrs.validators.le(29),
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
    def fast(cls) -> "LzhamConfig":
        """Create an LzhamConfig optimized for speed.

        Returns
        -------
        LzhamConfig
            Configuration optimized for speed
        """
        return cls(level=0, window=18)

    @classmethod
    def balanced(cls) -> "LzhamConfig":
        """Create an LzhamConfig with balanced speed/compression.

        Returns
        -------
        LzhamConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=2, window=22, threads=2)

    @classmethod
    def best_compression(cls) -> "LzhamConfig":
        """Create an LzhamConfig optimized for best compression.

        Returns
        -------
        LzhamConfig
            Configuration optimized for best compression
        """
        return cls(level=5, window=26, threads=4)

    @classmethod
    def minimal_memory(cls) -> "LzhamConfig":
        """Create an LzhamConfig with minimal memory usage.

        Returns
        -------
        LzhamConfig
            Configuration with minimal memory usage
        """
        return cls(level=3, window=15)
