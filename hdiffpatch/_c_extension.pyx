"""HDiffPatch Cython extension for high-performance binary diff/patch operations."""

from typing import Union, Literal, TYPE_CHECKING, get_args

if TYPE_CHECKING:
    from ._base_config import BaseConfig
else:
    # Runtime imports needed for isinstance checks
    from ._base_config import BaseConfig
    from ._zlib_config import ZlibConfig
    from ._lzma_config import LzmaConfig, Lzma2Config
    from ._tamp_config import TampConfig
    from ._bzip2_config import BZip2Config
    from ._zstd_config import ZStdConfig
    from ._xz_config import XzConfig
    from ._lz4_config import Lz4Config, Lz4HCConfig
    from ._tuz_config import TuzConfig

from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc.stddef cimport size_t
from libcpp cimport bool as cpp_bool
from libcpp.vector cimport vector
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AsString, PyBytes_Size

# C++ -> Python exception translator.
#
# The HDiffPatch C++ core throws ``std::runtime_error`` (and, on OOM,
# ``std::bad_alloc``) from internal stream code. A bare ``except +`` would map
# these onto Python's builtin ``RuntimeError``/``MemoryError``, but the package
# contract is that every diff/patch/compression failure raises
# ``HDiffPatchError``. ``except +hdiffpatch_translate_exception`` on the extern
# C++ declarations below routes those throws through this handler instead:
# ``std::bad_alloc`` stays a ``MemoryError`` (never swallow OOM), everything
# else becomes ``HDiffPatchError`` carrying the original ``what()`` message.
# Cython calls the handler from inside the generated ``catch (...)`` block with
# the GIL held, so ``throw;`` re-raises the in-flight exception for inspection.
cdef extern from *:
    """
    #include <exception>
    #include <new>
    #include <Python.h>

    static PyObject* __hdiffpatch_error_type = NULL;

    static void hdiffpatch_register_error(PyObject* error_type) {
        __hdiffpatch_error_type = error_type;
    }

    static void hdiffpatch_translate_exception() {
        PyObject* error_type =
            __hdiffpatch_error_type ? __hdiffpatch_error_type : PyExc_RuntimeError;
        try {
            throw;
        } catch (const std::bad_alloc& exn) {
            PyErr_SetString(PyExc_MemoryError, exn.what());
        } catch (const std::exception& exn) {
            PyErr_SetString(error_type, exn.what());
        } catch (...) {
            PyErr_SetString(error_type, "Unknown C++ exception raised by HDiffPatch");
        }
    }
    """
    void hdiffpatch_register_error(object error_type)
    void hdiffpatch_translate_exception()

cdef extern from "libHDiffPatch/HPatch/patch_types.h":
    ctypedef unsigned long long hpatch_StreamPos_t
    ctypedef int hpatch_BOOL
    ctypedef struct hpatch_compressedDiffInfo:
        hpatch_StreamPos_t newDataSize
        hpatch_StreamPos_t oldDataSize
        unsigned int compressedCount
        char compressType[257]  # hpatch_kMaxPluginTypeLength+1

    hpatch_BOOL hpatch_unpackUInt(const unsigned char** src_code, const unsigned char* src_code_end,
                                 hpatch_StreamPos_t* result)


cdef extern from "libHDiffPatch/HDiff/diff_types.h":
    ctypedef struct hdiff_TCompress:
        pass

cdef extern from "libHDiffPatch/HDiff/diff.h":
    const int kMinSingleMatchScore_default
    void hdiff_create_compressed_diff "create_compressed_diff"(const unsigned char* newData, const unsigned char* newData_end,
                                                             const unsigned char* oldData, const unsigned char* oldData_end,
                                                             vector[unsigned char]& out_diff,
                                                             const hdiff_TCompress* compressPlugin,
                                                             int kMinSingleMatchScore,
                                                             cpp_bool isUseBigCacheMatch) except +hdiffpatch_translate_exception nogil

cdef extern from "libHDiffPatch/HPatch/patch_types.h":
    ctypedef struct hpatch_TDecompress:
        pass

cdef extern from "libHDiffPatch/HPatch/patch.h":
    int patch(unsigned char* out_newData, unsigned char* out_newData_end,
             const unsigned char* oldData, const unsigned char* oldData_end,
             const unsigned char* diff, const unsigned char* diff_end) nogil

    hpatch_BOOL getCompressedDiffInfo_mem(hpatch_compressedDiffInfo* out_diffInfo,
                                         const unsigned char* compressedDiff,
                                         const unsigned char* compressedDiff_end)

    hpatch_BOOL patch_decompress_mem(unsigned char* out_newData, unsigned char* out_newData_end,
                                     const unsigned char* oldData, const unsigned char* oldData_end,
                                     const unsigned char* compressedDiff, const unsigned char* compressedDiff_end,
                                     hpatch_TDecompress* decompressPlugin) nogil

    ctypedef struct hpatch_TCover:
        hpatch_StreamPos_t oldPos
        hpatch_StreamPos_t newPos
        hpatch_StreamPos_t length

    ctypedef struct hpatch_TCovers:
        hpatch_StreamPos_t (*leave_cover_count)(const hpatch_TCovers* covers)
        hpatch_BOOL (*read_cover)(hpatch_TCovers* covers, hpatch_TCover* out_cover)
        hpatch_BOOL (*is_finish)(const hpatch_TCovers* covers)
        hpatch_BOOL (*close)(hpatch_TCovers* covers)

    ctypedef struct hpatch_TCoverList:
        hpatch_TCovers* ICovers
        unsigned char _buf[4096]  # hpatch_kStreamCacheSize*4

    ctypedef struct hpatch_TStreamInput:
        void* streamImport
        hpatch_StreamPos_t streamSize
        hpatch_BOOL (*read)(const hpatch_TStreamInput* stream, hpatch_StreamPos_t readFromPos,
                           unsigned char* out_data, unsigned char* out_data_end)
        void* _private_reserved

    void hpatch_coverList_init(hpatch_TCoverList* coverList)
    hpatch_BOOL hpatch_coverList_open_serializedDiff(hpatch_TCoverList* out_coverList,
                                                     const hpatch_TStreamInput* serializedDiff)
    hpatch_BOOL hpatch_coverList_close(hpatch_TCoverList* coverList)

    const hpatch_TStreamInput* mem_as_hStreamInput(hpatch_TStreamInput* out_stream,
                                                   const unsigned char* mem, const unsigned char* mem_end)

    ctypedef struct hpatch_TStreamOutput:
        void* streamImport
        hpatch_StreamPos_t streamSize
        hpatch_BOOL (*write)(const hpatch_TStreamOutput* stream, hpatch_StreamPos_t writeToPos,
                           const unsigned char* data, const unsigned char* data_end)

    ctypedef struct hpatch_singleCompressedDiffInfo:
        hpatch_StreamPos_t newDataSize
        hpatch_StreamPos_t oldDataSize
        char compressType[257]  # hpatch_kMaxPluginTypeLength+1

    hpatch_BOOL getSingleCompressedDiffInfo_mem(hpatch_singleCompressedDiffInfo* out_diffInfo,
                                               const unsigned char* singleCompressedDiff,
                                               const unsigned char* singleCompressedDiff_end)

    const hpatch_TStreamOutput* mem_as_hStreamOutput(hpatch_TStreamOutput* out_stream,
                                                     unsigned char* mem, unsigned char* mem_end)

cdef extern from "libHDiffPatch/HDiff/diff.h":
    void resave_compressed_diff(const hpatch_TStreamInput* in_diff,
                               hpatch_TDecompress* decompressPlugin,
                               const hpatch_TStreamOutput* out_diff,
                               const hdiff_TCompress* compressPlugin,
                               hpatch_StreamPos_t out_diff_curPos) except +hdiffpatch_translate_exception nogil

    hpatch_StreamPos_t resave_single_compressed_diff(
        const hpatch_TStreamInput* in_diff,
        hpatch_TDecompress* decompressPlugin,
        const hpatch_TStreamOutput* out_diff,
        const hdiff_TCompress* compressPlugin,
        const hpatch_singleCompressedDiffInfo* diffInfo,
        hpatch_StreamPos_t in_diff_curPos,
        hpatch_StreamPos_t out_diff_curPos) except +hdiffpatch_translate_exception nogil

