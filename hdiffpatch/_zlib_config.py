"""ZlibConfig class for configuring zlib compression parameters."""

from enum import Enum
from typing import Union

import attrs

from ._base_config import BaseConfig


class ZlibStrategy(Enum):
    """Zlib compression strategies."""

    DEFAULT = "default"
    FILTERED = "filtered"
    HUFFMAN_ONLY = "huffman_only"
    RLE = "rle"
    FIXED = "fixed"


def _convert_strategy(value: Union[ZlibStrategy, str]) -> ZlibStrategy:
    """Convert and validate strategy parameter.

    Parameters
    ----------
    value : ZlibStrategy or str
        The strategy value to convert

    Returns
    -------
    ZlibStrategy
        The validated strategy enum

    Raises
    ------
    TypeError
        If value is not a ZlibStrategy enum or string
    ValueError
        If string value is not a valid strategy
    """
    if isinstance(value, str):
        try:
            return ZlibStrategy(value.lower())
        except ValueError:
            valid_strategies = [s.value for s in ZlibStrategy]
            raise ValueError(f"Invalid strategy '{value}'. Valid options: {valid_strategies}") from None
    elif isinstance(value, ZlibStrategy):
        return value
    else:
        raise TypeError("strategy must be a ZlibStrategy enum or string")


@attrs.frozen
class ZlibConfig(BaseConfig):
    """Configuration for zlib compression parameters.

    This class allows fine-grained control over zlib compression behavior,
    including compression level, memory usage, window size, and strategy.

    Parameters
    ----------
    level : int, default=9
        Compression level (0-9). Higher values give better
        compression but are slower. 0 = no compression, 9 = best compression.
    memory_level : int, default=8
        Memory level (1-9). Higher values use more memory but
        may improve compression speed.
    window : int, default=15
        Window size as power of 2 (9-15). Larger windows give
        better compression but use more memory. (32KB window)
    strategy : ZlibStrategy, default=ZlibStrategy.DEFAULT
        Compression strategy optimized for different data types.
    save_window_bits : bool, default=True
        Whether to save window bits in compressed data header.

    Examples
    --------
    Fast compression with minimal memory usage

    >>> config = ZlibConfig(level=1, memory_level=1, window=9)

    Best compression for text data

    >>> config = ZlibConfig(level=9, strategy=ZlibStrategy.DEFAULT)

    Optimized for PNG-like data

    >>> config = ZlibConfig(strategy=ZlibStrategy.RLE)
    """

    level: int = attrs.field(
        default=9,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(9),
        ),
    )
    memory_level: int = attrs.field(
        default=8,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(9),
        ),
    )
    window: int = attrs.field(
        default=15,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(9),
            attrs.validators.le(15),
        ),
    )
    strategy: ZlibStrategy = attrs.field(
        default=ZlibStrategy.DEFAULT,
        converter=_convert_strategy,
    )
    save_window_bits: bool = attrs.field(
        default=True,
        converter=bool,
    )

    @classmethod
    def fast(cls) -> "ZlibConfig":
        """Create a ZlibConfig optimized for speed.

        Returns
        -------
        ZlibConfig
            Configuration optimized for speed
        """
        return cls(level=1, memory_level=1, window=9)

    @classmethod
    def balanced(cls) -> "ZlibConfig":
        """Create a ZlibConfig with balanced speed/compression.

        Returns
        -------
        ZlibConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(level=6, memory_level=8, window=15)

    @classmethod
    def best_compression(cls) -> "ZlibConfig":
        """Create a ZlibConfig optimized for best compression.

        Returns
        -------
        ZlibConfig
            Configuration optimized for best compression
        """
        return cls(level=9, memory_level=9, window=15)

    @classmethod
    def minimal_memory(cls) -> "ZlibConfig":
        """Create a ZlibConfig with minimal memory usage.

        Returns
        -------
        ZlibConfig
            Configuration with minimal memory usage
        """
        return cls(level=6, memory_level=1, window=9)

    @classmethod
    def png_optimized(cls) -> "ZlibConfig":
        """Create a ZlibConfig optimized for PNG-like data.

        Returns
        -------
        ZlibConfig
            Configuration optimized for PNG-like data
        """
        return cls(level=9, strategy=ZlibStrategy.RLE)
