"""BrotliConfig class for configuring brotli compression parameters."""

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class BrotliConfig(BaseConfig):
    """Configuration for brotli compression parameters.

    Parameters
    ----------
    level : int, default=9
        Compression quality (0-11). Higher values give better compression but
        are slower. 0 = fastest, 11 = best compression.
    window : int, default=24
        Window size as log2 (10-30). Larger windows give better compression
        but use more memory. Windows above 24 use brotli's "large window"
        extension, which standard (RFC 7932) brotli decoders reject. The
        encoder shrinks the window to fit the input when the input is smaller.

    Examples
    --------
    Fast compression with a small window

    >>> config = BrotliConfig(level=1, window=16)

    Best compression

    >>> config = BrotliConfig(level=11, window=24)
    """

    level: int = attrs.field(
        default=9,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(11),
        ),
    )
    window: int = attrs.field(
        default=24,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(10),
            attrs.validators.le(30),
        ),
    )

    @classmethod
    def fast(cls) -> "BrotliConfig":
        """Create a BrotliConfig optimized for speed.

        Returns
        -------
        BrotliConfig
            Configuration optimized for speed
        """
        return cls(level=1, window=18)

    @classmethod
    def balanced(cls) -> "BrotliConfig":
        """Create a BrotliConfig with balanced speed/compression.

        Returns
        -------
        BrotliConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, window=22)

    @classmethod
    def best_compression(cls) -> "BrotliConfig":
        """Create a BrotliConfig optimized for best compression.

        Returns
        -------
        BrotliConfig
            Configuration optimized for best compression
        """
        return cls(level=11, window=24)

    @classmethod
    def minimal_memory(cls) -> "BrotliConfig":
        """Create a BrotliConfig with minimal memory usage.

        Returns
        -------
        BrotliConfig
            Configuration with minimal memory usage
        """
        return cls(level=6, window=10)