# Plain C++ vector-backed output stream (the one create_compressed_diff uses).
# Multithreaded encoders (lzma2, xz) call its write() from worker threads, so it
# must not touch Python objects.
cdef extern from "libHDiffPatch/HDiff/private_diff/limit_mem_diff/stream_serialize.h" namespace "hdiff_private":
    cppclass TVectorAsStreamOutput:
        TVectorAsStreamOutput(vector[unsigned char]& dst)

cdef extern from "compress_plugin_demo.h":
    extern const void* zlibCompressPlugin
    extern const void* lzmaCompressPlugin
    extern const void* lzma2CompressPlugin
    extern const void* zstdCompressPlugin
    extern const void* bz2CompressPlugin
    extern const void* _7zXZCompressPlugin
    # Builds the CRC32 table the xz container checks; must run before xz is used.
    int _init_CompressPlugin_7zXZ()
    extern const void* lz4CompressPlugin
    extern const void* lz4hcCompressPlugin
    extern const void* tuzCompressPlugin

cdef extern from "tamp_compress_plugin.cpp":
    extern const void* tampCompressPlugin
    extern const void* tampDecompressPlugin

# zlib strategy constants
cdef extern from "zlib.h":
    enum:
        Z_DEFAULT_STRATEGY
        Z_FILTERED
        Z_HUFFMAN_ONLY
        Z_RLE
        Z_FIXED

cdef extern from "decompress_plugin_demo.h":
    extern const void* zlibDecompressPlugin
    extern const void* lzmaDecompressPlugin
    extern const void* lzma2DecompressPlugin
    extern const void* zstdDecompressPlugin
    extern const void* bz2DecompressPlugin
    extern const void* _7zXZDecompressPlugin
    extern const void* lz4DecompressPlugin
    extern const void* tuzDecompressPlugin

# HPatchLite "lite"-format diff creator. hpi_byte is a typedef for
# ``unsigned char``, so ``vector[unsigned char]`` is the same C++ type as the
# ``std::vector<hpi_byte>&`` out-param the creator expects.
cdef extern from "libHDiffPatch/HPatchLite/hpatch_lite_types.h":
    ctypedef enum hpi_compressType:
        hpi_compressType_no
        hpi_compressType_tuz
        hpi_compressType_zlib
        hpi_compressType_lzma
        hpi_compressType_lzma2
        hpi_compressType_zstd
        hpi_compressType_bzip2
        hpi_compressType_lz4

cdef extern from "libHDiffPatch/HDiff/diff_for_hpatch_lite.h":
    ctypedef struct hdiffi_TCompress:
        const hdiff_TCompress* compress
        hpi_compressType       compress_type

    const int kLiteMatchScore_default
    # Trailing C++ default arguments (listener, threadNum) are omitted here so
    # the library defaults apply.
    void c_create_lite_diff "create_lite_diff"(const unsigned char* newData, const unsigned char* newData_end,
                                               const unsigned char* oldData, const unsigned char* oldData_end,
                                               vector[unsigned char]& out_lite_diff,
                                               const hdiffi_TCompress* compressPlugin,
                                               int kMinSingleMatchScore,
                                               cpp_bool isUseBigCacheMatch) except +hdiffpatch_translate_exception nogil

    cpp_bool c_check_lite_diff "check_lite_diff"(const unsigned char* newData, const unsigned char* newData_end,
                                                 const unsigned char* oldData, const unsigned char* oldData_end,
                                                 const unsigned char* lite_diff, const unsigned char* lite_diff_end,
                                                 hpatch_TDecompress* decompressPlugin) except +hdiffpatch_translate_exception nogil

    # Peeks the lite header to recover the self-describing compress-type byte
    # without applying the diff, so apply_lite can pick the matching decompressor.
    cpp_bool c_check_lite_diff_open "check_lite_diff_open"(const unsigned char* lite_diff, const unsigned char* lite_diff_end,
                                                           hpi_compressType* out_compress_type) except +hdiffpatch_translate_exception nogil

# Host-side lite applier shim (see apply_lite_shim.hpp). Mirrors the vendored
# check_lite_diff() wiring but writes the reconstruction into an output vector.
cdef extern from "apply_lite_shim.hpp" namespace "hdiffpatch_lite_shim":
    int c_apply_lite_diff "hdiffpatch_lite_shim::apply_lite_diff"(
        const unsigned char* oldData, const unsigned char* oldData_end,
        const unsigned char* lite_diff, const unsigned char* lite_diff_end,
        hpatch_TDecompress* decompressPlugin,
        hpi_compressType* out_compress_type,
        vector[unsigned char]& out_new) except +hdiffpatch_translate_exception nogil

# TCompressPlugin_zlib structure for custom zlib configuration
# Host-side lite recompressor shim (see recompress_lite_shim.hpp): re-encodes a
# lite diff's body with the same do_compress() + header layout diff_lite uses.
cdef extern from "recompress_lite_shim.hpp" namespace "hdiffpatch_lite_shim":
    int c_recompress_lite_diff "hdiffpatch_lite_shim::recompress_lite_diff"(
        const unsigned char* lite_diff, const unsigned char* lite_diff_end,
        hpatch_TDecompress* decompressPlugin,
        const hdiffi_TCompress* compressPlugin,
        vector[unsigned char]& out_diff) except +hdiffpatch_translate_exception nogil

cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_zlib:
        hdiff_TCompress base
        int             compress_level
        int             mem_level
        signed char     windowBits
        int             isNeedSaveWindowBits  # hpatch_BOOL
        int             strategy

# TCompressPlugin_lzma structure for custom LZMA configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_lzma:
        hdiff_TCompress base
        int             compress_level  # 0..9
        unsigned int    dict_size      # patch decompress need 4?*lzma_dictSize memory
        int             thread_num     # 1..2

# TCompressPlugin_lzma2 structure for custom LZMA2 configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_lzma2:
        hdiff_TCompress base
        int             compress_level  # 0..9
        unsigned int    dict_size      # patch decompress need 4?*lzma_dictSize memory
        int             thread_num     # 1..64

# TCompressPlugin_tamp structure for custom TAMP configuration
cdef extern from "tamp_compress_plugin.cpp":
    ctypedef struct TCompressPlugin_tamp:
        hdiff_TCompress base
        int             window         # 8..15
        int             literal        # 5..8 (fixed at 8)
        int             use_custom_dictionary  # 0 or 1
        int             extended       # 0 or 1
        int             lazy_matching  # 0 or 1

# TCompressPlugin_bz2 structure for custom bzip2 configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_bz2:
        hdiff_TCompress base
        int             compress_level  # 0..9

# TCompressPlugin_zstd structure for custom zstd configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_zstd:
        hdiff_TCompress base
        int             compress_level  # 0..22
        int             dict_bits       # 10..(30 or 31)
        int             thread_num      # 1..(200?)

# TCompressPlugin_7zXZ structure for custom xz configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_7zXZ:
        hdiff_TCompress base
        int             compress_level  # 0..9
        unsigned int    dict_size
        int             thread_num      # 1..64
# TCompressPlugin_lz4 / TCompressPlugin_lz4hc structures for custom LZ4 configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct TCompressPlugin_lz4:
        hdiff_TCompress base
        int             compress_level  # 1..50 (maps to LZ4 acceleration 50..1)

    ctypedef struct TCompressPlugin_lz4hc:
        hdiff_TCompress base
        int             compress_level  # 3..12
# TCompressPlugin_tuz structure for custom tinyuz configuration
cdef extern from "compress_plugin_demo.h":
    ctypedef struct tuz_TCompressProps:
        size_t   dictSize        # 1..2**30
        size_t   maxSaveLength   # 127..65535
        size_t   threadNum
        cpp_bool isNeedLiteralLine

    ctypedef struct TCompressPlugin_tuz:
        hdiff_TCompress    base
        tuz_TCompressProps props

# Type aliases for compression parameters
CompressionType = Literal["none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp", "xz", "lz4", "lz4hc", "tuz"]
# The subset of CompressionType that has a lite compress-type byte.
LiteCompressionType = Literal["none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp", "lz4", "lz4hc", "tuz"]

# Constants for convenience
COMPRESSION_NONE = "none"
COMPRESSION_ZLIB = "zlib"
COMPRESSION_LZMA = "lzma"
COMPRESSION_LZMA2 = "lzma2"
COMPRESSION_ZSTD = "zstd"
COMPRESSION_BZIP2 = "bzip2"
COMPRESSION_TAMP = "tamp"
COMPRESSION_XZ = "xz"
COMPRESSION_LZ4 = "lz4"
COMPRESSION_LZ4HC = "lz4hc"
COMPRESSION_TUZ = "tuz"


