// recompress_lite_shim.hpp
//
// Host-side helper that re-encodes the body of an HPatchLite "lite"-format
// diff with a different compressor, without redoing the match search.
//
// The header is parsed with the vendored hpatch_lite_open() /
// hpatchi_inplace_open() (the same pair check_lite_diff() tries), the body is
// decompressed through the caller-chosen hpatch_TDecompress plugin, and the new
// body is produced by the same do_compress() call that serialize_lite_diff()
// (libHDiffPatch/HDiff/diff.cpp) uses. The header is then rewritten exactly as
// serialize_lite_diff() writes it, so recompressing an uncompressed lite diff
// is byte-identical to creating the diff with that compressor directly.

#ifndef HDIFFPATCH_RECOMPRESS_LITE_SHIM_HPP
#define HDIFFPATCH_RECOMPRESS_LITE_SHIM_HPP

#include <cstring>
#include <vector>

#include "libHDiffPatch/HDiff/diff_for_hpatch_lite.h"  // hdiffi_TCompress
#include "libHDiffPatch/HDiff/private_diff/limit_mem_diff/stream_serialize.h"  // do_compress
#include "libHDiffPatch/HPatch/patch.h"  // mem_as_hStreamInput
#include "libHDiffPatch/HPatchLite/hpatch_lite.h"

namespace hdiffpatch_lite_shim {

// Return codes for recompress_lite_diff().
enum {
    kRecompressLiteOk = 0,           // success; out_diff holds the re-encoded diff
    kRecompressLiteOpenError = 1,    // header could not be opened (bad magic/format)
    kRecompressLiteDecompError = 2,  // compressed body but decompressor missing/failed
};

struct TMemReader {
    const hpi_byte* cur;
    const hpi_byte* end;

    // Strict reader: a short read fails, so a truncated header is rejected.
    static hpi_BOOL read(hpi_TInputStreamHandle handle, hpi_byte* out_data, hpi_size_t* data_size) {
        TMemReader& self = *(TMemReader*)handle;
        if (*data_size > (size_t)(self.end - self.cur))
            return hpi_FALSE;
        memcpy(out_data, self.cur, *data_size);
        self.cur += *data_size;
        return hpi_TRUE;
    }
};

static inline hpi_byte saved_size_bytes(hpi_pos_t size) {
    hpi_byte bytes = 0;
    for (; size > 0; size >>= 8)
        ++bytes;
    return bytes;
}

static inline void save_size(std::vector<unsigned char>& buf, hpi_pos_t size) {
    for (; size > 0; size >>= 8)
        buf.push_back((unsigned char)size);
}

// Re-encode a lite diff's body with compressPlugin (compressPlugin->compress may
// be NULL to store it uncompressed). decompressPlugin must be non-NULL iff the
// input body is compressed.
static inline int recompress_lite_diff(const hpi_byte* lite_diff, const hpi_byte* lite_diff_end,
                                       hpatch_TDecompress* decompressPlugin,
                                       const hdiffi_TCompress* compressPlugin,
                                       std::vector<unsigned char>& out_diff) {
    TMemReader reader = {lite_diff, lite_diff_end};
    hpi_compressType compress_type = hpi_compressType_no;
    hpi_pos_t newSize = 0;
    hpi_pos_t uncompressSize = 0;
    hpi_size_t extraSafeSize = 0;
    bool isInplace = false;
    if (!hpatch_lite_open(&reader, TMemReader::read, &compress_type, &newSize, &uncompressSize)) {
        reader.cur = lite_diff;
        if (!hpatchi_inplace_open(&reader, TMemReader::read, &compress_type, &newSize, &uncompressSize,
                                  &extraSafeSize))
            return kRecompressLiteOpenError;
        isInplace = true;
    }

    std::vector<unsigned char> raw;
    if (compress_type == hpi_compressType_no) {
        raw.assign(reader.cur, reader.end);
    } else {
        if (decompressPlugin == 0)
            return kRecompressLiteDecompError;
        hpatch_TStreamInput codeStream;
        mem_as_hStreamInput(&codeStream, reader.cur, reader.end);
        hpatch_decompressHandle handle = decompressPlugin->open(
            decompressPlugin, uncompressSize, &codeStream, 0, (hpatch_StreamPos_t)(reader.end - reader.cur));
        if (handle == 0)
            return kRecompressLiteDecompError;
        // Grow in chunks so a corrupt header claiming a huge size fails on the
        // exhausted stream instead of allocating the claimed size up front.
        const size_t kChunk = 1 << 20;
        hpatch_BOOL ok = hpatch_TRUE;
        while (ok && raw.size() < (size_t)uncompressSize) {
            size_t pos = raw.size();
            size_t n = (size_t)uncompressSize - pos;
            if (n > kChunk)
                n = kChunk;
            raw.resize(pos + n);
            ok = decompressPlugin->decompress_part(handle, raw.data() + pos, raw.data() + pos + n);
        }
        ok = decompressPlugin->close(decompressPlugin, handle) && ok;
        if (!ok)
            return kRecompressLiteDecompError;
    }

    // From here on this mirrors serialize_lite_diff() in HDiff/diff.cpp.
    std::vector<unsigned char> compressed;
    hdiff_private::do_compress(compressed, raw, compressPlugin->compress);
    const hpi_pos_t savedUncompressSize = compressed.empty() ? 0 : (hpi_pos_t)raw.size();
    out_diff.clear();
    out_diff.push_back('h');
    out_diff.push_back('I');
    out_diff.push_back(compressed.empty() ? (unsigned char)hpi_compressType_no
                                          : (unsigned char)compressPlugin->compress_type);
    out_diff.push_back((unsigned char)(((isInplace ? 2 : 1) << 6) | saved_size_bytes(newSize) |
                                       (saved_size_bytes(savedUncompressSize) << 3)));
    if (isInplace)
        out_diff.push_back(saved_size_bytes(extraSafeSize));
    save_size(out_diff, newSize);
    save_size(out_diff, savedUncompressSize);
    if (isInplace)
        save_size(out_diff, extraSafeSize);
    const std::vector<unsigned char>& body = compressed.empty() ? raw : compressed;
    out_diff.insert(out_diff.end(), body.begin(), body.end());
    return kRecompressLiteOk;
}

}  // namespace hdiffpatch_lite_shim

#endif  // HDIFFPATCH_RECOMPRESS_LITE_SHIM_HPP
