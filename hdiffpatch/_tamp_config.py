"""TampConfig class for configuring tamp compression parameters."""

from typing import Optional

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class TampConfig(BaseConfig):
    """Configuration for tamp compression parameters.

    This class allows control over tamp compression behavior,
    including window size and custom dictionary support.

    Parameters
    ----------
    window : int, default=10
        Window size as power of 2 (8-15). Larger windows give
        better compression but use more memory. (1KB window)

    Examples
    --------
    Default configuration

    >>> config = TampConfig()

    Custom window size

    >>> config = TampConfig(window=12)
    """

    window: int = attrs.field(
        default=10,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(8),
            attrs.validators.le(15),
        ),
    )

    @classmethod
    def fast(cls) -> "TampConfig":
        """Create a TampConfig optimized for speed.

        Returns
        -------
        TampConfig
            Configuration optimized for speed
        """
        return cls(window=8)

    @classmethod
    def balanced(cls) -> "TampConfig":
        """Create a TampConfig with balanced speed/compression.

        Returns
        -------
        TampConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(window=10)

    @classmethod
    def best_compression(cls) -> "TampConfig":
        """Create a TampConfig optimized for best compression.

        Returns
        -------
        TampConfig
            Configuration optimized for best compression
        """
        return cls(window=15)

    @classmethod
    def minimal_memory(cls) -> "TampConfig":
        """Create a TampConfig with minimal memory usage.

        Returns
        -------
        TampConfig
            Configuration with minimal memory usage
        """
        return cls(window=8)
