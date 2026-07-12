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

See the [documentation](https://hdiffpatch-python.readthedocs.io) for fine-grained compression configuration, diff recompression, and performance benchmarks.
