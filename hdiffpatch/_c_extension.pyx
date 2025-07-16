"""HDiffPatch Cython extension for high-performance binary diff/patch operations."""

from typing import Union, Literal, TYPE_CHECKING

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

from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc.stddef cimport size_t
from libcpp.vector cimport vector
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AsString, PyBytes_Size

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
    void hdiff_create_compressed_diff "create_compressed_diff"(const unsigned char* newData, const unsigned char* newData_end,
                                                             const unsigned char* oldData, const unsigned char* oldData_end,
                                                             vector[unsigned char]& out_diff,
                                                             const hdiff_TCompress* compressPlugin)

cdef extern from "libHDiffPatch/HPatch/patch_types.h":
    ctypedef struct hpatch_TDecompress:
        pass

cdef extern from "libHDiffPatch/HPatch/patch.h":
    int patch(unsigned char* out_newData, unsigned char* out_newData_end,
             const unsigned char* oldData, const unsigned char* oldData_end,
             const unsigned char* diff, const unsigned char* diff_end)

    hpatch_BOOL getCompressedDiffInfo_mem(hpatch_compressedDiffInfo* out_diffInfo,
                                         const unsigned char* compressedDiff,
                                         const unsigned char* compressedDiff_end)

    hpatch_BOOL patch_decompress_mem(unsigned char* out_newData, unsigned char* out_newData_end,
                                     const unsigned char* oldData, const unsigned char* oldData_end,
                                     const unsigned char* compressedDiff, const unsigned char* compressedDiff_end,
                                     hpatch_TDecompress* decompressPlugin)

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
                               hpatch_StreamPos_t out_diff_curPos) except +

    hpatch_StreamPos_t resave_single_compressed_diff(
        const hpatch_TStreamInput* in_diff,
        hpatch_TDecompress* decompressPlugin,
        const hpatch_TStreamOutput* out_diff,
        const hdiff_TCompress* compressPlugin,
        const hpatch_singleCompressedDiffInfo* diffInfo,
        hpatch_StreamPos_t in_diff_curPos,
        hpatch_StreamPos_t out_diff_curPos) except +

cdef extern from "compress_plugin_demo.h":
    extern const void* zlibCompressPlugin
    extern const void* lzmaCompressPlugin
    extern const void* lzma2CompressPlugin
    extern const void* zstdCompressPlugin
    extern const void* bz2CompressPlugin

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

# TCompressPlugin_zlib structure for custom zlib configuration
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

# Type aliases for compression parameters
CompressionType = Literal["none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp"]

# Constants for convenience
COMPRESSION_NONE = "none"
COMPRESSION_ZLIB = "zlib"
COMPRESSION_LZMA = "lzma"
COMPRESSION_LZMA2 = "lzma2"
COMPRESSION_ZSTD = "zstd"
COMPRESSION_BZIP2 = "bzip2"
COMPRESSION_TAMP = "tamp"


_valid_compression_types = {"none", "zlib", "lzma", "lzma2", "zstd", "bzip2", "tamp"}


class HDiffPatchError(Exception):
    """Base exception for HDiffPatch operations."""


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
    custom_plugin.thread_num = lzma_config.thread_num

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
    custom_plugin.thread_num = lzma2_config.thread_num

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
    custom_plugin.thread_num = zstd_config.workers

    # Convert window to dict_bits if specified, otherwise use default
    if zstd_config.window is not None:
        custom_plugin.dict_bits = zstd_config.window
    # Note: other advanced parameters like hash_log, chain_log, etc. are not directly
    # supported by the HDiffPatch zstd plugin structure, so we only use the main ones

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
        remaining_newDataDiff = newDataDiffSize - newDataDiff_used
        if remaining_newDataDiff < 0:
            remaining_newDataDiff = 0

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


cdef class VectorOutputStream:
    """Container for vector-based output stream for HDiffPatch operations."""
    cdef hpatch_TStreamOutput stream
    cdef vector[unsigned char]* output_vector
    cdef hpatch_StreamPos_t current_size

    def __cinit__(self):
        self.output_vector = new vector[unsigned char]()
        self.current_size = 0
        self.stream.streamImport = <void*>self
        self.stream.streamSize = 0
        self.stream.write = _vector_output_write

    def __dealloc__(self):
        """Clean up vector memory."""
        if self.output_vector != NULL:
            del self.output_vector

    cdef const hpatch_TStreamOutput* get_stream(self):
        """Get pointer to the stream interface (C-only method)."""
        return &self.stream

    cdef vector[unsigned char]* get_vector(self):
        """Get pointer to the output vector (C-only method)."""
        return self.output_vector

    cdef hpatch_StreamPos_t get_size(self):
        """Get the current stream size (C-only method)."""
        return self.current_size


