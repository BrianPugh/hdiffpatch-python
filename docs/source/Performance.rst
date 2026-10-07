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

Diffing two consecutive MicroPython RPI_PICO firmware releases (~650 KB each, best of 5 runs, Apple M3 MacBook Pro). Each compression type uses its default settings. Absolute times vary by machine and input; the ratios are the point. Regenerate with ``uv run python tools/benchmark.py``.

* **diff** — create the compressed diff from scratch: :func:`hdiffpatch.diff` with ``validate=False``.
* **apply** — apply that diff to the old file with :func:`hdiffpatch.apply`.
* **recompress** — re-encode a precomputed uncompressed diff into this compression with :func:`hdiffpatch.recompress`; compare against the *diff* column to see what skipping the diff computation saves.
* **diff size / % of new file** — the compressed diff in bytes, and relative to the new file's size (lower is better).

===========  =========  ==========  ===============  =========  =============
compression  diff (ms)  apply (ms)  recompress (ms)  diff size  % of new file
===========  =========  ==========  ===============  =========  =============
none              26.1         0.4                —    161,041          24.1%
zlib              31.6         0.9              5.3     99,772          14.9%
lzma              38.1         3.3             11.5     92,647          13.9%
lzma2             38.1         3.3             11.7     92,656          13.9%
xz                38.6         3.7             12.1     92,865          13.9%
zstd              42.8         0.6             16.5     97,520          14.6%
bzip2             35.4         4.2              9.1    102,686          15.4%
brotli            30.2         1.0              3.9     98,925          14.8%
lzham             40.2         1.5             13.7     97,500          14.6%
lz4               26.5         0.4              0.1    131,067          19.6%
lz4hc             28.9         0.5              2.5    120,571          18.1%
tuz               42.9         1.1             16.6    104,363          15.6%
tamp              42.7         1.1             16.3    110,711          16.6%
===========  =========  ==========  ===============  =========  =============

``validate=True`` measured 27.0 ms against 26.3 ms with ``validate=False`` (uncompressed diff) — a few percent of overhead.

Standard vs. lite
~~~~~~~~~~~~~~~~~~

HPatchLite is HDiffPatch's tiny on-device applier format (``hpatch_lite_patch``), built for minimal device RAM/flash. :func:`hdiffpatch.diff_lite` and :func:`hdiffpatch.apply_lite` produce and consume it; it is **not** interchangeable with :func:`hdiffpatch.diff`/:func:`hdiffpatch.apply`. The trade-off is a slightly larger diff for a much smaller device-side footprint, which does not appear in host apply times. Every codec with a lite compress-type byte is supported (none/zlib/lzma/lzma2/zstd/bzip2/lz4/lz4hc/tuz/brotli/lzham/tamp); the table covers the ones small enough to decode on a microcontroller.

:func:`hdiffpatch.recompress_lite` is the lite counterpart of :func:`hdiffpatch.recompress`: it re-encodes an existing lite diff's body without redoing the match search, and for a diff made by :func:`hdiffpatch.diff_lite` its output is byte-identical to calling :func:`hdiffpatch.diff_lite` with the target codec. The *lite recompress* column times re-encoding a precomputed uncompressed lite diff, so to produce one lite diff under several codecs:

.. code-block:: python

   base = hdiffpatch.diff_lite(old, new)
   lite_lzma = hdiffpatch.recompress_lite(base, "lzma")
   lite_tamp = hdiffpatch.recompress_lite(base, "tamp")

===========  =============  ==============  ====================  ==============  ===============  ========  =========  ========
compression  std diff (ms)  lite diff (ms)  lite recompress (ms)  std apply (ms)  lite apply (ms)  std size  lite size  lite/std
===========  =============  ==============  ====================  ==============  ===============  ========  =========  ========
none                  26.2            25.9                     —             0.4              0.2   161,041    637,195    395.7%
zlib                  31.8           128.2                 102.1             1.0              0.9    99,772    106,275    106.5%
lzma                  38.3            66.2                  39.3             3.3              3.1    92,647     96,859    104.5%
lz4                   26.6            26.5                   0.4             0.4              0.3   131,067    148,758    113.5%
lz4hc                 28.9           110.4                  84.0             0.5              0.2   120,571    121,172    100.5%
tuz                   43.2            72.2                  45.9             1.1              1.9   104,363    105,910    101.5%
tamp                  42.8            64.6                  39.1             1.2              1.4   110,711    125,726    113.6%
===========  =============  ==============  ====================  ==============  ===============  ========  =========  ========

The ``none`` row is a ~4x outlier because the uncompressed lite encoding stores many literal new-data bytes; with a codec those literals compress and the gap collapses to ~0.5-14%, so lite should be used with compression.

