# Don't manually change, let setuptools-scm handle it.
__version__ = "0.0.0"

__all__ = [
    # Types and constants
    "COMPRESSION_BROTLI",
    "COMPRESSION_BZIP2",
    "COMPRESSION_LZ4",
    "COMPRESSION_LZ4HC",
    "COMPRESSION_LZMA",
    "COMPRESSION_LZMA2",
    "COMPRESSION_NONE",
    "COMPRESSION_TAMP",
    "COMPRESSION_XZ",
    "COMPRESSION_TUZ",
    "COMPRESSION_ZLIB",
    "COMPRESSION_ZSTD",
    "CompressionType",
    "LiteCompressionType",
    # Exceptions
    "HDiffPatchError",
    # Core functions
    "diff",
    "diff_lite",
    "apply",
    "apply_lite",
    "recompress",
    "recompress_lite",
    # Configuration classes
    "BaseConfig",
    "BrotliConfig",
    "BZip2Config",
    "ZlibConfig",
    "ZlibStrategy",
    "Lz4Config",
    "Lz4HCConfig",
    "LzmaConfig",
    "Lzma2Config",
    "TampConfig",
    "XzConfig",
    "TuzConfig",
    "ZStdConfig",
]

from ._base_config import (
    BaseConfig,
)
from ._brotli_config import (
    BrotliConfig,
)
from ._bzip2_config import (
    BZip2Config,
)
from ._c_extension import (
    # Types and constants
    COMPRESSION_BROTLI,
    COMPRESSION_BZIP2,
    COMPRESSION_LZ4,
    COMPRESSION_LZ4HC,
    COMPRESSION_LZMA,
    COMPRESSION_LZMA2,
    COMPRESSION_NONE,
    COMPRESSION_TAMP,
    COMPRESSION_TUZ,
    COMPRESSION_XZ,
    COMPRESSION_ZLIB,
    COMPRESSION_ZSTD,
    CompressionType,
    # Exceptions
    HDiffPatchError,
    LiteCompressionType,
    # Core functions
    apply,
    apply_lite,
    diff,
    diff_lite,
    recompress,
    recompress_lite,
)
from ._lz4_config import (
    Lz4Config,
    Lz4HCConfig,
)
from ._lzma_config import (
    Lzma2Config,
    LzmaConfig,
)
from ._tamp_config import (
    TampConfig,
)
from ._tuz_config import (
    TuzConfig,
)
from ._xz_config import (
    XzConfig,
)
from ._zlib_config import (
    ZlibConfig,
    ZlibStrategy,
)
from ._zstd_config import (
    ZStdConfig,
)
