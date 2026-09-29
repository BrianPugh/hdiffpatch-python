Performance
===========

* :func:`hdiffpatch.diff` is the expensive operation: it searches for matches between ``old_data`` and ``new_data``, and its cost grows with input size. :func:`hdiffpatch.apply` is comparatively cheap (10-60x faster in the benchmark below).

  * ``validate=True`` (the default) round-trips the freshly created diff through :func:`hdiffpatch.apply` and verifies that it reproduces ``new_data`` exactly. This adds only a few percent on top of creating the diff, and catches any data-compromising bug in the diff/compression stack before a corrupt diff is stored or shipped — leave it enabled.

* :func:`hdiffpatch.recompress` re-encodes an existing diff without redoing the expensive diff computation, paying only for the recompression itself. To produce the same diff with several compression algorithms, create it once and recompress it per target instead of calling :func:`hdiffpatch.diff` repeatedly:

.. code-block:: python

   base = hdiffpatch.diff(old_data, new_data, compression="none")
   diff_zstd = hdiffpatch.recompress(base, compression="zstd")
   diff_lzma = hdiffpatch.recompress(base, compression="lzma")

* ``big_cache_match=True`` on :func:`hdiffpatch.diff` and :func:`hdiffpatch.diff_lite` speeds up the match search (see below).

Big-cache matching
------------------

``big_cache_match`` maps to HDiffPatch's ``isUseBigCacheMatch``. Before matching, it hashes every 5-byte window of ``old_data`` into a bloom filter, and the matcher uses that filter to reject most candidate positions without a suffix-array search. It is a matching-stage option only, so it works the same for every compression type and has no effect on :func:`hdiffpatch.apply`, :func:`hdiffpatch.recompress`, or their lite counterparts.

Trade-offs:

* **Output:** byte-identical to ``big_cache_match=False``. Diff size and compression ratio don't change, and a diff made either way can be cached or compared against the other.
* **Speed:** on 0.65-2 MB firmware images, the match search is about 15-30% faster. On the RPI_PICO pair used in the benchmarks below (measured separately, best of 9, ``validate=False``; the tables below use the default ``big_cache_match=False``), :func:`hdiffpatch.diff` went from 26.8 to 19.6 ms and :func:`hdiffpatch.diff_lite` from 26.3 to 18.9 ms. On ESP32 images of 1.3-2 MB the gain was 15-25%. Building the filter is one extra pass over ``old_data``; upstream warns that this build is slow, but it paid for itself at every size measured, down to 4 KB inputs.
* **Memory:** the filter holds at least 4 bits per byte of ``old_data``, rounded up to a power of 2, so 0.5-1 byte per byte of ``old_data`` (a 2 MB image costs 1 MB). That sits on top of the suffix array the matcher always builds (4 bytes per byte of ``old_data`` below 2 GB, 8 above), and in the firmware measurements peak memory didn't grow measurably. For multi-GB inputs, budget up to ``len(old_data)`` extra bytes.
* **Threads:** the filter is built on the calling thread, like the rest of the match search, with the GIL released.

The default stays ``False`` to keep the upstream default and the existing memory profile for very large inputs. For firmware-sized inputs, turning it on is a free speedup.

Benchmarks
----------

Diffing two consecutive MicroPython RPI_PICO firmware releases (~650 KB each, best of 5 runs, Apple M3). Each compression type uses its default settings. Absolute times vary by machine and input; the ratios are the point. Regenerate with ``uv run python tools/benchmark.py``.

* **diff** — create the compressed diff from scratch: :func:`hdiffpatch.diff` with ``validate=False``.
* **apply** — apply that diff to the old file with :func:`hdiffpatch.apply`.
* **recompress** — re-encode a precomputed uncompressed diff into this compression with :func:`hdiffpatch.recompress`; compare against the *diff* column to see what skipping the diff computation saves.
* **diff size / % of new file** — the compressed diff in bytes, and relative to the new file's size (lower is better).

===========  =========  ==========  ===============  =========  =============
compression  diff (ms)  apply (ms)  recompress (ms)  diff size  % of new file
===========  =========  ==========  ===============  =========  =============
none              25.5         0.4                —    161,041          24.1%
zlib              30.9         1.0              5.2     99,772          14.9%
lzma              36.5         3.3             10.9     92,647          13.9%
zstd              41.3         0.6             15.7     97,520          14.6%
bzip2             34.2         4.0              8.6    102,686          15.4%
tamp              40.5         1.1             15.1    110,711          16.6%
===========  =========  ==========  ===============  =========  =============

``validate=True`` measured 26.0 ms against 25.5 ms with ``validate=False`` (uncompressed diff) — a few percent of overhead.

Standard vs. lite
~~~~~~~~~~~~~~~~~~

HPatchLite is HDiffPatch's tiny on-device applier format (``hpatch_lite_patch``), built for minimal device RAM/flash. :func:`hdiffpatch.diff_lite` and :func:`hdiffpatch.apply_lite` produce and consume it; it is **not** interchangeable with :func:`hdiffpatch.diff`/:func:`hdiffpatch.apply`. The trade-off is a slightly larger diff for a much smaller device-side footprint, which does not appear in host apply times. Every codec with a lite compress-type byte is supported (none/zlib/lzma/lzma2/zstd/bzip2/lz4/lz4hc/tamp); the table covers the ones small enough to decode on a microcontroller.

:func:`hdiffpatch.recompress_lite` is the lite counterpart of :func:`hdiffpatch.recompress`: it re-encodes an existing lite diff's body without redoing the match search, and for a diff made by :func:`hdiffpatch.diff_lite` its output is byte-identical to calling :func:`hdiffpatch.diff_lite` with the target codec. The *lite recompress* column times re-encoding a precomputed uncompressed lite diff, so to produce one lite diff under several codecs:

.. code-block:: python

   base = hdiffpatch.diff_lite(old, new)
   lite_lzma = hdiffpatch.recompress_lite(base, "lzma")
   lite_tamp = hdiffpatch.recompress_lite(base, "tamp")

===========  =============  ==============  ====================  ==============  ===============  ========  =========  ========
compression  std diff (ms)  lite diff (ms)  lite recompress (ms)  std apply (ms)  lite apply (ms)  std size  lite size  lite/std
===========  =============  ==============  ====================  ==============  ===============  ========  =========  ========
none                  25.8            25.9                     —             0.5              0.2   161,041    637,195    395.7%
zlib                  33.0           128.7                 106.5             1.0              0.9    99,772    106,275    106.5%
lzma                  40.8            72.6                  43.7             3.8              3.8    92,647     96,859    104.5%
tamp                  45.3            68.2                  40.6             1.2              1.5   110,711    125,726    113.6%
===========  =============  ==============  ====================  ==============  ===============  ========  =========  ========

The ``none`` row is a ~4x outlier because the uncompressed lite encoding stores many literal new-data bytes; with a codec those literals compress and the gap collapses to ~5-14%, so lite should be used with compression.