_valid_compression_types = {"none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp", "xz", "lz4", "lz4hc", "tuz"}

# Codecs that have a compress-type byte in the "lite" diff header: every
# upstream ``hpi_compressType`` value this build can encode, plus tamp's
# vendor-specific byte. ``hpatch_lite_patch`` does no decompression itself, so
# which of these a device can apply depends on the decoders it links.
_lite_supported_compression_types = set(get_args(LiteCompressionType))

# tamp has no upstream ``hpi_compressType`` enum value. This vendor-specific tag
# is written into the lite-diff header and must match whatever the device-side
# tamp decompressor plugin looks for. ``hpatch_lite_open`` treats the byte as
# opaque, so it does not affect round-trip validation through ``check_lite_diff``.
_HPI_COMPRESS_TYPE_TAMP = 0xF0


class HDiffPatchError(Exception):
    """Base exception for HDiffPatch operations."""


_init_CompressPlugin_7zXZ()

# Hand the exception type to the C++ translator so C++ throws from the core
# surface as HDiffPatchError. The translator holds a borrowed reference; the
# class lives for the lifetime of the module, so no incref is required.
hdiffpatch_register_error(HDiffPatchError)


cdef const hdiff_TCompress* get_compress_plugin(str compression):
    """Get compression plugin by name.

    Parameters
    ----------
    compression : str
        The compression type name

    Returns
    -------
    const hdiff_TCompress*
        Pointer to compression plugin or NULL if not found
    """
    if compression == COMPRESSION_ZLIB:
        return <const hdiff_TCompress*>&zlibCompressPlugin
    elif compression == COMPRESSION_LZMA:
        return <const hdiff_TCompress*>&lzmaCompressPlugin
    elif compression == COMPRESSION_LZMA2:
        return <const hdiff_TCompress*>&lzma2CompressPlugin
    elif compression == COMPRESSION_ZSTD:
        return <const hdiff_TCompress*>&zstdCompressPlugin
    elif compression == COMPRESSION_BZIP2:
        return <const hdiff_TCompress*>&bz2CompressPlugin
    elif compression == COMPRESSION_TAMP:
        return <const hdiff_TCompress*>&tampCompressPlugin
    elif compression == COMPRESSION_XZ:
        return <const hdiff_TCompress*>&_7zXZCompressPlugin
    elif compression == COMPRESSION_LZ4:
        return <const hdiff_TCompress*>&lz4CompressPlugin
    elif compression == COMPRESSION_LZ4HC:
        return <const hdiff_TCompress*>&lz4hcCompressPlugin
    elif compression == COMPRESSION_TUZ:
        return <const hdiff_TCompress*>&tuzCompressPlugin
    else:
        return NULL


cdef const hpatch_TDecompress* get_decompress_plugin(str compression):
    """Get decompression plugin by name.

    Parameters
    ----------
    compression : str
        The compression type name

    Returns
    -------
    const hpatch_TDecompress*
        Pointer to decompression plugin or NULL if not found
    """
    if compression == COMPRESSION_ZLIB:
        return <const hpatch_TDecompress*>&zlibDecompressPlugin
    elif compression == COMPRESSION_LZMA:
        return <const hpatch_TDecompress*>&lzmaDecompressPlugin
    elif compression == COMPRESSION_LZMA2:
        return <const hpatch_TDecompress*>&lzma2DecompressPlugin
    elif compression == COMPRESSION_ZSTD:
        return <const hpatch_TDecompress*>&zstdDecompressPlugin
    elif compression == COMPRESSION_BZIP2 or compression == "bz2":
        return <const hpatch_TDecompress*>&bz2DecompressPlugin
    elif compression == COMPRESSION_TAMP:
        return <const hpatch_TDecompress*>&tampDecompressPlugin
    elif compression == COMPRESSION_XZ or compression == "7zXZ":
        return <const hpatch_TDecompress*>&_7zXZDecompressPlugin
    elif compression == COMPRESSION_LZ4 or compression == COMPRESSION_LZ4HC:
        return <const hpatch_TDecompress*>&lz4DecompressPlugin
    elif compression == COMPRESSION_TUZ:
        return <const hpatch_TDecompress*>&tuzDecompressPlugin
    else:
        return NULL


cdef TCompressPlugin_zlib* create_custom_zlib_plugin(zlib_config) except NULL:
    """Create a custom zlib plugin instance with configuration.

    Parameters
    ----------
    zlib_config : ZlibConfig
        The zlib configuration object

    Returns
    -------
    TCompressPlugin_zlib*
        Pointer to configured zlib plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    ValueError
        If configuration is invalid
    """
    cdef TCompressPlugin_zlib* custom_plugin = <TCompressPlugin_zlib*>malloc(sizeof(TCompressPlugin_zlib))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom zlib plugin")

    # Copy the base zlib plugin
    cdef TCompressPlugin_zlib* base_plugin = <TCompressPlugin_zlib*>&zlibCompressPlugin
    custom_plugin[0] = base_plugin[0]

    # Set custom parameters
    custom_plugin.compress_level = zlib_config.level
    custom_plugin.mem_level = zlib_config.memory_level
    custom_plugin.windowBits = <signed char>(-zlib_config.window)  # Negative for raw deflate
    custom_plugin.isNeedSaveWindowBits = 1 if zlib_config.save_window_bits else 0

    # Map strategy enum to zlib constants
    strategy_value = zlib_config.strategy.value
    if strategy_value == "default":
        custom_plugin.strategy = Z_DEFAULT_STRATEGY
    elif strategy_value == "filtered":
        custom_plugin.strategy = Z_FILTERED
    elif strategy_value == "huffman_only":
        custom_plugin.strategy = Z_HUFFMAN_ONLY
    elif strategy_value == "rle":
        custom_plugin.strategy = Z_RLE
    elif strategy_value == "fixed":
        custom_plugin.strategy = Z_FIXED
    else:
        free(custom_plugin)
        raise ValueError(f"Unknown compression strategy: {strategy_value}")

    return custom_plugin


cdef TCompressPlugin_lzma* create_custom_lzma_plugin(lzma_config) except NULL:
    """Create a custom LZMA plugin instance with configuration.

    Parameters
    ----------
    lzma_config : LzmaConfig
        The LZMA configuration object

    Returns
    -------
    TCompressPlugin_lzma*
        Pointer to configured LZMA plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_lzma* custom_plugin = <TCompressPlugin_lzma*>malloc(sizeof(TCompressPlugin_lzma))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom LZMA plugin")

    # Copy the base LZMA plugin
    cdef const TCompressPlugin_lzma* base_plugin = <const TCompressPlugin_lzma*>&lzmaCompressPlugin
    custom_plugin[0] = base_plugin[0]

    # Set custom parameters
    custom_plugin.compress_level = lzma_config.level
    custom_plugin.dict_size = <unsigned int>(1 << lzma_config.window)
    custom_plugin.thread_num = lzma_config.threads

    return custom_plugin


cdef TCompressPlugin_tamp* create_custom_tamp_plugin(tamp_config) except NULL:
    """Create a custom tamp plugin instance with configuration.

    Parameters
    ----------
    tamp_config : TampConfig
        The tamp configuration object

    Returns
    -------
    TCompressPlugin_tamp*
        Pointer to configured tamp plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_tamp* custom_plugin = <TCompressPlugin_tamp*>malloc(sizeof(TCompressPlugin_tamp))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom tamp plugin")

    # Copy the base tamp plugin
    cdef const TCompressPlugin_tamp* base_plugin = <const TCompressPlugin_tamp*>&tampCompressPlugin
    custom_plugin[0] = base_plugin[0]

    # Set custom parameters
    custom_plugin.window = tamp_config.window
    custom_plugin.literal = 8  # Fixed at 8
    custom_plugin.use_custom_dictionary = 0
    custom_plugin.extended = 1 if tamp_config.extended else 0
    custom_plugin.lazy_matching = 1 if tamp_config.lazy_matching else 0

    return custom_plugin

