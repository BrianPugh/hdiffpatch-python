"""Benchmark every codec preset on real MicroPython firmware updates for several boards.

Downloads consecutive release images from micropython.org (cached in
~/.cache/hdiffpatch-benchmark), diffs each pair once, then recompresses the
uncompressed diff with every codec's ``fast``/``balanced``/``best_compression``/
``minimal_memory`` preset. Prints RST tables of diff size (as % of the new
image) and recompress time.

Usage: uv run python tools/benchmark_firmware.py
"""

import urllib.request
from pathlib import Path

from benchmark import best_of, print_rst_table

import hdiffpatch

CACHE = Path.home() / ".cache" / "hdiffpatch-benchmark"
FIRMWARE_URL = "https://micropython.org/resources/firmware/{board}-{release}.{ext}"
OLD_RELEASE = "20250415-v1.25.0"
NEW_RELEASE = "20250809-v1.26.0"
BOARDS = [
    ("ESP32_GENERIC", "bin"),
    ("ESP32_GENERIC_S3", "bin"),
    ("RPI_PICO_W", "uf2"),
    ("PYBV11", "dfu"),
]
CONFIGS = [
    hdiffpatch.ZlibConfig,
    hdiffpatch.LzmaConfig,
    hdiffpatch.Lzma2Config,
    hdiffpatch.XzConfig,
    hdiffpatch.ZStdConfig,
    hdiffpatch.BZip2Config,
    hdiffpatch.BrotliConfig,
    hdiffpatch.LzhamConfig,
    hdiffpatch.Lz4Config,
    hdiffpatch.Lz4HCConfig,
    hdiffpatch.TuzConfig,
    hdiffpatch.TampConfig,
]
PRESETS = ("fast", "balanced", "best_compression", "minimal_memory")
REPEATS = 3


def fetch(board: str, release: str, ext: str) -> bytes:
    """Return a MicroPython firmware image, downloading it on first use.

    Parameters
    ----------
    board : str
        MicroPython board name.
    release : str
        ``<YYYYMMDD>-v<version>`` release tag as used in firmware filenames.
    ext : str
        Image file extension for this board.

    Returns
    -------
    bytes
        The firmware image.
    """
    path = CACHE / f"{board}-{release}.{ext}"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        url = FIRMWARE_URL.format(board=board, release=release, ext=ext)
        print(f"downloading {url}")
        with urllib.request.urlopen(url) as response:  # noqa: S310
            path.write_bytes(response.read())
    return path.read_bytes()


def main() -> None:
    """Run the benchmarks and print the RST tables."""
    images = {board: (fetch(board, OLD_RELEASE, ext), fetch(board, NEW_RELEASE, ext)) for board, ext in BOARDS}
    columns = ("codec", "preset", *(f"{board} ({len(new) / 1024:,.0f} KB)" for board, (_, new) in images.items()))

    size_rows: list[tuple[str, ...]] = []
    time_rows: list[tuple[str, ...]] = []
    bases = {
        board: hdiffpatch.diff(old, new, compression="none", validate=False) for board, (old, new) in images.items()
    }
    size_rows.append(("none", "—", *(f"{100 * len(bases[b]) / len(images[b][1]):.1f}%" for b in images)))

    for config_cls in CONFIGS:
        codec = config_cls.__name__.removesuffix("Config").lower()
        for preset in PRESETS:
            config = getattr(config_cls, preset)()
            sizes: list[str] = []
            times: list[str] = []
            for board, (_, new) in images.items():
                diff_data = hdiffpatch.recompress(bases[board], compression=config)
                sizes.append(f"{100 * len(diff_data) / len(new):.1f}%")
                t = best_of(lambda b=bases[board], c=config: hdiffpatch.recompress(b, compression=c), REPEATS)
                times.append(f"{t * 1000:.1f}")
            size_rows.append((codec, preset, *sizes))
            time_rows.append((codec, preset, *times))

    full_image = hdiffpatch.LzmaConfig.best_compression()
    size_rows.append(
        (
            "full image",
            "lzma best",
            *(
                f"{100 * len(hdiffpatch.diff(b'', new, compression=full_image)) / len(new):.1f}%"
                for _, new in images.values()
            ),
        )
    )

    print(f"{OLD_RELEASE} -> {NEW_RELEASE}, best of {REPEATS} runs")
    print()
    print("Diff size (% of new image):")
    print()
    print_rst_table(columns, size_rows)
    print("Recompress time (ms):")
    print()
    print_rst_table(columns, time_rows)


if __name__ == "__main__":
    main()