Firmware presets
~~~~~~~~~~~~~~~~

Each codec's ``fast``/``balanced``/``best_compression``/``minimal_memory`` preset, applied with :func:`hdiffpatch.recompress` to the uncompressed diff between the MicroPython v1.25.0 and v1.26.0 images of four boards (best of 3 runs, Apple M3 MacBook Pro). The *full image* row is the new image compressed on its own with ``LzmaConfig.best_compression()``, i.e. what shipping the whole image instead of a diff would cost. Regenerate with ``uv run python tools/benchmark_firmware.py``, which downloads the images on first use.

* A codec's ``window`` sets how much RAM its decoder needs on the device, but a bigger window doesn't always mean a smaller diff: tamp's size bottoms out at ``window=12`` on these images and grows past it, while each step roughly doubles compression time. The presets are tuned so you don't have to pick one.
* ``brotli`` ``best_compression`` takes ~2.3 s on the ~1.7 MB images, about 100x its ``balanced`` preset, for diffs ~3 points smaller.
* ``zstd`` and ``brotli`` ``fast``/``balanced`` and ``lz4`` recompress in single-digit milliseconds; the ``lzma`` family gives the smallest diffs at every preset.

Diff size (% of new image):

==========  ================  ========================  ===========================  =====================  ===============
codec       preset            ESP32_GENERIC (1,694 KB)  ESP32_GENERIC_S3 (1,692 KB)  RPI_PICO_W (1,709 KB)  PYBV11 (359 KB)
==========  ================  ========================  ===========================  =====================  ===============
none                       —                     59.4%                        60.3%                  11.7%            22.8%
zlib                    fast                     44.3%                        45.2%                   6.1%            12.1%
zlib                balanced                     43.5%                        44.4%                   5.8%            11.5%
zlib        best_compression                     43.4%                        44.3%                   5.8%            11.5%
zlib          minimal_memory                     44.8%                        45.8%                   6.0%            11.7%
lzma                    fast                     42.1%                        42.9%                   5.6%            11.1%
lzma                balanced                     40.4%                        41.1%                   5.4%            10.6%
lzma        best_compression                     40.4%                        41.1%                   5.3%            10.6%
lzma          minimal_memory                     41.1%                        42.0%                   5.4%            10.6%
lzma2                   fast                     42.1%                        42.9%                   5.6%            11.1%
lzma2               balanced                     40.4%                        41.2%                   5.4%            10.6%
lzma2       best_compression                     40.4%                        41.1%                   5.3%            10.6%
lzma2         minimal_memory                     41.2%                        42.0%                   5.4%            10.6%
xz                      fast                     42.1%                        42.9%                   5.6%            11.1%
xz                  balanced                     40.4%                        41.2%                   5.4%            10.7%
xz          best_compression                     40.4%                        41.2%                   5.4%            10.7%
xz            minimal_memory                     41.2%                        42.0%                   5.4%            10.7%
zstd                    fast                     48.2%                        49.2%                   6.4%            12.6%
zstd                balanced                     44.9%                        46.0%                   6.0%            11.7%
zstd        best_compression                     42.2%                        43.0%                   5.6%            11.1%
zstd          minimal_memory                     49.2%                        50.3%                   6.9%            13.2%
bzip2                   fast                     44.8%                        45.9%                   5.9%            11.6%
bzip2               balanced                     44.6%                        45.7%                   5.9%            11.6%
bzip2       best_compression                     44.4%                        45.5%                   5.9%            11.6%
bzip2         minimal_memory                     44.8%                        45.9%                   5.9%            11.6%
brotli                  fast                     46.6%                        47.7%                   6.3%            12.6%
brotli              balanced                     43.7%                        44.6%                   5.9%            11.6%
brotli      best_compression                     40.9%                        41.7%                   5.4%            10.6%
brotli        minimal_memory                     45.4%                        46.6%                   6.0%            11.8%
lzham                   fast                     42.5%                        43.3%                   5.8%            11.6%
lzham               balanced                     41.7%                        42.5%                   5.6%            11.3%
lzham       best_compression                     41.4%                        42.2%                   5.6%            11.2%
lzham         minimal_memory                     42.1%                        42.9%                   5.6%            11.2%
lz4                     fast                     58.9%                        60.0%                   9.9%            19.8%
lz4                 balanced                     57.8%                        58.8%                   8.9%            18.3%
lz4         best_compression                     53.9%                        55.0%                   7.9%            16.1%
lz4           minimal_memory                     53.9%                        55.0%                   7.9%            16.1%
lz4hc                   fast                     49.8%                        51.0%                   7.2%            14.6%
lz4hc               balanced                     49.4%                        50.6%                   7.1%            14.3%
lz4hc       best_compression                     49.4%                        50.6%                   7.1%            14.2%
lz4hc         minimal_memory                     49.4%                        50.6%                   7.1%            14.2%
tuz                     fast                     45.1%                        46.0%                   6.0%            11.9%
tuz                 balanced                     44.7%                        45.6%                   6.0%            11.9%
tuz         best_compression                     44.4%                        45.3%                   6.0%            11.9%
tuz           minimal_memory                     47.6%                        48.7%                   6.3%            12.4%
tamp                    fast                     49.2%                        50.4%                   6.7%            13.0%
tamp                balanced                     47.6%                        48.7%                   6.5%            12.8%
tamp        best_compression                     47.0%                        48.1%                   6.5%            13.0%
tamp          minimal_memory                     49.2%                        50.4%                   6.7%            13.0%
full image         lzma best                     59.2%                        59.1%                  32.4%            60.8%
==========  ================  ========================  ===========================  =====================  ===============