cdef TCompressPlugin_lzma2* create_custom_lzma2_plugin(lzma2_config) except NULL:
    """Create a custom LZMA2 plugin instance with configuration.

    Parameters
    ----------
    lzma2_config : Lzma2Config
        The LZMA2 configuration object

    Returns
    -------
    TCompressPlugin_lzma2*
        Pointer to configured LZMA2 plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_lzma2* custom_plugin = <TCompressPlugin_lzma2*>malloc(sizeof(TCompressPlugin_lzma2))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom LZMA2 plugin")

    # Copy the base LZMA2 plugin
    cdef const TCompressPlugin_lzma2* base_plugin = <const TCompressPlugin_lzma2*>&lzma2CompressPlugin
    custom_plugin[0] = base_plugin[0]

    # Set custom parameters
    custom_plugin.compress_level = lzma2_config.level
    custom_plugin.dict_size = <unsigned int>(1 << lzma2_config.window)
    custom_plugin.thread_num = lzma2_config.threads

    return custom_plugin

cdef TCompressPlugin_bz2* create_custom_bzip2_plugin(bzip2_config) except NULL:
    """Create a custom bzip2 plugin instance with configuration.

    Parameters
    ----------
    bzip2_config : BZip2Config
        The bzip2 configuration object

    Returns
    -------
    TCompressPlugin_bz2*
        Pointer to configured bzip2 plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_bz2* custom_plugin = <TCompressPlugin_bz2*>malloc(sizeof(TCompressPlugin_bz2))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom bzip2 plugin")

    # Copy the base bzip2 plugin
    cdef const TCompressPlugin_bz2* base_plugin = <const TCompressPlugin_bz2*>&bz2CompressPlugin
    custom_plugin[0] = base_plugin[0]

    # Set custom parameters
    custom_plugin.compress_level = bzip2_config.level

    return custom_plugin

cdef TCompressPlugin_zstd* create_custom_zstd_plugin(zstd_config) except NULL:
    """Create a custom zstd plugin instance with configuration.

    Parameters
    ----------
    zstd_config : ZStdConfig
        The zstd configuration object

    Returns
    -------
    TCompressPlugin_zstd*
        Pointer to configured zstd plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_zstd* custom_plugin = <TCompressPlugin_zstd*>malloc(sizeof(TCompressPlugin_zstd))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom zstd plugin")

    # Copy the base zstd plugin
    cdef const TCompressPlugin_zstd* base_plugin = <const TCompressPlugin_zstd*>&zstdCompressPlugin
    custom_plugin[0] = base_plugin[0]

    # Set custom parameters
    custom_plugin.compress_level = zstd_config.level
    custom_plugin.thread_num = zstd_config.threads

    # Convert window to dict_bits if specified, otherwise use default
    if zstd_config.window is not None:
        custom_plugin.dict_bits = zstd_config.window
    # Note: other advanced parameters like hash_log, chain_log, etc. are not directly
    # supported by the HDiffPatch zstd plugin structure, so we only use the main ones

    return custom_plugin

cdef TCompressPlugin_7zXZ* create_custom_xz_plugin(xz_config) except NULL:
    """Create a custom xz plugin instance with configuration.

    Parameters
    ----------
    xz_config : XzConfig
        The xz configuration object

    Returns
    -------
    TCompressPlugin_7zXZ*
        Pointer to configured xz plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_7zXZ* custom_plugin = <TCompressPlugin_7zXZ*>malloc(sizeof(TCompressPlugin_7zXZ))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom xz plugin")

    cdef const TCompressPlugin_7zXZ* base_plugin = <const TCompressPlugin_7zXZ*>&_7zXZCompressPlugin
    custom_plugin[0] = base_plugin[0]

    custom_plugin.compress_level = xz_config.level
    custom_plugin.dict_size = <unsigned int>(1 << xz_config.window)
    custom_plugin.thread_num = xz_config.threads

    return custom_plugin

cdef TCompressPlugin_lz4* create_custom_lz4_plugin(lz4_config) except NULL:
    """Create a custom LZ4 plugin instance with configuration.

    Parameters
    ----------
    lz4_config : Lz4Config
        The LZ4 configuration object

    Returns
    -------
    TCompressPlugin_lz4*
        Pointer to configured LZ4 plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_lz4* custom_plugin = <TCompressPlugin_lz4*>malloc(sizeof(TCompressPlugin_lz4))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom LZ4 plugin")

    cdef const TCompressPlugin_lz4* base_plugin = <const TCompressPlugin_lz4*>&lz4CompressPlugin
    custom_plugin[0] = base_plugin[0]
    custom_plugin.compress_level = lz4_config.level

    return custom_plugin

cdef TCompressPlugin_lz4hc* create_custom_lz4hc_plugin(lz4hc_config) except NULL:
    """Create a custom LZ4HC plugin instance with configuration.

    Parameters
    ----------
    lz4hc_config : Lz4HCConfig
        The LZ4HC configuration object

    Returns
    -------
    TCompressPlugin_lz4hc*
        Pointer to configured LZ4HC plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_lz4hc* custom_plugin = <TCompressPlugin_lz4hc*>malloc(sizeof(TCompressPlugin_lz4hc))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom LZ4HC plugin")

    cdef const TCompressPlugin_lz4hc* base_plugin = <const TCompressPlugin_lz4hc*>&lz4hcCompressPlugin
    custom_plugin[0] = base_plugin[0]
    custom_plugin.compress_level = lz4hc_config.level

    return custom_plugin

cdef TCompressPlugin_tuz* create_custom_tuz_plugin(tuz_config) except NULL:
    """Create a custom tinyuz plugin instance with configuration.

    Parameters
    ----------
    tuz_config : TuzConfig
        The tinyuz configuration object

    Returns
    -------
    TCompressPlugin_tuz*
        Pointer to configured tinyuz plugin

    Raises
    ------
    MemoryError
        If memory allocation fails
    """
    cdef TCompressPlugin_tuz* custom_plugin = <TCompressPlugin_tuz*>malloc(sizeof(TCompressPlugin_tuz))
    if custom_plugin == NULL:
        raise MemoryError("Failed to allocate memory for custom tinyuz plugin")

    cdef const TCompressPlugin_tuz* base_plugin = <const TCompressPlugin_tuz*>&tuzCompressPlugin
    custom_plugin[0] = base_plugin[0]

    custom_plugin.props.dictSize = tuz_config.dict_size
    custom_plugin.props.maxSaveLength = tuz_config.max_save_length
    custom_plugin.props.threadNum = tuz_config.threads
    custom_plugin.props.isNeedLiteralLine = tuz_config.literal_line

    return custom_plugin

