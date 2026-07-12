"""Regression tests for tamp compression on incompressible diff payloads.

High-entropy data expands under tamp's literal encoding (~1.125x), so a 32 KB
input chunk cannot fit into a same-sized output buffer. This exercises the
partial-consumption path of ``tamp_compressor_compress`` against HDiffPatch's
sequential-only ``TNewDataDiffStream``.
"""

import random

import pytest

import hdiffpatch


@pytest.mark.parametrize("window", [8, 10])
def test_diff_apply_roundtrip_incompressible(window):
    """Round-trip a large incompressible payload through tamp compression."""
    rng = random.Random(42)  # noqa: S311
    old = rng.randbytes(1_350_000)
    new = rng.randbytes(1_350_000)

    patch = hdiffpatch.diff(old, new, compression=hdiffpatch.TampConfig(window=window))
    assert hdiffpatch.apply(old, patch) == new
