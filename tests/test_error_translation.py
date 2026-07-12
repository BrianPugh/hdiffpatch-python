"""Tests that C++ exceptions from the HDiffPatch core surface as HDiffPatchError."""

import random

import hdiffpatch


def test_cpp_exceptions_surface_as_hdiffpatch_error():
    """A C++ throw from the core must never escape as a bare RuntimeError.

    Diffing two large seeded-random buffers with tamp compression currently
    triggers a ``std::runtime_error`` inside the HDiffPatch C++ core. Cython's
    bare ``except +`` would translate that into a builtin ``RuntimeError``,
    violating the package contract that all diff/patch/compression failures
    raise ``HDiffPatchError``.

    This test is written to pass in both worlds: if the underlying tamp bug is
    later fixed and the diff succeeds, the round-trip must validate; otherwise
    the only acceptable failure is ``HDiffPatchError``. Any other exception
    (notably a bare ``RuntimeError``) escaping is a failure.
    """
    rng = random.Random(42)  # noqa: S311
    old = rng.randbytes(1_350_000)
    new = rng.randbytes(1_350_000)
    try:
        patch = hdiffpatch.diff(old, new, compression=hdiffpatch.TampConfig(window=10))
    except hdiffpatch.HDiffPatchError:
        pass  # translated C++ error: acceptable
    else:
        assert hdiffpatch.apply(old, patch) == new