cdef hpatch_StreamPos_t calculate_new_data_size(const unsigned char* diff_ptr, const unsigned char* diff_end) except -1:
    """Calculate the new data size from an uncompressed diff by examining covers.

    Parameters
    ----------
    diff_ptr : const unsigned char*
        Pointer to start of diff data
    diff_end : const unsigned char*
        Pointer to end of diff data

    Returns
    -------
    hpatch_StreamPos_t
        The calculated new data size

    Raises
    ------
    HDiffPatchError
        If the size cannot be determined
    """
    cdef hpatch_TStreamInput diff_stream
    cdef hpatch_TCoverList cover_list
    cdef hpatch_TCover cover
    cdef hpatch_StreamPos_t max_new_end = 0
    cdef hpatch_StreamPos_t current_new_end
    cdef hpatch_StreamPos_t cover_count
    cdef const unsigned char* pos
    cdef hpatch_StreamPos_t coverCount, lengthSize, inc_newPosSize, inc_oldPosSize, newDataDiffSize
    cdef hpatch_StreamPos_t newPosBack = 0
    cdef hpatch_StreamPos_t newDataDiff_used = 0
    cdef hpatch_StreamPos_t remaining_newDataDiff
    cdef hpatch_StreamPos_t total_size

    # Initialize cover list
    hpatch_coverList_init(&cover_list)

    # Create stream input from diff data
    mem_as_hStreamInput(&diff_stream, diff_ptr, diff_end)

    # Open cover list from serialized diff
    if not hpatch_coverList_open_serializedDiff(&cover_list, &diff_stream):
        hpatch_coverList_close(&cover_list)
        raise HDiffPatchError("Failed to open cover list from diff data")

    # Check if there are any covers
    cover_count = cover_list.ICovers.leave_cover_count(cover_list.ICovers)

    # Parse the diff header manually to get newDataDiffSize
    # Format: coverCount, lengthSize, inc_newPosSize, inc_oldPosSize, newDataDiffSize
    pos = diff_ptr

    # Skip coverCount
    if not hpatch_unpackUInt(&pos, diff_end, &coverCount):
        hpatch_coverList_close(&cover_list)
        raise HDiffPatchError("Failed to read coverCount from diff header")

    # Skip lengthSize
    if not hpatch_unpackUInt(&pos, diff_end, &lengthSize):
        hpatch_coverList_close(&cover_list)
        raise HDiffPatchError("Failed to read lengthSize from diff header")

    # Skip inc_newPosSize
    if not hpatch_unpackUInt(&pos, diff_end, &inc_newPosSize):
        hpatch_coverList_close(&cover_list)
        raise HDiffPatchError("Failed to read inc_newPosSize from diff header")

    # Skip inc_oldPosSize
    if not hpatch_unpackUInt(&pos, diff_end, &inc_oldPosSize):
        hpatch_coverList_close(&cover_list)
        raise HDiffPatchError("Failed to read inc_oldPosSize from diff header")

    # Get newDataDiffSize
    if not hpatch_unpackUInt(&pos, diff_end, &newDataDiffSize):
        hpatch_coverList_close(&cover_list)
        raise HDiffPatchError("Failed to read newDataDiffSize from diff header")

    if cover_count == 0:
        # When there are no covers, the new data size is just the newDataDiffSize
        hpatch_coverList_close(&cover_list)
        return newDataDiffSize
    else:
        # Process all covers to properly simulate the patching process
        newPosBack = 0
        newDataDiff_used = 0

        while cover_list.ICovers.leave_cover_count(cover_list.ICovers) > 0:
            if not cover_list.ICovers.read_cover(cover_list.ICovers, &cover):
                break

            # Based on the patchByClip function, for each cover:
            # 1. Copy (cover.newPos - newPosBack) bytes from newDataDiff
            # 2. Copy cover.length bytes from old data
            # 3. newPosBack = cover.newPos + cover.length

            # Calculate how much newDataDiff is used for this cover
            if cover.newPos > newPosBack:
                newDataDiff_used += cover.newPos - newPosBack

            # Update newPosBack to the position after this cover
            newPosBack = cover.newPos + cover.length

        # Close cover list
        hpatch_coverList_close(&cover_list)

        # After processing all covers, the total new data size is:
        # newPosBack + remaining newDataDiff data
        # (operands are unsigned; guard before subtracting so a malformed diff
        # can't wrap around to a huge value)
        if newDataDiff_used > newDataDiffSize:
            remaining_newDataDiff = 0
        else:
            remaining_newDataDiff = newDataDiffSize - newDataDiff_used

        total_size = newPosBack + remaining_newDataDiff

        return total_size


cdef class CompressionPlugin:
    """Container for compression plugin and cleanup information."""
    cdef const hdiff_TCompress* plugin
    cdef void* custom_plugin_ptr
    cdef str plugin_type

    def __cinit__(self):
        self.plugin = NULL
        self.custom_plugin_ptr = NULL
        self.plugin_type = ""

    cdef void set_plugin(self, const hdiff_TCompress* plugin, void* custom_plugin_ptr, str plugin_type):
        """Set the plugin parameters (C-only method).

        Parameters
        ----------
        plugin : const hdiff_TCompress*
            Pointer to compression plugin
        custom_plugin_ptr : void*
            Pointer to custom plugin memory
        plugin_type : str
            Type description of the plugin
        """
        self.plugin = plugin
        self.custom_plugin_ptr = custom_plugin_ptr
        self.plugin_type = plugin_type

    def __dealloc__(self):
        """Clean up custom plugin memory if needed."""
        if self.custom_plugin_ptr != NULL:
            free(self.custom_plugin_ptr)


cdef CompressionPlugin _resolve_compression_to_plugin(compression: Union[CompressionType, None, 'BaseConfig']):
    """Resolve compression parameter to plugin object.

    Parameters
    ----------
    compression : CompressionType, BaseConfig, or None
        The compression parameter from diff function

    Returns
    -------
    CompressionPlugin or None
        CompressionPlugin object containing plugin pointer and cleanup info,
        or None if no compression should be applied

    Raises
    ------
    ValueError
        If compression type is invalid
    HDiffPatchError
        If no plugin found for compression type
    """
    cdef const hdiff_TCompress* compress_plugin = NULL
    cdef void* custom_plugin_ptr = NULL
    cdef str plugin_type = ""

    if compression is None:
        return None
    elif isinstance(compression, ZlibConfig):
        custom_plugin_ptr = <void*>create_custom_zlib_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "zlib_config"
    elif isinstance(compression, Lzma2Config):
        custom_plugin_ptr = <void*>create_custom_lzma2_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "lzma2_config"
    elif isinstance(compression, LzmaConfig):
        custom_plugin_ptr = <void*>create_custom_lzma_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "lzma_config"
    elif isinstance(compression, TampConfig):
        # This is a TampConfig object - create custom TAMP plugin
        custom_plugin_ptr = <void*>create_custom_tamp_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "tamp_config"
    elif isinstance(compression, BZip2Config):
        # This is a BZip2Config object - create custom bzip2 plugin
        custom_plugin_ptr = <void*>create_custom_bzip2_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "bzip2_config"
    elif isinstance(compression, ZStdConfig):
        # This is a ZStdConfig object - create custom zstd plugin
        custom_plugin_ptr = <void*>create_custom_zstd_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "zstd_config"
    elif isinstance(compression, XzConfig):
        custom_plugin_ptr = <void*>create_custom_xz_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "xz_config"
    elif isinstance(compression, Lz4Config):
        custom_plugin_ptr = <void*>create_custom_lz4_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "lz4_config"
    elif isinstance(compression, Lz4HCConfig):
        custom_plugin_ptr = <void*>create_custom_lz4hc_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "lz4hc_config"
    elif isinstance(compression, TuzConfig):
        custom_plugin_ptr = <void*>create_custom_tuz_plugin(compression)
        compress_plugin = <const hdiff_TCompress*>custom_plugin_ptr
        plugin_type = "tuz_config"
    else:
        # String-based compression - normalize and validate
        compression_str = str(compression).lower()
        if compression_str not in _valid_compression_types:
            raise ValueError(f"Invalid compression type: {compression_str}. Valid options: {', '.join(sorted(_valid_compression_types))}")

        if compression_str == COMPRESSION_NONE:
            return None

        compress_plugin = get_compress_plugin(compression_str)
        if compress_plugin == NULL:
            raise HDiffPatchError(f"No compression plugin found for type: {compression_str}")
        plugin_type = f"builtin_{compression_str}"

    cdef CompressionPlugin plugin_obj = CompressionPlugin()
    plugin_obj.set_plugin(compress_plugin, custom_plugin_ptr, plugin_type)
    return plugin_obj


def diff(
    old_data: bytes,
    new_data: bytes,
    compression: Union[CompressionType, 'BaseConfig', None] = None,
    *,
    validate: bool = True,
    big_cache_match: bool = False,
) -> bytes:
    """Create a binary diff between old and new data using HDiffPatch.

    Parameters
    ----------
    old_data : bytes
        The original data
    new_data : bytes
        The new data to diff against
    compression : CompressionType, BaseConfig, or None, default=None
        Compression algorithm to use
    validate : bool, default=True
        If True, validates that applying the diff to old_data produces new_data
    big_cache_match : bool, default=False
        If True, builds an extra match cache over ``old_data`` (a bloom filter of
        roughly 0.5-1 byte per byte of ``old_data``) so candidate matches are
        rejected without a suffix-array search. Diff creation gets faster and
        the output is byte-identical; see the Performance docs for measurements
        and trade-offs.

    Returns
    -------
    bytes
        The diff data as bytes

    Raises
    ------
    TypeError
        If old_data or new_data are not bytes
    HDiffPatchError
        If diff creation fails or roundtrip validation fails
    """
    if not isinstance(old_data, bytes) or not isinstance(new_data, bytes):
        raise TypeError("old_data and new_data must be bytes")

    cdef const unsigned char* old_ptr = <const unsigned char*>PyBytes_AsString(old_data)
    cdef const unsigned char* new_ptr = <const unsigned char*>PyBytes_AsString(new_data)
    cdef const unsigned char* old_end = old_ptr + PyBytes_Size(old_data)
    cdef const unsigned char* new_end = new_ptr + PyBytes_Size(new_data)
    cdef vector[unsigned char] diff_vector
    cdef size_t diff_size

    compression_plugin = _resolve_compression_to_plugin(compression)

    # NULL plugin means no compression - HDIFF13& header format
    cdef const hdiff_TCompress* compress_plugin_ptr = <hdiff_TCompress*>0
    cdef cpp_bool use_big_cache = big_cache_match
    if compression_plugin is not None:
        compress_plugin_ptr = compression_plugin.plugin

    with nogil:
        hdiff_create_compressed_diff(new_ptr, new_end, old_ptr, old_end, diff_vector, compress_plugin_ptr,
                                     kMinSingleMatchScore_default, use_big_cache)

    diff_size = diff_vector.size()
    if diff_size == 0:
        raise HDiffPatchError("HDiffPatch created empty diff")

    diff_bytes = PyBytes_FromStringAndSize(<char*>diff_vector.data(), diff_size)

    if validate:
        try:
            result_data = apply(old_data, diff_bytes)
        except Exception as e:
            raise HDiffPatchError(f"Roundtrip validation failed: {str(e)}") from e
        if result_data != new_data:
            raise HDiffPatchError("Roundtrip validation failed: applying the diff to old_data does not produce new_data")

    return diff_bytes


