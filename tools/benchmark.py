"""Benchmark diff/apply/recompress speed and size ratios on the firmware test binaries.

Regenerates the numbers in docs/source/Performance.rst: the output is the RST
simple table used there, followed by the validate=True overhead measurement.

Usage: uv run python tools/benchmark.py
"""

import time
from collections.abc import Callable
from pathlib import Path

import hdiffpatch
from hdiffpatch import CompressionType

BINARIES = Path(__file__).parent.parent / "tests" / "binaries"
COMPRESSIONS: list[CompressionType] = ["none", "zlib", "lzma", "zstd", "bzip2", "tamp"]
REPEATS = 5

COLUMNS = ("compression", "diff (ms)", "apply (ms)", "recompress (ms)", "diff size", "% of new file")


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


def main() -> None:
    """Run the benchmark and print the RST table used in docs/source/Performance.rst."""
    old = (BINARIES / "RPI_PICO-20241129-v1.24.1.uf2").read_bytes()
    new = (BINARIES / "RPI_PICO-20250415-v1.25.0.uf2").read_bytes()
    print(f"old={len(old):,} bytes  new={len(new):,} bytes  best of {REPEATS} runs")
    print()

    base = hdiffpatch.diff(old, new, compression="none", validate=False)

    rows: list[tuple[str, ...]] = [COLUMNS]
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

    widths = [max(len(row[i]) for row in rows) for i in range(len(COLUMNS))]
    rule = "  ".join("=" * width for width in widths)
    print(rule)
    print("  ".join(name.ljust(width) for name, width in zip(COLUMNS, widths)))
    print(rule)
    for row in rows[1:]:
        cells = [row[0].ljust(widths[0])] + [cell.rjust(width) for cell, width in zip(row[1:], widths[1:])]
        print("  ".join(cells).rstrip())
    print(rule)
    print()

    t_no_validate = best_of(lambda: hdiffpatch.diff(old, new, compression=None, validate=False))
    t_validate = best_of(lambda: hdiffpatch.diff(old, new, compression=None, validate=True))
    overhead = 100 * (t_validate - t_no_validate) / t_no_validate
    print(
        f"validate=True: {t_validate * 1000:.1f} ms vs validate=False: {t_no_validate * 1000:.1f} ms "
        f"({overhead:.0f}% overhead)"
    )


if __name__ == "__main__":
    main()
