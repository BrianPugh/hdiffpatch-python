# Don't manually change, let poetry-dynamic-versioning handle it.
__version__ = "0.0.0"

__all__ = [
    # Types and constants
    "COMPRESSION_BZIP2",
    "COMPRESSION_LZMA",
    "COMPRESSION_LZMA2",
    "COMPRESSION_NONE",
    "COMPRESSION_TAMP",
    "COMPRESSION_ZLIB",
    "COMPRESSION_ZSTD",
    "CompressionType",
    # Exceptions
    "HDiffPatchError",
    # Core functions
    "diff",
    "apply",
    "recompress",
    # Configuration classes
    "BaseConfig",
    "BZip2Config",
    "ZlibConfig",
    "ZlibStrategy",
    "LzmaConfig",
    "Lzma2Config",
    "TampConfig",
    "ZStdConfig",
]

from ._base_config import (
    BaseConfig,
)
from ._bzip2_config import (
    BZip2Config,
)
from ._c_extension import (
    # Types and constants
    COMPRESSION_BZIP2,
    COMPRESSION_LZMA,
    COMPRESSION_LZMA2,
    COMPRESSION_NONE,
    COMPRESSION_TAMP,
    COMPRESSION_ZLIB,
    COMPRESSION_ZSTD,
    CompressionType,
    # Exceptions
    HDiffPatchError,
    # Core functions
    apply,
    diff,
    recompress,
)
from ._lzma_config import (
    Lzma2Config,
    LzmaConfig,
)
from ._tamp_config import (
    TampConfig,
)
from ._zlib_config import (
    ZlibConfig,
    ZlibStrategy,
)
from ._zstd_config import (
    ZStdConfig,
)