def apply(
    old_data: bytes,
    diff_data: bytes
) -> bytes:
    """Apply a patch to old data to produce new data using HDiffPatch.

    The compression type is automatically detected from the diff data header.

    Parameters
    ----------
    old_data : bytes
        The original data
    diff_data : bytes
        The diff/patch data

    Returns
    -------
    bytes
        The patched data as bytes

    Raises
    ------
    TypeError
        If old_data or diff_data are not bytes
    HDiffPatchError
        If patch application fails
    MemoryError
        If memory allocation fails
    """
    if not isinstance(old_data, bytes) or not isinstance(diff_data, bytes):
        raise TypeError("old_data and diff_data must be bytes")

    cdef const unsigned char* old_ptr = <const unsigned char*>PyBytes_AsString(old_data)
    cdef const unsigned char* old_end = old_ptr + PyBytes_Size(old_data)
    cdef const unsigned char* diff_ptr = <const unsigned char*>PyBytes_AsString(diff_data)
    cdef const unsigned char* diff_end = diff_ptr + PyBytes_Size(diff_data)
    cdef unsigned char* new_ptr = NULL
    cdef unsigned char* new_end
    cdef int result
    cdef hpatch_compressedDiffInfo diff_info
    cdef hpatch_StreamPos_t new_size

    try:
        # Check if this is a compressed diff by trying to extract info
        if getCompressedDiffInfo_mem(&diff_info, diff_ptr, diff_end):
            # This is a compressed diff - extract new data size and compression type
            new_size = diff_info.newDataSize
            compression_type = diff_info.compressType.decode('ascii')
            if len(compression_type) > 0:
                decompress_plugin = <hpatch_TDecompress*>get_decompress_plugin(compression_type)
                if decompress_plugin == NULL:
                    raise HDiffPatchError(f"No decompression plugin available for type: {compression_type}")
            else:
                # Empty compression type means no compression (uncompressed format)
                decompress_plugin = NULL

            new_ptr = <unsigned char*>malloc(new_size)
            if new_ptr == NULL:
                raise MemoryError("Failed to allocate memory for patched data")

            new_end = new_ptr + new_size

            with nogil:
                result = patch_decompress_mem(new_ptr, new_end, old_ptr, old_end,
                                              diff_ptr, diff_end, <hpatch_TDecompress*>decompress_plugin)
        else:
            # This is an uncompressed diff - calculate the new data size from covers
            new_size = calculate_new_data_size(diff_ptr, diff_end)

            # Apply the patch with the calculated size
            if new_size == 0:
                new_ptr = NULL
                new_end = NULL
            else:
                new_ptr = <unsigned char*>malloc(new_size)
                if new_ptr == NULL:
                    raise MemoryError("Failed to allocate memory for patched data")
                new_end = new_ptr + new_size

            with nogil:
                result = patch(new_ptr, new_end, old_ptr, old_end, diff_ptr, diff_end)

        if result == 0:
            raise HDiffPatchError("HDiffPatch patch operation failed")

        # Create Python bytes object with the result
        result_bytes = PyBytes_FromStringAndSize(<char*>new_ptr, new_size)

        if new_ptr != NULL:
            free(new_ptr)
        return result_bytes
    except (HDiffPatchError, MemoryError):
        if new_ptr != NULL:
            free(new_ptr)
        raise
    except Exception as e:
        if new_ptr != NULL:
            free(new_ptr)
        raise HDiffPatchError(f"Patch application failed: {str(e)}") from e


def recompress(
    diff_data: bytes,
    compression: Union[CompressionType, 'BaseConfig', None]
) -> bytes:
    """Recompress a diff with a different compression algorithm.

    This function can recompress diffs in HDiffPatch's compressed diff format, which includes
    diffs created by hdiffz (both compressed and uncompressed). The input format is automatically
    detected and the diff is recompressed with the specified compression algorithm.

    Supports both single-compressed and regular compressed diff formats. Works with diffs
    created by hdiffz tool and the hdiffpatch.diff() function when explicit compression is used.

    Parameters
    ----------
    diff_data : bytes
        The diff data to recompress
    compression : CompressionType, BaseConfig, or None
        Target compression algorithm to use. Pass ``"none"`` (or ``None``)
        to strip compression from the diff.

    Returns
    -------
    bytes
        The recompressed diff data

    Raises
    ------
    TypeError
        If diff_data is not bytes
    HDiffPatchError
        If recompression fails or input format is unsupported
    ValueError
        If compression type is invalid
    """
    if not isinstance(diff_data, bytes):
        raise TypeError("diff_data must be bytes")

    cdef const unsigned char* diff_ptr = <const unsigned char*>PyBytes_AsString(diff_data)
    cdef const unsigned char* diff_end = diff_ptr + PyBytes_Size(diff_data)
    cdef hpatch_singleCompressedDiffInfo singleDiffInfo
    cdef hpatch_compressedDiffInfo diff_info
    cdef hpatch_TDecompress* decompress_plugin = NULL
    cdef bint is_single_diff = False
    cdef str input_compression_type = ""

    # Input stream setup
    cdef hpatch_TStreamInput input_stream
    mem_as_hStreamInput(&input_stream, diff_ptr, diff_end)

    # Detect diff format and determine decompression plugin
    try:
        if getSingleCompressedDiffInfo_mem(&singleDiffInfo, diff_ptr, diff_end):
            # Single compressed diff format
            is_single_diff = True
            if len(singleDiffInfo.compressType) > 0:
                input_compression_type = singleDiffInfo.compressType.decode('ascii')
                decompress_plugin = <hpatch_TDecompress*>get_decompress_plugin(input_compression_type)
                if decompress_plugin == NULL:
                    raise HDiffPatchError(f"No decompression plugin available for input type: {input_compression_type}")
            # else: single format with no compression, decompress_plugin stays NULL

        elif getCompressedDiffInfo_mem(&diff_info, diff_ptr, diff_end):
            # Regular compressed diff format (may or may not be actually compressed)
            if diff_info.compressedCount > 0:
                input_compression_type = diff_info.compressType.decode('ascii')
                if len(input_compression_type) > 0:
                    decompress_plugin = <hpatch_TDecompress*>get_decompress_plugin(input_compression_type)
                    if decompress_plugin == NULL:
                        raise HDiffPatchError(f"No decompression plugin available for input type: {input_compression_type}")
                # else: compressed format with empty compression type, decompress_plugin stays NULL
            # else: compressed format with no compression, decompress_plugin stays NULL

        else:
            # Original uncompressed diff format (the very old format that lacks compressed headers)
            # This should be rare since hdiffz creates compressed format even for uncompressed data
            raise HDiffPatchError(
                "Cannot recompress legacy uncompressed diff format. "
                "The input diff appears to be in the original HDiffPatch format that predates "
                "the compressed diff framework. Modern tools like hdiffz create compressed-format "
                "diffs even when no compression is applied, which are supported by this function."
            )

    except HDiffPatchError:
        raise
    except Exception as e:
        raise HDiffPatchError(f"Failed to detect diff format: {str(e)}") from e

    # Resolve output compression plugin
    compression_plugin = _resolve_compression_to_plugin(compression)
    cdef const hdiff_TCompress* compress_plugin_ptr = NULL
    if compression_plugin is not None:
        compress_plugin_ptr = compression_plugin.plugin

    cdef vector[unsigned char] out_vector
    cdef TVectorAsStreamOutput* out_stream = new TVectorAsStreamOutput(out_vector)
    cdef const hpatch_TStreamOutput* out_stream_ptr = <const hpatch_TStreamOutput*>out_stream

    try:
        with nogil:
            if is_single_diff:
                resave_single_compressed_diff(
                    &input_stream,
                    decompress_plugin,
                    out_stream_ptr,
                    compress_plugin_ptr,
                    &singleDiffInfo,
                    0,  # in_diff_curPos
                    0   # out_diff_curPos
                )
            else:
                resave_compressed_diff(
                    &input_stream,
                    decompress_plugin,
                    out_stream_ptr,
                    compress_plugin_ptr,
                    0   # out_diff_curPos
                )
    finally:
        del out_stream

    if out_vector.size() == 0:
        raise HDiffPatchError("Recompression produced empty result")

    return PyBytes_FromStringAndSize(<char*>out_vector.data(), out_vector.size())


