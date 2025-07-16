"""Base configuration class for compression configs."""

import attrs


@attrs.frozen
class BaseConfig:
    """Base class for all compression configuration classes.

    This class provides common functionality for all compression configurations,
    including standardized classmethods for creating common configuration presets.
    """

    @classmethod
    def fast(cls):
        """Create a config optimized for speed.

        Returns
        -------
        BaseConfig
            Configuration optimized for speed
        """
        raise NotImplementedError(f"{cls.__name__} does not implement fast() classmethod")

    @classmethod
    def balanced(cls):
        """Create a config with balanced speed/compression.

        Returns
        -------
        BaseConfig
            Configuration with balanced speed/compression tradeoff
        """
        raise NotImplementedError(f"{cls.__name__} does not implement balanced() classmethod")

    @classmethod
    def best_compression(cls):
        """Create a config optimized for best compression.

        Returns
        -------
        BaseConfig
            Configuration optimized for best compression
        """
        raise NotImplementedError(f"{cls.__name__} does not implement best_compression() classmethod")

    @classmethod
    def minimal_memory(cls):
        """Create a config with minimal memory usage.

        Returns
        -------
        BaseConfig
            Configuration with minimal memory usage
        """
        raise NotImplementedError(f"{cls.__name__} does not implement minimal_memory() classmethod")