cdef hpatch_BOOL _vector_output_write(const hpatch_TStreamOutput* stream,
                                     hpatch_StreamPos_t writeToPos,
                                     const unsigned char* data,
                                     const unsigned char* data_end) noexcept:
    """C callback function for writing to vector output stream."""
    cdef VectorOutputStream self_obj = <VectorOutputStream>stream.streamImport
    cdef size_t data_size = data_end - data
    cdef size_t required_size = writeToPos + data_size

    try:
        # Resize vector if necessary
        if self_obj.output_vector.size() < required_size:
            self_obj.output_vector.resize(required_size)

        # Copy data to vector
        if data_size > 0:
            memcpy(&(self_obj.output_vector.at(writeToPos)), data, data_size)

        # Update current size
        if writeToPos + data_size > self_obj.current_size:
            self_obj.current_size = writeToPos + data_size
            self_obj.stream.streamSize = self_obj.current_size

        return 1  # hpatch_TRUE
    except:
        return 0  # hpatch_FALSE


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
    else:
        # String-based compression - normalize and validate
        compression_str = str(compression).lower()
        if compression_str not in _valid_compression_types:
            raise ValueError(f"Invalid compression type: {compression_str}. Valid options: {', '.join(_valid_compression_types)}")

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

    if compression_plugin is None:  # No compression - use NULL plugin for HDIFF13& header format
        hdiff_create_compressed_diff(new_ptr, new_end, old_ptr, old_end, diff_vector, <hdiff_TCompress*>0)
    else:
        hdiff_create_compressed_diff(new_ptr, new_end, old_ptr, old_end, diff_vector, compression_plugin.plugin)

    diff_size = diff_vector.size()
    if diff_size == 0:
        raise HDiffPatchError("HDiffPatch created empty diff")

    diff_bytes = PyBytes_FromStringAndSize(<char*>diff_vector.data(), diff_size)

    if validate:
        try:
            result_data = apply(old_data, diff_bytes)
            if result_data != new_data:
                raise HDiffPatchError("Roundtrip validation failed: applying the diff to old_data does not produce new_data")
        except Exception as e:
            if isinstance(e, HDiffPatchError) and "Roundtrip validation failed" in str(e):
                raise
            raise HDiffPatchError(f"Roundtrip validation failed: {str(e)}") from e

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

            result = patch(new_ptr, new_end, old_ptr, old_end, diff_ptr, diff_end)

        if result == 0:
            raise HDiffPatchError("HDiffPatch patch operation failed")

        # Create Python bytes object with the result
        result_bytes = PyBytes_FromStringAndSize(<char*>new_ptr, new_size)

        if new_ptr != NULL:
            free(new_ptr)
        return result_bytes
    except Exception as e:
        if new_ptr != NULL:
            free(new_ptr)
        raise HDiffPatchError(f"Patch application failed: {str(e)}") from e


def recompress(
    diff_data: bytes,
    compression: Union[CompressionType, 'BaseConfig', None] = None
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
    compression : CompressionType, BaseConfig, or None, default=None
        Target compression algorithm to use

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

    except Exception as e:
        raise HDiffPatchError(f"Failed to detect diff format: {str(e)}") from e

    # Resolve output compression plugin
    compression_plugin = _resolve_compression_to_plugin(compression)

    # Create output stream
    cdef VectorOutputStream output_stream = VectorOutputStream()
    cdef hpatch_StreamPos_t result_size
    cdef vector[unsigned char]* result_vector

    try:
        # Call appropriate resave function based on detected format
        if is_single_diff:
            resave_single_compressed_diff(
                &input_stream,
                decompress_plugin,
                output_stream.get_stream(),
                compression_plugin.plugin if compression_plugin is not None else NULL,
                &singleDiffInfo,
                0,  # in_diff_curPos
                0   # out_diff_curPos
            )
        else:
            resave_compressed_diff(
                &input_stream,
                decompress_plugin,
                output_stream.get_stream(),
                compression_plugin.plugin if compression_plugin is not None else NULL,
                0   # out_diff_curPos
            )

        # Extract result from output vector
        result_size = output_stream.get_size()
        if result_size == 0:
            raise HDiffPatchError("Recompression produced empty result")

        result_vector = output_stream.get_vector()
        return PyBytes_FromStringAndSize(<char*>result_vector.data(), result_size)

    except Exception as e:
        raise HDiffPatchError(f"Recompression failed: {str(e)}") from e