Recompress time (ms):

======  ================  ========================  ===========================  =====================  ===============
codec   preset            ESP32_GENERIC (1,694 KB)  ESP32_GENERIC_S3 (1,692 KB)  RPI_PICO_W (1,709 KB)  PYBV11 (359 KB)
======  ================  ========================  ===========================  =====================  ===============
zlib                fast                      11.6                         11.7                    1.9              0.8
zlib            balanced                      34.6                         34.2                    5.0              2.2
zlib    best_compression                      48.7                         43.4                    9.7              6.1
zlib      minimal_memory                      12.7                         12.6                    2.4              1.2
lzma                fast                      34.2                         34.7                    5.1              2.3
lzma            balanced                      64.3                         64.6                   14.7              8.2
lzma    best_compression                      65.6                         65.8                   16.2              8.9
lzma      minimal_memory                      60.2                         60.0                   14.4              7.8
lzma2               fast                      34.9                         35.4                    5.4              2.8
lzma2           balanced                      64.8                         65.0                   14.8              8.1
lzma2   best_compression                      66.0                         66.3                   16.2              8.7
lzma2     minimal_memory                      60.7                         60.3                   14.6              7.9
xz                  fast                      34.8                         35.1                    5.3              2.5
xz              balanced                      64.7                         65.2                   14.9              8.4
xz      best_compression                      66.5                         66.8                   17.0              9.4
xz        minimal_memory                      60.9                         60.4                   14.6              7.8
zstd                fast                       1.5                          1.5                    0.3              0.2
zstd            balanced                       8.2                          8.3                    1.6              0.8
zstd    best_compression                      76.1                         73.6                   30.0             10.4
zstd      minimal_memory                       6.2                          6.2                    1.1              0.4
bzip2               fast                      59.2                         59.3                   13.1              6.8
bzip2           balanced                      57.9                         58.1                   13.3              7.3
bzip2   best_compression                      58.0                         58.2                   13.4              7.3
bzip2     minimal_memory                      59.2                         59.1                   13.0              7.0
brotli              fast                       4.3                          4.3                    0.7              0.3
brotli          balanced                      21.5                         21.8                    3.3              1.6
brotli  best_compression                    2429.9                       2497.9                  288.2             95.0
brotli    minimal_memory                      12.9                         13.1                    2.6              1.4
lzham               fast                      71.5                         72.6                   13.5              6.4
lzham           balanced                      93.2                         96.9                   21.2             10.3
lzham   best_compression                     161.6                        154.2                  138.7             47.3
lzham     minimal_memory                      88.7                         87.8                   25.3             12.4
lz4                 fast                       0.3                          0.3                    0.0              0.0
lz4             balanced                       0.5                          0.5                    0.1              0.0
lz4     best_compression                       1.0                          1.0                    0.3              0.1
lz4       minimal_memory                       1.0                          1.0                    0.3              0.1
lz4hc               fast                      13.8                         14.2                    1.4              0.5
lz4hc           balanced                      19.0                         18.5                    2.7              1.3
lz4hc   best_compression                      32.7                         30.3                    5.9              3.6
lz4hc     minimal_memory                      29.0                         27.3                    4.6              2.7
tuz                 fast                     125.4                        124.5                   25.7             12.2
tuz             balanced                     152.3                        153.6                   25.9             12.2
tuz     best_compression                     153.5                        155.0                   26.0             12.2
tuz       minimal_memory                     101.6                        100.3                   24.1             11.6
tamp                fast                      33.5                         34.2                    5.7              2.5
tamp            balanced                     111.3                        112.9                   18.7              8.3
tamp    best_compression                     322.3                        328.6                   52.2             23.3
tamp      minimal_memory                      34.1                         34.3                    5.6              2.5
======  ================  ========================  ===========================  =====================  ===============