def _lite_unsupported_message(codec_name: str) -> str:
    """Build the error message for a codec that has no lite compress-type byte."""
    return (
        f"Compression type {codec_name!r} is not supported by HPatchLite lite diffs "
        f"(the lite header has no compress-type byte for it). Supported types: "
        f"{', '.join(sorted(_lite_supported_compression_types))}."
    )


cdef hpi_compressType _lite_compress_type_tag(str codec_name) except *:
    """Map a lite-supported codec name to its ``hpi_compressType`` header tag."""
    if codec_name == COMPRESSION_NONE:
        return hpi_compressType_no
    elif codec_name == COMPRESSION_ZLIB:
        return hpi_compressType_zlib
    elif codec_name == COMPRESSION_LZMA:
        return hpi_compressType_lzma
    elif codec_name == COMPRESSION_LZMA2:
        return hpi_compressType_lzma2
    elif codec_name == COMPRESSION_ZSTD:
        return hpi_compressType_zstd
    elif codec_name == COMPRESSION_BZIP2:
        return hpi_compressType_bzip2
    elif codec_name == COMPRESSION_TAMP:
        return <hpi_compressType><int>_HPI_COMPRESS_TYPE_TAMP
    elif codec_name == COMPRESSION_LZ4 or codec_name == COMPRESSION_LZ4HC:
        return hpi_compressType_lz4
    elif codec_name == COMPRESSION_TUZ:
        return hpi_compressType_tuz
    else:
        raise HDiffPatchError(f"No lite compress-type tag for codec: {codec_name}")


cdef str _lite_normalize_compression(compression):
    """Resolve a compression argument to a lite-supported codec name.

    Parameters
    ----------
    compression : CompressionType, BaseConfig, or None
        The compression argument passed to a lite-diff function.

    Returns
    -------
    str
        A codec name in ``_lite_supported_compression_types``.

    Raises
    ------
    ValueError
        If the compression type is not a valid HDiffPatch codec at all.
    HDiffPatchError
        If the codec is a valid HDiffPatch codec with no lite compress-type byte.
    """
    if compression is None:
        return COMPRESSION_NONE
    if isinstance(compression, ZlibConfig):
        return COMPRESSION_ZLIB
    if isinstance(compression, Lzma2Config):
        return COMPRESSION_LZMA2
    if isinstance(compression, LzmaConfig):
        return COMPRESSION_LZMA
    if isinstance(compression, TampConfig):
        return COMPRESSION_TAMP
    if isinstance(compression, Lz4Config):
        return COMPRESSION_LZ4
    if isinstance(compression, Lz4HCConfig):
        return COMPRESSION_LZ4HC
    if isinstance(compression, TuzConfig):
        return COMPRESSION_TUZ
    if isinstance(compression, ZStdConfig):
        return COMPRESSION_ZSTD
    if isinstance(compression, BZip2Config):
        return COMPRESSION_BZIP2
    if isinstance(compression, XzConfig):
        raise HDiffPatchError(_lite_unsupported_message(COMPRESSION_XZ))
    if isinstance(compression, BaseConfig):
        raise HDiffPatchError(f"Unsupported compression config for lite diffs: {type(compression).__name__}")

    codec_name = str(compression).lower()
    if codec_name not in _valid_compression_types:
        raise ValueError(
            f"Invalid compression type: {codec_name}. "
            f"Valid options: {', '.join(sorted(_valid_compression_types))}"
        )
    if codec_name not in _lite_supported_compression_types:
        raise HDiffPatchError(_lite_unsupported_message(codec_name))
    return codec_name


cdef cpp_bool _run_check_lite_diff(bytes old_data, bytes new_data, bytes lite_diff, str codec_name):
    """Run the vendored ``check_lite_diff`` round-trip validator."""
    cdef const unsigned char* old_ptr = <const unsigned char*>PyBytes_AsString(old_data)
    cdef const unsigned char* old_end = old_ptr + PyBytes_Size(old_data)
    cdef const unsigned char* new_ptr = <const unsigned char*>PyBytes_AsString(new_data)
    cdef const unsigned char* new_end = new_ptr + PyBytes_Size(new_data)
    cdef const unsigned char* diff_ptr = <const unsigned char*>PyBytes_AsString(lite_diff)
    cdef const unsigned char* diff_end = diff_ptr + PyBytes_Size(lite_diff)
    cdef hpatch_TDecompress* decompress_plugin = <hpatch_TDecompress*>get_decompress_plugin(codec_name)
    cdef cpp_bool ok

    with nogil:
        ok = c_check_lite_diff(new_ptr, new_end, old_ptr, old_end, diff_ptr, diff_end, decompress_plugin)
    return ok


def diff_lite(
    old_data: bytes,
    new_data: bytes,
    *,
    compression: Union[LiteCompressionType, 'BaseConfig', None] = None,
    validate: bool = True,
    big_cache_match: bool = False,
) -> bytes:
    """Create an HPatchLite "lite"-format binary diff between old and new data.

    Lite diffs are the compact format consumed by HDiffPatch's tiny on-device
    applier (``hpatch_lite_patch``). This output is **not** interchangeable with
    :func:`diff`/:func:`apply`; it can only be applied by an HPatchLite-family
    patcher.

    Parameters
    ----------
    old_data : bytes
        The original data.
    new_data : bytes
        The new data to diff against.
    compression : LiteCompressionType, BaseConfig, or None, default=None
        Compression algorithm to use. Any codec with a compress-type byte in
        the lite header is accepted: ``"none"``, ``"zlib"``, ``"lzma"``,
        ``"lzma2"``, ``"zstd"``, ``"bzip2"``, ``"lz4"``, ``"lz4hc"``, ``"tuz"``,
        and ``"tamp"`` (the latter under the vendor-specific byte ``0xF0``). A
        device can only apply the codecs whose decoders it links.
    validate : bool, default=True
        If True, validates that the lite diff reconstructs new_data from old_data
        using the vendored HPatchLite applier.
    big_cache_match : bool, default=False
        If True, builds an extra match cache over ``old_data`` (a bloom filter of
        roughly 0.5-1 byte per byte of ``old_data``) so candidate matches are
        rejected without a suffix-array search. Diff creation gets faster and
        the output is byte-identical; see the Performance docs for measurements
        and trade-offs.

    Returns
    -------
    bytes
        The lite-format diff data as bytes.

    Raises
    ------
    TypeError
        If old_data or new_data are not bytes.
    ValueError
        If compression is not a recognized compression type.
    HDiffPatchError
        If the codec has no lite compress-type byte, if diff creation fails, or
        if roundtrip validation fails.
    """
    if not isinstance(old_data, bytes) or not isinstance(new_data, bytes):
        raise TypeError("old_data and new_data must be bytes")

    codec_name = _lite_normalize_compression(compression)

    cdef const unsigned char* old_ptr = <const unsigned char*>PyBytes_AsString(old_data)
    cdef const unsigned char* new_ptr = <const unsigned char*>PyBytes_AsString(new_data)
    cdef const unsigned char* old_end = old_ptr + PyBytes_Size(old_data)
    cdef const unsigned char* new_end = new_ptr + PyBytes_Size(new_data)
    cdef vector[unsigned char] diff_vector
    cdef hdiffi_TCompress lite_compress
    cdef size_t diff_size
    cdef cpp_bool use_big_cache = big_cache_match

    # A NULL ``compress`` with ``hpi_compressType_no`` yields an uncompressed
    # lite diff; ``do_compress`` handles the NULL plugin internally.
    lite_compress.compress = NULL
    lite_compress.compress_type = hpi_compressType_no

    # Keep the resolved plugin alive for the duration of the create call; its
    # __dealloc__ frees any custom-plugin allocation once this scope ends.
    compression_plugin = None
    if codec_name != COMPRESSION_NONE:
        compression_plugin = _resolve_compression_to_plugin(compression)
        lite_compress.compress = compression_plugin.plugin
        lite_compress.compress_type = _lite_compress_type_tag(codec_name)

    with nogil:
        c_create_lite_diff(new_ptr, new_end, old_ptr, old_end, diff_vector, &lite_compress,
                           kLiteMatchScore_default, use_big_cache)

    diff_size = diff_vector.size()
    if diff_size == 0:
        raise HDiffPatchError("HDiffPatch created empty lite diff")

    diff_bytes = PyBytes_FromStringAndSize(<char*>diff_vector.data(), diff_size)

    if validate:
        if not _run_check_lite_diff(old_data, new_data, diff_bytes, codec_name):
            raise HDiffPatchError(
                "Roundtrip validation failed: the lite diff does not reconstruct new_data from old_data"
            )

    return diff_bytes


