"""Tests for GIL release and thread-safety of diff/apply.

diff() and apply() release the GIL around the core C/C++ calls, so
concurrent calls from multiple threads must run correctly and actually
overlap instead of serializing behind the GIL.
"""

import concurrent.futures
import threading

import pytest

import hdiffpatch


@pytest.fixture
def firmware_like_data():
    """Generate moderately large binary data pairs for concurrency tests."""
    old = bytes(range(256)) * 400
    new = old[:40000] + b"inserted section" * 64 + old[40000:] + b"\x00" * 1024
    return {"old": old, "new": new}


@pytest.mark.parametrize("compression", ["none", "zlib", "zstd", "tamp"])
def test_concurrent_diff_correctness(firmware_like_data, compression):
    """Test that concurrent diff() calls from many threads all round-trip."""
    old = firmware_like_data["old"]
    new = firmware_like_data["new"]

    def worker(_):
        diff_data = hdiffpatch.diff(old, new, compression=compression)
        return hdiffpatch.apply(old, diff_data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(worker, range(16)))

    assert all(result == new for result in results)


def test_diff_releases_gil():
    """Test that another Python thread makes progress while diff() runs."""
    # Large enough that the diff itself takes a macroscopic amount of time
    old = bytes(range(256)) * 8192  # 2 MiB
    new = old[: len(old) // 2] + b"wedge" * 1000 + old[len(old) // 2 :]

    counter = 0
    stop = threading.Event()

    def count():
        nonlocal counter
        while not stop.is_set():
            counter += 1

    thread = threading.Thread(target=count)
    thread.start()
    try:
        before = counter
        hdiffpatch.diff(old, new, compression="lzma", validate=False)
        during = counter - before
    finally:
        stop.set()
        thread.join()

    # With the GIL held for the whole C call, the counter thread is frozen for
    # the duration of diff() (a single bytecode); released, it runs throughout.
    assert during > 1000
