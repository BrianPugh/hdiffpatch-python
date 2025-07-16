// tamp_compress_plugin.cpp
// Tamp compression plugin for HDiffPatch
// This plugin provides Tamp compression using the embedded Tamp library

#include <cstdlib>
#include "compress_plugin_demo.h"
#include "decompress_plugin_demo.h"
#include "tamp/common.h"
#include "tamp/compressor.h"
#include "tamp/decompressor.h"

#ifdef __cplusplus
extern "C" {
#endif

// Tamp compression plugin structure
typedef struct {
    hdiff_TCompress base;
    int             window;         // 8..15
    int             literal;        // 5..8 (fixed at 8)
    int             use_custom_dictionary;  // 0 or 1
} TCompressPlugin_tamp;

// Tamp compression function
static hpatch_StreamPos_t _tamp_compress(const hdiff_TCompress* compressPlugin,
                                         const hpatch_TStreamOutput* out_code,
                                         const hpatch_TStreamInput* in_data) {
    hpatch_StreamPos_t result = 0;
    const char* errAt = "";
    unsigned char* read_buf = 0;
    unsigned char* compress_buf = 0;
    unsigned char* window_buf = 0;
    TampCompressor compressor;

    // Get configuration from custom plugin or use defaults
    const TCompressPlugin_tamp* tamp_plugin = (const TCompressPlugin_tamp*)compressPlugin;
    TampConf conf = {
        static_cast<uint16_t>(tamp_plugin->window),
        static_cast<uint16_t>(tamp_plugin->literal),
        static_cast<uint16_t>(tamp_plugin->use_custom_dictionary)
    };

    // Validate that custom dictionary is not used (not yet supported)
    if (conf.use_custom_dictionary) {
        return 0; // Return failure
    }
    hpatch_StreamPos_t readFromPos = 0;
    int outStream_isCanceled = 0;
    size_t window_size = 1 << conf.window; // 2^10 = 1024 bytes
    tamp_res res;
    size_t final_output = 0;

    // Allocate buffers
    read_buf = (unsigned char*)malloc(kCompressBufSize);
    if (!read_buf) _compress_error_return("read buffer alloc");

    compress_buf = (unsigned char*)malloc(kCompressBufSize);
    if (!compress_buf) _compress_error_return("compress buffer alloc");

    window_buf = (unsigned char*)malloc(window_size);
    if (!window_buf) _compress_error_return("window buffer alloc");

    // Initialize Tamp compressor
    res = tamp_compressor_init(&compressor, &conf, window_buf);
    if (res != TAMP_OK) _compress_error_return("tamp_compressor_init");

    // Let Tamp write its own header during compression - no manual header needed

    // Compress data in chunks
    while (readFromPos < in_data->streamSize) {
        size_t readLen = kCompressBufSize;
        if (readLen > (size_t)(in_data->streamSize - readFromPos))
            readLen = (size_t)(in_data->streamSize - readFromPos);

        // Read data from input
        if (!in_data->read(in_data, readFromPos, read_buf, read_buf + readLen))
            _compress_error_return("in_data->read()");

        // Compress the chunk
        size_t output_written = 0;
        size_t input_consumed = 0;
        res = tamp_compressor_compress(&compressor, compress_buf, kCompressBufSize,
                                       &output_written, read_buf, readLen, &input_consumed);

        if (res < 0) _compress_error_return("tamp_compressor_compress");

        // Write compressed data
        if (output_written > 0) {
            _stream_out_code_write(out_code, outStream_isCanceled, result, compress_buf, output_written);
        }

        readFromPos += input_consumed;

        // If we didn't consume all input, we need to handle partial consumption
        if (input_consumed < readLen) {
            readFromPos -= (readLen - input_consumed);
        }
    }

    // Flush any remaining data
    res = tamp_compressor_flush(&compressor, compress_buf, kCompressBufSize, &final_output, false);
    if (res < 0) _compress_error_return("tamp_compressor_flush");

    if (final_output > 0) {
        _stream_out_code_write(out_code, outStream_isCanceled, result, compress_buf, final_output);
    }

clear:
    _check_compress_result(result, outStream_isCanceled, "_tamp_compress()", errAt);
    if (read_buf) free(read_buf);
    if (compress_buf) free(compress_buf);
    if (window_buf) free(window_buf);
    return result;
}

// Define the compression type function
_def_fun_compressType(_tamp_compressType, "tamp");

// Static instance of the tamp compression plugin with default configuration
static const TCompressPlugin_tamp tampCompressPlugin = {
    {_tamp_compressType, _default_maxCompressedSize, _default_setParallelThreadNumber, _tamp_compress},
    10,  // window
    8,   // literal
    0    // use_custom_dictionary
};

//=============================================================================
// TAMP DECOMPRESSION PLUGIN
//=============================================================================

// Tamp decompression state structure
typedef struct _tamp_TDecompress {
    hpatch_StreamPos_t code_begin;
    hpatch_StreamPos_t code_end;
    const struct hpatch_TStreamInput* codeStream;
    unsigned char* dec_buf;
    size_t dec_buf_size;
    unsigned char* window_buf;
    TampDecompressor decompressor;
    unsigned char* input_buf;
    size_t input_buf_size;
    size_t input_buf_pos;
    size_t input_buf_avail;
    hpatch_dec_error_t decError;
} _tamp_TDecompress;

// Check if this plugin can handle the compression type
static hpatch_BOOL _tamp_is_can_open(const char* compressType) {
    return (0 == strcmp(compressType, "tamp"));
}

// Open/initialize tamp decompression
static hpatch_decompressHandle _tamp_decompress_open(hpatch_TDecompress* decompressPlugin,
                                                     hpatch_StreamPos_t dataSize,
                                                     const hpatch_TStreamInput* codeStream,
                                                     hpatch_StreamPos_t code_begin,
                                                     hpatch_StreamPos_t code_end) {
    _tamp_TDecompress* self = 0;
    TampConf conf;
    tamp_res res;
    unsigned char header_buf[1];
    size_t header_consumed = 0;

    // Verify we have at least the header byte
    if (code_end - code_begin < 1) {
        return NULL;
    }

    // Read the 1-byte header to determine window size
    if (!codeStream->read(codeStream, code_begin, header_buf, header_buf + 1)) {
        return NULL;
    }

    // Parse header to get configuration
    res = tamp_decompressor_read_header(&conf, header_buf, 1, &header_consumed);
    if (res != TAMP_OK || header_consumed != 1) {
        return NULL;
    }

    // Check if file requires custom dictionary - not yet supported
    if (conf.use_custom_dictionary) {
        return NULL;
    }

    // Calculate window size from header
    size_t window_size = 1 << conf.window;

    // Allocate memory for the decompressor state and buffers + window
    unsigned char* _mem_buf = (unsigned char*)_dec_malloc(sizeof(_tamp_TDecompress) + kDecompressBufSize * 2 + window_size);
    if (!_mem_buf) _dec_memErr_rt();

    self = (_tamp_TDecompress*)_mem_buf;
    memset(self, 0, sizeof(_tamp_TDecompress));

    // Setup basic state
    self->dec_buf = _mem_buf + sizeof(_tamp_TDecompress);
    self->dec_buf_size = kDecompressBufSize;
    self->input_buf = self->dec_buf + kDecompressBufSize;
    self->input_buf_size = kDecompressBufSize;
    self->window_buf = self->input_buf + kDecompressBufSize;
    self->input_buf_pos = 0;
    self->input_buf_avail = 0;
    self->codeStream = codeStream;
    self->code_begin = code_begin + sizeof(header_buf); // Skip the header byte we already read
    self->code_end = code_end;
    self->decError = hpatch_dec_ok;

    // Initialize Tamp decompressor with the parsed configuration
    res = tamp_decompressor_init(&self->decompressor, &conf, self->window_buf);
    if (res != TAMP_OK) {
        self->decError = hpatch_dec_error;
        return self;
    }

    return self;
}

// Close/cleanup tamp decompression
static hpatch_BOOL _tamp_decompress_close(struct hpatch_TDecompress* decompressPlugin,
                                          hpatch_decompressHandle decompressHandle) {
    _tamp_TDecompress* self = (_tamp_TDecompress*)decompressHandle;
    hpatch_BOOL result = hpatch_TRUE;

    if (self) {
        // Update plugin error state if needed
        if (self->decError != hpatch_dec_ok) {
            _hpatch_update_decError(decompressPlugin, self->decError);
            result = hpatch_FALSE;
        }

        // Clean up memory (window_buf is now part of the allocated block)
        memset(self, 0, sizeof(_tamp_TDecompress));
        free(self);
    }

    return result;
}

// Decompress data part using Tamp decompressor (following bz2 plugin pattern)
static hpatch_BOOL _tamp_decompress_part(hpatch_decompressHandle decompressHandle,
                                         unsigned char* out_part_data,
                                         unsigned char* out_part_data_end) {
    _tamp_TDecompress* self = (_tamp_TDecompress*)decompressHandle;
    unsigned char* current_output = out_part_data;
    size_t remaining_output = out_part_data_end - out_part_data;

    // Main decompression loop - continue until output buffer is filled
    while (remaining_output > 0) {
        size_t output_written = 0;
        size_t input_consumed = 0;
        tamp_res res;
        hpatch_StreamPos_t codeLen = (self->code_end - self->code_begin);

        // Fill input buffer if needed and we have more data to read
        if ((self->input_buf_avail == 0) && (codeLen > 0)) {
            size_t readLen = self->input_buf_size;
            if (readLen > codeLen) readLen = (size_t)codeLen;

            if (!self->codeStream->read(self->codeStream, self->code_begin,
                                       self->input_buf, self->input_buf + readLen)) {
                self->decError = hpatch_dec_error;
                return hpatch_FALSE;
            }

            self->input_buf_pos = 0;
            self->input_buf_avail = readLen;
            self->code_begin += readLen;
            codeLen -= readLen;
        }

        // Track state before decompression to detect no-progress situation
        size_t avail_out_back = remaining_output;
        size_t avail_in_back = self->input_buf_avail;

        // Call Tamp decompressor
        res = tamp_decompressor_decompress(&self->decompressor,
                                           current_output, remaining_output, &output_written,
                                           self->input_buf + self->input_buf_pos,
                                           self->input_buf_avail, &input_consumed);

        // Check for errors (< 0). TAMP_OUTPUT_FULL and TAMP_INPUT_EXHAUSTED are success codes
        if (res < 0) {
            self->decError = hpatch_dec_error;
            return hpatch_FALSE;
        }

        // Update input buffer position
        self->input_buf_pos += input_consumed;
        self->input_buf_avail -= input_consumed;

        // Update output position
        current_output += output_written;
        remaining_output -= output_written;

        // Check for no progress condition (same as bz2 plugin)
        if ((self->input_buf_avail == avail_in_back) && (remaining_output == avail_out_back)) {
            // No progress made - this shouldn't happen unless there's an error
            self->decError = hpatch_dec_error;
            return hpatch_FALSE;
        }

        // If we've exhausted input and made no progress, we're done
        if (output_written == 0 && self->input_buf_avail == 0 && codeLen == 0) {
            break;
        }
    }

    // For now, require exact output size (can be relaxed later if needed)
    if (remaining_output != 0) {
        self->decError = hpatch_dec_error;
        return hpatch_FALSE;
    }

    return hpatch_TRUE;
}

// Static instance of the tamp decompression plugin
static hpatch_TDecompress tampDecompressPlugin = {
    _tamp_is_can_open,
    _tamp_decompress_open,
    _tamp_decompress_close,
    _tamp_decompress_part
};


#ifdef __cplusplus
}
#endif
