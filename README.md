<div align="center">

![Python compat](https://img.shields.io/badge/%3E=python-3.10-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/hdiffpatch.svg)](https://pypi.org/project/hdiffpatch/)
[![ReadTheDocs](https://readthedocs.org/projects/hdiffpatch-python/badge/?version=latest)](https://hdiffpatch-python.readthedocs.io)
[![GHA Status](https://github.com/BrianPugh/hdiffpatch-python/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/BrianPugh/hdiffpatch-python/actions?query=workflow%3Atests)

</div>

---

**Documentation:** https://hdiffpatch-python.readthedocs.io

**Source Code:** https://github.com/BrianPugh/hdiffpatch-python

---

**hdiffpatch-python** is a Python wrapper around the [HDiffPatch](https://github.com/sisong/HDiffPatch) C++ library, providing fast binary diff and patch operations with a variety of compression options.

# Installation

hdiffpatch requires Python >=3.10 and can be installed via:

```console
pip install hdiffpatch
```

# Quick Start

**hdiffpatch** primarily provides 3 simple functions:

* `diff` for creating a patch.
* `apply` for applying a patch.
* `recompress` for changing an existing patch's compression.

```python
import hdiffpatch

old = b"The quick brown fox jumps over the lazy dog."
new = b"The quick brown fox leaps over the sleepy dog."

# Create a compressed patch that transforms old -> new.
patch = hdiffpatch.diff(old, new, compression="zstd")

# Later (e.g. on another device), reconstruct new from old + patch.
assert hdiffpatch.apply(old, patch) == new

# Re-encode an existing patch with a different compression algorithm.
patch_lzma = hdiffpatch.recompress(patch, compression="lzma")
assert hdiffpatch.apply(old, patch_lzma) == new
```

A patch is typically much smaller than the new data itself, making **hdiffpatch** ideal for bandwidth-constrained applications like over-the-air firmware updates.

## Lite-format diffs for HPatchLite

For extremely memory-constrained devices, `diff_lite` produces the compact "lite" format consumed by HDiffPatch's tiny on-device applier, [HPatchLite](https://github.com/sisong/HPatchLite) (`hpatch_lite_patch`). Only codecs the device can decode are accepted — `"none"`, `"zlib"`, `"lzma"`, and `"tamp"` (the last via a device-side decompressor plugin); `"zstd"`, `"lzma2"`, and `"bzip2"` are rejected with a clear error.

```python
import hdiffpatch

lite = hdiffpatch.diff_lite(old, new, compression="lzma")
restored = hdiffpatch.apply_lite(old, lite)   # == new
```

`apply_lite` is the lite-format counterpart of `apply`: it drives the vendored HPatchLite applier (the same code path a device runs) to reconstruct the new data. The codec is auto-detected from the self-describing lite header, so `apply_lite` takes no `compression` argument.

Lite diffs are **not** interchangeable with `diff`/`apply` — they can only be applied by an HPatchLite-family patcher (`apply_lite` here, or an HPatchLite build on the target device), and the standard `apply` rejects them.

See the [documentation](https://hdiffpatch-python.readthedocs.io) for fine-grained compression configuration, diff recompression, and performance benchmarks.
