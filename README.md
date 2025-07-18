**hdiffpatch-python** is a Python wrapper around the [HDiffPatch](https://github.com/sisong/HDiffPatch) C++ library, providing binary diff and patch operations with compression support.

<div align="center">

![Python compat](https://img.shields.io/badge/%3E=python-3.9-blue.svg)
[![PyPi](https://img.shields.io/pypi/v/hdiffpatch-python.svg)](https://pypi.python.org/pypi/hdiffpatch-python)
[![GHA Status](https://github.com/BrianPugh/hdiffpatch-python/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/BrianPugh/hdiffpatch-python/actions?query=workflow%3Atests)
[![Coverage](https://codecov.io/github/BrianPugh/hdiffpatch-python/coverage.svg?branch=main)](https://codecov.io/github/BrianPugh/hdiffpatch-python?branch=main)

</div>

## Installation

**hdiffpatch** requires Python `>=3.9` and can be installed via:

```bash
pip install hdiffpatch
```

For development installation:

```bash
git clone https://github.com/BrianPugh/hdiffpatch-python.git
cd hdiffpatch-python
uv sync
uv run python rebuild.py  # Build Cython extensions
```

## Quick Start

**hdiffpatch** primarily provides 2 simple functions:

* `diff` for creating a patch.
* `apply` for applying a patch.

### Basic Usage

```python
import hdiffpatch

# Create binary data
old_data = b"Hello, world!"
new_data = b"Hello, HDiffPatch!"

# Create a diff
diff = hdiffpatch.diff(old_data, new_data)

# Apply the diff
result = hdiffpatch.apply(old_data, diff)
assert result == new_data
```

### With Simple Compression

```python
import hdiffpatch

old_data = b"Large binary data..." * 1000
new_data = b"Modified binary data..." * 1000

# Create a compressed diff
diff = hdiffpatch.diff(old_data, new_data, compression="zlib")

# Apply patch
result = hdiffpatch.apply(old_data, diff)
assert result == new_data
```

### With Advanced Compression Configuration

```python
import hdiffpatch

old_data = b"Large binary data..." * 1000
new_data = b"Modified binary data..." * 1000

# Use configuration classes for fine-grained control
config = hdiffpatch.ZlibConfig(level=9, window=12)

diff = hdiffpatch.diff(old_data, new_data, compression=config)
result = hdiffpatch.apply(old_data, diff)
assert result == new_data
```

### Recompressing Diffs

```python
import hdiffpatch

old_data = b"Large binary data..." * 1000
new_data = b"Modified binary data..." * 1000

# Create a diff with zlib compression
diff_zlib = hdiffpatch.diff(old_data, new_data, compression="zlib")

# Recompress the same diff with zstd
diff_zstd = hdiffpatch.recompress(diff_zlib, compression="zstd")

# Remove compression entirely
diff_uncompressed = hdiffpatch.recompress(diff_zlib, compression="none")

# Both diffs produce the same result when applied
result1 = hdiffpatch.apply(old_data, diff_zlib)
result2 = hdiffpatch.apply(old_data, diff_zstd)
assert result1 == result2 == new_data
```

## API Reference

### Core Functions

```python
def diff(old_data, new_data, compression="none", *, validate=True) -> bytes
```

Create a binary diff between two byte sequences.

**Parameters:**

* `old_data` (bytes): Original data.
* `new_data` (bytes): Modified data.
* `compression` (str or config object): Compression type as string (`"none"`, `"zlib"`, `"lzma"`, `"lzma2"`, `"zstd"`, `"bzip2"`, `"tamp"`) or a compression configuration object.
* `validate` (bool): Test that the patch successfully converts `old_data` to `new_data`. This is a computationally inexpensive operation. Defaults to `True`.

**Returns:** `bytes` - Binary diff data that can be used with `apply()` and `old_data` to generate `new_data`.

---

```python
def apply(old_data, diff_data) -> bytes
```

Apply a binary patch to reconstruct new data.

**Parameters:**

* `old_data` (bytes): Original data.
* `diff_data` (bytes): Patch data from `diff()`.

**Returns:** `bytes` - Reconstructed data. The `new_data` that was passed to `diff()`.

---

```python
def recompress(diff_data, compression=None) -> bytes
```

Recompress a diff with a different compression algorithm.

**Parameters:**

* `diff_data` (bytes): The diff data to recompress.
* `compression` (str or config object, optional): Target compression type as string (`"none"`, `"zlib"`, `"lzma"`, `"lzma2"`, `"zstd"`, `"bzip2"`, `"tamp"`) or a compression configuration object. If None, removes compression.

**Returns:** `bytes` - The recompressed diff data

### Compression Configuration

For advanced compression control, **hdiffpatch** provides configuration classes for each compression algorithm:

#### ZStdConfig

Fine-grained control over Zstandard compression:

```python
# Basic configuration
config = hdiffpatch.ZStdConfig(level=15, window=20, workers=2)

# Preset configurations
config = hdiffpatch.ZStdConfig.fast()             # Optimized for speed
config = hdiffpatch.ZStdConfig.balanced()         # Balanced speed/compression
config = hdiffpatch.ZStdConfig.best_compression() # Maximum compression
config = hdiffpatch.ZStdConfig.minimal_memory()   # Minimal memory usage

# Use with diff
diff = hdiffpatch.diff(old_data, new_data, compression=config)
```

**Parameters:**

* `level` (1-22): Compression level, higher = better compression
* `window` (10-27): Window size as log2, larger = better compression
* `workers` (0-200): Number of threads, 0 = single-threaded

#### ZlibConfig

Fine-grained control over zlib compression:

```python
# Basic configuration
config = hdiffpatch.ZlibConfig(
    level=9,
    memory_level=8,
    window=15,
    strategy=hdiffpatch.ZlibStrategy.DEFAULT
)

# Preset configurations
config = hdiffpatch.ZlibConfig.fast()
config = hdiffpatch.ZlibConfig.balanced()
config = hdiffpatch.ZlibConfig.best_compression()
config = hdiffpatch.ZlibConfig.minimal_memory()
config = hdiffpatch.ZlibConfig.png_optimized()    # Optimized for PNG-like data
```

**Parameters:**

* `level` (0-9): Compression level
* `memory_level` (1-9): Memory usage level
* `window` (9-15): Window size as power of 2
* `strategy`: Compression strategy (`DEFAULT`, `FILTERED`, `HUFFMAN_ONLY`, `RLE`, `FIXED`)

#### LzmaConfig and Lzma2Config

Fine-grained control over LZMA compression:

```python
# LZMA configuration
config = hdiffpatch.LzmaConfig(level=9, window=23, thread_num=1)

# LZMA2 configuration (supports more threads)
config = hdiffpatch.Lzma2Config(level=9, window=23, thread_num=4)

# Preset configurations available for both
config = hdiffpatch.LzmaConfig.fast()
config = hdiffpatch.LzmaConfig.balanced()
config = hdiffpatch.LzmaConfig.best_compression()
config = hdiffpatch.LzmaConfig.minimal_memory()
```

**Parameters:**

* `level` (0-9): Compression level
* `window` (12-30): Window size as log2
* `thread_num`: Number of threads (1-2 for LZMA, 1-64 for LZMA2)

#### BZip2Config

Fine-grained control over bzip2 compression:

```python
config = hdiffpatch.BZip2Config(level=9, work_factor=30)

# Preset configurations
config = hdiffpatch.BZip2Config.fast()
config = hdiffpatch.BZip2Config.balanced()
config = hdiffpatch.BZip2Config.best_compression()
config = hdiffpatch.BZip2Config.minimal_memory()
```

**Parameters:**

* `level` (1-9): Compression level
* `work_factor` (0-250): Work factor for worst-case scenarios

#### TampConfig

Fine-grained control over [Tamp](https://github.com/BrianPugh/tamp) compression (embedded-friendly):

```python
config = hdiffpatch.TampConfig(window=10)

# Preset configurations
config = hdiffpatch.TampConfig.fast()
config = hdiffpatch.TampConfig.balanced()
config = hdiffpatch.TampConfig.best_compression()
config = hdiffpatch.TampConfig.minimal_memory()
```

**Parameters:**

* `window` (8-15): Window size as power of 2

### Exceptions

```python
hdiffpatch.HDiffPatchError
```

## Compression Performance

Different compression algorithms offer trade-offs between compression ratio and speed:

* **`zlib`**: Good balance of speed and compression. Very common.
* **`zstd`**: Fast compression with good ratios.
* **`lzma`/`lzma2`**: Very high compression ratios, slower.
* **`bzip2`**: Good compression, moderate speed
* **`tamp`**: Embedded-friendly compression, minimal memory usage.

### Basic Compression Comparison

```python
import hdiffpatch

# Large repetitive data
old_data = b"A" * 10000 + b"B" * 10000
new_data = b"A" * 10000 + b"C" * 10000

# Compare compression effectiveness
for compression in ["none", "zlib", "zstd", "lzma", "bzip2", "tamp"]:
    diff = hdiffpatch.diff(old_data, new_data, compression=compression)
    print(f"{compression}: {len(diff)} bytes")
```

### Advanced Configuration Comparison

```python
import hdiffpatch

# Compare different configuration approaches
configs = {
    "zstd_fast": hdiffpatch.ZStdConfig.fast(),
    "zstd_best": hdiffpatch.ZStdConfig.best_compression(),
    "zlib_balanced": hdiffpatch.ZlibConfig.balanced(),
    "lzma2_custom": hdiffpatch.Lzma2Config(level=6, window=20, thread_num=4),
}

for name, config in configs.items():
    diff = hdiffpatch.diff(old_data, new_data, compression=config)
    print(f"{name}: {len(diff)} bytes")
```

### Real-World Example: MicroPython Firmware

Here's a comprehensive comparison using actual MicroPython firmware files with a 12-bit window size (4096 bytes). This window size was chosen because it is typically a good trade-off between memory-usage and compression-performance for embedded targets.

* [RPI_PICO-20241129-v1.24.1.uf2](https://micropython.org/resources/firmware/RPI_PICO-20241129-v1.24.1.uf2): 651 KB
* [RPI_PICO-20250415-v1.25.0.uf2](https://micropython.org/resources/firmware/RPI_PICO-20250415-v1.25.0.uf2): 652 KB

Since we're using compression for the diff, a natural question would be: "If I'm adding a decompression library to my target project, then how much smaller is the patch compared to just compressing the firmware?"
To answer this question, we compare the size of the compressed patch to the compressed firmware.

| Algorithm | Size (HDiffPatch) | Size (firmware) | Improvement |
|-----------|-------------------|-----------------|-------------|
| none      |          209.7 KB |        652.0 KB | 3.11x |
| tamp      |          143.1 KB |        322.8 KB | 2.26x |
| zstd      |          133.4 KB |        277.6 KB | 2.08x |
| zlib      |          125.5 KB |        251.8 KB | 2.01x |
| bzip2     |          128.6 KB |        246.2 KB | 1.91x |
| lzma      |          116.9 KB |        222.7 KB | 1.91x |

In this example, using **hdiffpatch** resulted in a ~3x smaller update when compared to a naive uncompressed firmware update, and ~2x smaller when comparing against an equivalently-compressed firmware update.

To reproduce these results:

```bash
uv run python tools/micropython-binary-demo.py
```
