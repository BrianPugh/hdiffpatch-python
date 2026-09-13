// apply_lite_shim.hpp
//
// Host-side helper that APPLIES an HPatchLite "lite"-format diff to old_data
// and returns the reconstructed new bytes. It mirrors the vendored
// check_lite_diff() (libHDiffPatch/HDiff/diff.cpp): same listener/callback
// trio and the same decompress-stream wiring, but it writes the reconstruction
// into an output buffer instead of comparing it against an expected image.
//
// It calls only PUBLIC vendored APIs (hpatch_lite_open / hpatch_lite_patch and
// the hpatch_TDecompress open/decompress_part/close interface), so it does not
// modify any vendored source. The decompressor is chosen by the caller from
// the compress-type byte the lite header self-describes (see apply_lite in
// _c_extension.pyx), exactly like the standard apply() auto-detects its codec.

#ifndef HDIFFPATCH_APPLY_LITE_SHIM_HPP
#define HDIFFPATCH_APPLY_LITE_SHIM_HPP

#include <cstring>
#include <vector>

#include "libHDiffPatch/HPatch/patch.h"        // mem_as_hStreamInput
#include "libHDiffPatch/HPatch/patch_types.h"  // hpatch_TDecompress, hpatch_kFileIOBufBetterSize
#include "libHDiffPatch/HPatchLite/hpatch_lite.h"

namespace hdiffpatch_lite_shim {

// Return codes for apply_lite_diff().
enum {
    kApplyLiteOk = 0,          // success; out_new holds the reconstructed bytes
    kApplyLiteOpenError = 1,   // header could not be opened (bad magic/format)
    kApplyLiteDecompError = 2, // compressed diff but decompressor open failed
    kApplyLitePatchError = 3,  // patch/reconstruction failed
};

struct TApplyListener : public hpatchi_listener_t {
    hpatch_decompressHandle decompressor;
    hpatch_TDecompress*     decompressPlugin;
    const hpi_byte*         diffData_cur;
    const hpi_byte*         diffData_end;
    hpatch_TStreamInput     diffStream;
    hpi_pos_t               uncompressSize;
    const hpi_byte*         oldData;
    const hpi_byte*         oldData_end;
    std::vector<unsigned char>* out;

    TApplyListener() : decompressor(0), decompressPlugin(0) {}
    ~TApplyListener() {
        if (decompressor && decompressPlugin)
            decompressPlugin->close(decompressPlugin, decompressor);
    }

    // Read raw (uncompressed) diff bytes straight from the buffer.
    static hpi_BOOL _read_diff(hpi_TInputStreamHandle inputStream,
                               hpi_byte* out_data, hpi_size_t* data_size) {
        TApplyListener& self = *(TApplyListener*)inputStream;
        size_t d_size = (size_t)(self.diffData_end - self.diffData_cur);
        size_t r_size = *data_size;
        if (r_size > d_size) {
            r_size = d_size;
            *data_size = (hpi_size_t)r_size;
        }
        memcpy(out_data, self.diffData_cur, r_size);
        self.diffData_cur += r_size;
        return hpi_TRUE;
    }

    // Read diff bytes through the decompressor (compressed lite diffs).
    static hpi_BOOL _read_diff_dec(hpi_TInputStreamHandle inputStream,
                                   hpi_byte* out_data, hpi_size_t* data_size) {
        TApplyListener& self = *(TApplyListener*)inputStream;
        hpi_size_t r_size = *data_size;
        if (r_size > self.uncompressSize) {
            r_size = (hpi_size_t)self.uncompressSize;
            *data_size = r_size;
        }
        if (!self.decompressPlugin->decompress_part(self.decompressor, out_data, out_data + r_size))
            return hpi_FALSE;
        self.uncompressSize -= r_size;
        return hpi_TRUE;
    }

    // Append reconstructed new bytes to the output vector.
    static hpi_BOOL _write_new(struct hpatchi_listener_t* listener,
                               const hpi_byte* data, hpi_size_t data_size) {
        TApplyListener& self = *(TApplyListener*)listener;
        self.out->insert(self.out->end(), data, data + data_size);
        return hpi_TRUE;
    }

    // Random-access read from the old image.
    static hpi_BOOL _read_old(struct hpatchi_listener_t* listener,
                              hpi_pos_t read_from_pos, hpi_byte* out_data, hpi_size_t data_size) {
        TApplyListener& self = *(TApplyListener*)listener;
        size_t dsize = (size_t)(self.oldData_end - self.oldData);
        if ((read_from_pos > dsize) || (data_size > (size_t)(dsize - read_from_pos)))
            return hpi_FALSE;
        memcpy(out_data, self.oldData + (size_t)read_from_pos, data_size);
        return hpi_TRUE;
    }
};

// Apply a lite diff. decompressPlugin must be non-NULL iff the diff is
// compressed; pass NULL for an uncompressed ("none") diff. The compress-type
// byte read from the header is returned via out_compress_type (may be NULL).
static inline int apply_lite_diff(const hpi_byte* oldData, const hpi_byte* oldData_end,
                                  const hpi_byte* lite_diff, const hpi_byte* lite_diff_end,
                                  hpatch_TDecompress* decompressPlugin,
                                  hpi_compressType* out_compress_type,
                                  std::vector<unsigned char>& out_new) {
    TApplyListener listener;
    listener.diffData_cur = lite_diff;
    listener.diffData_end = lite_diff_end;

    hpi_compressType compress_type = hpi_compressType_no;
    hpi_pos_t saved_newSize = 0;
    hpi_pos_t saved_uncompressSize = 0;
    if (!hpatch_lite_open(&listener, TApplyListener::_read_diff,
                          &compress_type, &saved_newSize, &saved_uncompressSize))
        return kApplyLiteOpenError;
    if (out_compress_type)
        *out_compress_type = compress_type;

    listener.diff_data = &listener;
    if (compress_type != hpi_compressType_no) {
        if (decompressPlugin == 0)
            return kApplyLiteDecompError;
        listener.decompressPlugin = decompressPlugin;
        listener.uncompressSize = saved_uncompressSize;
        mem_as_hStreamInput(&listener.diffStream, listener.diffData_cur, lite_diff_end);
        listener.decompressor = decompressPlugin->open(
            decompressPlugin, saved_uncompressSize, &listener.diffStream,
            0, (hpatch_StreamPos_t)(lite_diff_end - listener.diffData_cur));
        if (listener.decompressor == 0)
            return kApplyLiteDecompError;
        listener.read_diff = TApplyListener::_read_diff_dec;
    } else {
        listener.read_diff = TApplyListener::_read_diff;
    }
    listener.write_new = TApplyListener::_write_new;
    listener.oldData = oldData;
    listener.oldData_end = oldData_end;
    listener.read_old = TApplyListener::_read_old;

    out_new.clear();
    out_new.reserve((size_t)saved_newSize);
    listener.out = &out_new;

    std::vector<unsigned char> cache(hpatch_kFileIOBufBetterSize);
    if (!hpatch_lite_patch(&listener, saved_newSize, cache.data(), (hpi_size_t)cache.size()))
        return kApplyLitePatchError;
    if (out_new.size() != (size_t)saved_newSize)
        return kApplyLitePatchError;
    return kApplyLiteOk;
}

}  // namespace hdiffpatch_lite_shim

#endif  // HDIFFPATCH_APPLY_LITE_SHIM_HPP
