Performance
===========

* :func:`hdiffpatch.diff` is the expensive operation: it searches for matches between ``old_data`` and ``new_data``, and its cost grows with input size. :func:`hdiffpatch.apply` is comparatively cheap (10-60x faster in the benchmark below).

  * ``validate=True`` (the default) round-trips the freshly created diff through :func:`hdiffpatch.apply` and verifies that it reproduces ``new_data`` exactly. This adds only a few percent on top of creating the diff, and catches any data-compromising bug in the diff/compression stack before a corrupt diff is stored or shipped — leave it enabled.

* :func:`hdiffpatch.recompress` re-encodes an existing diff without redoing the expensive diff computation, paying only for the recompression itself. To produce the same diff with several compression algorithms, create it once and recompress it per target instead of calling :func:`hdiffpatch.diff` repeatedly:

.. code-block:: python

   base = hdiffpatch.diff(old_data, new_data, compression="none")
   diff_zstd = hdiffpatch.recompress(base, compression="zstd")
   diff_lzma = hdiffpatch.recompress(base, compression="lzma")

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