cdef hpi_compressType _lite_header_compress_type(const unsigned char* diff_ptr,
                                                  const unsigned char* diff_end) except *:
    """Read the compress-type byte from a lite diff header."""
    cdef hpi_compressType compress_type
    if not c_check_lite_diff_open(diff_ptr, diff_end, &compress_type):
        raise HDiffPatchError("Invalid or corrupt lite diff header")
    return compress_type


cdef hpatch_TDecompress* _lite_header_decompress_plugin(hpi_compressType compress_type) except? NULL:
    """Return the decompressor for a lite header's compress-type byte (NULL for uncompressed)."""
    cdef int ct = <int>compress_type
    if ct == <int>hpi_compressType_no:
        return NULL
    elif ct == <int>hpi_compressType_zlib:
        return <hpatch_TDecompress*>&zlibDecompressPlugin
    elif ct == <int>hpi_compressType_lzma:
        return <hpatch_TDecompress*>&lzmaDecompressPlugin
    elif ct == <int>hpi_compressType_lzma2:
        return <hpatch_TDecompress*>&lzma2DecompressPlugin
    elif ct == <int>hpi_compressType_zstd:
        return <hpatch_TDecompress*>&zstdDecompressPlugin
    elif ct == <int>hpi_compressType_bzip2:
        return <hpatch_TDecompress*>&bz2DecompressPlugin
    elif ct == <int>hpi_compressType_lz4:
        return <hpatch_TDecompress*>&lz4DecompressPlugin
    elif ct == <int>hpi_compressType_tuz:
        return <hpatch_TDecompress*>&tuzDecompressPlugin
    elif ct == _HPI_COMPRESS_TYPE_TAMP:
        return <hpatch_TDecompress*>&tampDecompressPlugin
    raise HDiffPatchError(
        f"Lite diff uses compress-type byte 0x{ct:02X}, which has no "
        f"decompressor available in this build"
    )


def apply_lite(old_data: bytes, lite_diff: bytes) -> bytes:
    """Apply an HPatchLite "lite"-format patch to reconstruct the new data.

    This is the lite-format counterpart of :func:`apply`: given the original
    ``old_data`` and a ``lite_diff`` produced by :func:`diff_lite`, it returns
    the reconstructed new bytes. It drives the vendored HPatchLite applier
    (``hpatch_lite_open`` + ``hpatch_lite_patch``) -- the same code path a
    device runs -- so a successful call is a genuine end-to-end round-trip.

    The compression codec is auto-detected from the lite header (which is
    self-describing, exactly like the standard patch format), so there is no
    ``compression`` argument. Upstream codecs use their ``hpi_compressType``
    values; the vendor-specific byte ``0xF0`` selects the tamp decompressor.

    Parameters
    ----------
    old_data : bytes
        The original data the patch was created against.
    lite_diff : bytes
        The lite-format diff produced by :func:`diff_lite`.

    Returns
    -------
    bytes
        The reconstructed new data.

    Raises
    ------
    TypeError
        If old_data or lite_diff are not bytes.
    HDiffPatchError
        If the header is invalid, names a codec whose decompressor is not
        available, or the patch fails to reconstruct the data.
    """
    if not (isinstance(old_data, bytes) and isinstance(lite_diff, bytes)):
        raise TypeError("old_data and lite_diff must be bytes")

    cdef const unsigned char* old_ptr = <const unsigned char*>PyBytes_AsString(old_data)
    cdef const unsigned char* old_end = old_ptr + PyBytes_Size(old_data)
    cdef const unsigned char* diff_ptr = <const unsigned char*>PyBytes_AsString(lite_diff)
    cdef const unsigned char* diff_end = diff_ptr + PyBytes_Size(lite_diff)

    # Peek the self-describing compress-type byte to pick the decompressor,
    # mirroring how apply() auto-detects the codec from the diff itself.
    cdef hpi_compressType compress_type = _lite_header_compress_type(diff_ptr, diff_end)

    cdef hpatch_TDecompress* decompress_plugin = _lite_header_decompress_plugin(compress_type)

    cdef vector[unsigned char] out_vector
    cdef int rc
    with nogil:
        rc = c_apply_lite_diff(old_ptr, old_end, diff_ptr, diff_end,
                               decompress_plugin, NULL, out_vector)

    if rc == 2:
        raise HDiffPatchError("Failed to open the decompressor for the lite diff")
    if rc != 0:
        raise HDiffPatchError("Failed to apply lite diff: it does not reconstruct from old_data")

    return PyBytes_FromStringAndSize(<char*>out_vector.data(), out_vector.size())


def recompress_lite(
    lite_diff: bytes,
    compression: Union[LiteCompressionType, 'BaseConfig', None],
) -> bytes:
    """Recompress an HPatchLite "lite"-format diff with a different compression algorithm.

    This is the lite-format counterpart of :func:`recompress`. Only the diff
    body is re-encoded; the match search is not redone, so for a diff made by
    :func:`diff_lite` the output is byte-identical to calling :func:`diff_lite`
    with ``compression`` directly.
    A common pattern is to create the diff once uncompressed
    (``diff_lite(old, new)``) and then derive each compressed variant from it.

    The input's codec is auto-detected from the lite header. Inplace-variant
    headers (version code 2, carrying ``extraSafeSize``) are preserved.

    Parameters
    ----------
    lite_diff : bytes
        A lite-format diff, compressed with any lite codec or uncompressed.
    compression : LiteCompressionType, BaseConfig, or None
        Target compression, with the same accepted forms as :func:`diff_lite`:
        any lite codec name or a matching ``*Config``. ``None``/``"none"``
        stores the body uncompressed.

    Returns
    -------
    bytes
        The recompressed lite-format diff.

    Raises
    ------
    TypeError
        If lite_diff is not bytes.
    ValueError
        If compression is not a recognized compression type.
    HDiffPatchError
        If the codec has no lite compress-type byte, or if the lite diff's
        header or body is malformed.
    """
    if not isinstance(lite_diff, bytes):
        raise TypeError("lite_diff must be bytes")

    codec_name = _lite_normalize_compression(compression)

    cdef const unsigned char* diff_ptr = <const unsigned char*>PyBytes_AsString(lite_diff)
    cdef const unsigned char* diff_end = diff_ptr + PyBytes_Size(lite_diff)
    cdef hpatch_TDecompress* decompress_plugin = _lite_header_decompress_plugin(
        _lite_header_compress_type(diff_ptr, diff_end)
    )

    cdef hdiffi_TCompress lite_compress
    lite_compress.compress = NULL
    lite_compress.compress_type = hpi_compressType_no
    compression_plugin = None
    if codec_name != COMPRESSION_NONE:
        compression_plugin = _resolve_compression_to_plugin(compression)
        lite_compress.compress = compression_plugin.plugin
        lite_compress.compress_type = _lite_compress_type_tag(codec_name)

    cdef vector[unsigned char] out_vector
    cdef int rc
    with nogil:
        rc = c_recompress_lite_diff(diff_ptr, diff_end, decompress_plugin, &lite_compress, out_vector)

    if rc == 1:
        raise HDiffPatchError("Invalid or corrupt lite diff header")
    if rc == 3:
        raise HDiffPatchError("Corrupt lite diff body: it does not describe the new data's size")
    if rc != 0:
        raise HDiffPatchError("Failed to decompress the lite diff body")

    return PyBytes_FromStringAndSize(<char*>out_vector.data(), out_vector.size())
