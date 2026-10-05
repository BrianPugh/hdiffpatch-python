"""TuzConfig class for configuring tinyuz compression parameters."""

import attrs

from ._base_config import BaseConfig


@attrs.frozen
class TuzConfig(BaseConfig):
    """Configuration for tinyuz compression parameters.

    tinyuz is a small-footprint LZ77 codec whose decoder needs only
    ``dict_size`` bytes of dictionary plus a small code cache.

    Parameters
    ----------
    dict_size : int, default=16777216
        Dictionary size in bytes (1 to 2**30). Any value is allowed, not just
        powers of 2. Larger dictionaries compress better but cost memory on
        both sides: decompression needs ``dict_size`` bytes plus a small code
        cache, and compression needs, per thread, roughly ``18 * dict_size``
        bytes plus about 0.5 MB. The encoder shrinks it to the input size
        when the input is smaller.
    max_save_length : int, default=65535
        Longest match length (127-65535).
    threads : int, default=1
        Number of compression threads (1-64).
    literal_line : bool, default=False
        Emit literal-line control codes, which store runs of incompressible
        bytes more compactly. The decoder must be built with
        ``tuz_isNeedLiteralLine`` (tinyuz's default) to read them.

    Examples
    --------
    Small dictionary for a memory-constrained decoder

    >>> config = TuzConfig(dict_size=4096)

    Best compression

    >>> config = TuzConfig(dict_size=1 << 24, literal_line=True)
    """

    dict_size: int = attrs.field(
        default=1 << 24,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(1),
            attrs.validators.le(1 << 30),
        ),
    )
    max_save_length: int = attrs.field(
        default=65535,
        validator=attrs.validators.and_(
            attrs.validators.instance_of(int),
            attrs.validators.ge(127),
            attrs.validators.le(65535),
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
    literal_line: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )

    @classmethod
    def fast(cls) -> "TuzConfig":
        """Create a TuzConfig optimized for speed.

        Returns
        -------
        TuzConfig
            Configuration optimized for speed
        """
        return cls(dict_size=1 << 16, max_save_length=1023)

    @classmethod
    def balanced(cls) -> "TuzConfig":
        """Create a TuzConfig with balanced speed/compression.

        Returns
        -------
        TuzConfig
            Configuration with balanced speed/compression tradeoff
        """
        return cls(dict_size=1 << 20)

    @classmethod
    def best_compression(cls) -> "TuzConfig":
        """Create a TuzConfig optimized for best compression.

        Returns
        -------
        TuzConfig
            Configuration optimized for best compression
        """
        return cls(dict_size=1 << 24, literal_line=True)

    @classmethod
    def minimal_memory(cls) -> "TuzConfig":
        """Create a TuzConfig with minimal memory usage.

        Returns
        -------
        TuzConfig
            Configuration with minimal memory usage
        """
        return cls(dict_size=1 << 10)
