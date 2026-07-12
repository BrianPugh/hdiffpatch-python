Performance
===========

* :func:`hdiffpatch.diff` is the expensive operation: it searches for matches between ``old_data`` and ``new_data``, and its cost grows with input size. :func:`hdiffpatch.apply` is comparatively cheap.
* ``validate=True`` (the default for :func:`hdiffpatch.diff`) round-trips the freshly created diff through :func:`hdiffpatch.apply` and compares the result. This is very cheap relative to creating the diff, so it is generally worth leaving enabled.
* :func:`hdiffpatch.recompress` re-encodes an existing diff without redoing the diff computation. To produce the same diff with several compression algorithms, create it once and recompress it per target instead of calling :func:`hdiffpatch.diff` repeatedly:

.. code-block:: python

   base = hdiffpatch.diff(old_data, new_data, compression="none")
   diff_zstd = hdiffpatch.recompress(base, compression="zstd")
   diff_lzma = hdiffpatch.recompress(base, compression="lzma")
