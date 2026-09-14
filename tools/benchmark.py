"""Benchmark diff/apply/recompress speed and size ratios on the firmware test binaries.

Regenerates the numbers in docs/source/Performance.rst: the standard-format RST
table, the validate=True overhead measurement, and a standard-vs-lite comparison
for the codecs HPatchLite can decode.

Usage: uv run python tools/benchmark.py
"""

import time
from collections.abc import Callable, Sequence
from pathlib import Path

import hdiffpatch
from hdiffpatch import CompressionType

BINARIES = Path(__file__).parent.parent / "tests" / "binaries"
COMPRESSIONS: list[CompressionType] = ["none", "zlib", "lzma", "zstd", "bzip2", "tamp"]
# Codecs HPatchLite can decode; the only ones diff_lite/apply_lite accept.
LITE_COMPRESSIONS: list[CompressionType] = ["none", "zlib", "lzma", "tamp"]
REPEATS = 5

COLUMNS = ("compression", "diff (ms)", "apply (ms)", "recompress (ms)", "diff size", "% of new file")
LITE_COLUMNS = (
    "compression",
    "std diff (ms)",
    "lite diff (ms)",
    "std apply (ms)",
    "lite apply (ms)",
    "std size",
    "lite size",
    "lite/std",
)


def best_of(fn: Callable[[], object], repeats: int = REPEATS) -> float:
    """Return the fastest wall-clock time of ``repeats`` runs of ``fn``, in seconds.

    Parameters
    ----------
    fn : Callable[[], object]
        Zero-argument callable to time.
    repeats : int
        Number of runs to sample.

    Returns
    -------
    float
        Best observed duration in seconds.
    """
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return min(times)


def print_rst_table(columns: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Print ``rows`` as an RST simple table under ``columns``.

    The first column is left-justified; the rest are right-justified.

    Parameters
    ----------
    columns : Sequence[str]
        Header cells.
    rows : Sequence[Sequence[str]]
        Body rows, each with one cell per column.
    """
    all_rows = [columns, *rows]
    widths = [max(len(row[i]) for row in all_rows) for i in range(len(columns))]
    rule = "  ".join("=" * width for width in widths)
    print(rule)
    print("  ".join(name.ljust(width) for name, width in zip(columns, widths)))
    print(rule)
    for row in rows:
        cells = [row[0].ljust(widths[0])] + [cell.rjust(width) for cell, width in zip(row[1:], widths[1:])]
        print("  ".join(cells).rstrip())
    print(rule)
    print()


def standard_table(old: bytes, new: bytes) -> None:
    """Print the standard-format diff/apply/recompress/size table."""
    base = hdiffpatch.diff(old, new, compression="none", validate=False)

    rows: list[tuple[str, ...]] = []
    for compression in COMPRESSIONS:
        diff_data = hdiffpatch.diff(old, new, compression=compression, validate=False)
        t_diff = best_of(lambda c=compression: hdiffpatch.diff(old, new, compression=c, validate=False))
        t_apply = best_of(lambda d=diff_data: hdiffpatch.apply(old, d))
        if compression == "none":
            t_recompress = "—"
        else:
            t_recompress = f"{best_of(lambda c=compression: hdiffpatch.recompress(base, compression=c)) * 1000:.1f}"
        rows.append(
            (
                compression,
                f"{t_diff * 1000:.1f}",
                f"{t_apply * 1000:.1f}",
                t_recompress,
                f"{len(diff_data):,}",
                f"{100 * len(diff_data) / len(new):.1f}%",
            )
        )
    print_rst_table(COLUMNS, rows)


def lite_table(old: bytes, new: bytes) -> None:
    """Print the standard-vs-lite comparison for the HPatchLite-decodable codecs.

    For each codec, times both formats' diff and apply and reports their output
    sizes plus the lite size as a percentage of the standard size (``lite/std``).
    ``recompress`` has no lite equivalent, so it is omitted here.
    """
    rows: list[tuple[str, ...]] = []
    for compression in LITE_COMPRESSIONS:
        std_diff = hdiffpatch.diff(old, new, compression=compression, validate=False)
        lite_diff = hdiffpatch.diff_lite(old, new, compression=compression, validate=False)
        t_std_diff = best_of(lambda c=compression: hdiffpatch.diff(old, new, compression=c, validate=False))
        t_lite_diff = best_of(lambda c=compression: hdiffpatch.diff_lite(old, new, compression=c, validate=False))
        t_std_apply = best_of(lambda d=std_diff: hdiffpatch.apply(old, d))
        t_lite_apply = best_of(lambda d=lite_diff: hdiffpatch.apply_lite(old, d))
        rows.append(
            (
                compression,
                f"{t_std_diff * 1000:.1f}",
                f"{t_lite_diff * 1000:.1f}",
                f"{t_std_apply * 1000:.1f}",
                f"{t_lite_apply * 1000:.1f}",
                f"{len(std_diff):,}",
                f"{len(lite_diff):,}",
                f"{100 * len(lite_diff) / len(std_diff):.1f}%",
            )
        )
    print_rst_table(LITE_COLUMNS, rows)


def main() -> None:
    """Run the benchmarks and print the RST tables used in docs/source/Performance.rst."""
    old = (BINARIES / "RPI_PICO-20241129-v1.24.1.uf2").read_bytes()
    new = (BINARIES / "RPI_PICO-20250415-v1.25.0.uf2").read_bytes()
    print(f"old={len(old):,} bytes  new={len(new):,} bytes  best of {REPEATS} runs")
    print()

    standard_table(old, new)

    print("Standard vs lite (HPatchLite-decodable codecs):")
    print()
    lite_table(old, new)

    t_no_validate = best_of(lambda: hdiffpatch.diff(old, new, compression=None, validate=False))
    t_validate = best_of(lambda: hdiffpatch.diff(old, new, compression=None, validate=True))
    overhead = 100 * (t_validate - t_no_validate) / t_no_validate
    print(
        f"validate=True: {t_validate * 1000:.1f} ms vs validate=False: {t_no_validate * 1000:.1f} ms "
        f"({overhead:.0f}% overhead)"
    )


if __name__ == "__main__":
    main()
