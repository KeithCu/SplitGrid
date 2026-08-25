# SplitGrid
# Copyright (c) 2026 KeithCu
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cython flatten accelerator vs pure-Python flatten parity.

Skipped when ``splitgrid.pack`` is not built. Default pytest still passes on the
pure-Python path.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

import splitgrid.codec as pc
from splitgrid.codec import (
    _flatten_grid_to_components,
    _verify_accelerator,
    host_pack_data,
)
from tests.payload_codec_test_support import (
    MIXED_LABEL_GRID,
    MIXED_WITH_ZIP,
    NUMERIC_4X4,
    NUMERIC_AT_THRESHOLD,
)
from tests.serialization_ab_support import (
    all_codec_ab_cases,
    assert_cython_vs_python_flatten_parity,
    cython_accelerator_context,
    prepare_grid,
)


def _cython_available() -> bool:
    return pc.fast_flatten_grid_2d is not None and pc.fast_flatten_grid_1d is not None


pytestmark = pytest.mark.skipif(not _cython_available(), reason="Cython splitgrid.pack extension not built")


def _nan_equal_buffers(a, b) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if math.isnan(x) and math.isnan(y):
            continue
        if x != y:
            return False
    return True


PARITY_GRIDS: list[tuple[str, list[Any] | list[list[Any]]]] = [
    ("numeric_4x4", NUMERIC_4X4),
    ("mixed_label", MIXED_LABEL_GRID),
    ("mixed_zip", MIXED_WITH_ZIP),
    ("numeric_at_threshold", NUMERIC_AT_THRESHOLD),
    ("1d_numeric", [1.5, 2.5, 3.5, 4.5]),
    ("1d_mixed", [1.5, "banana", None, 4.5]),
    ("none_holes", [[1.0, None, 3.0], [4.0, 5.0, 6.0]]),
    ("bools", [[True, False], [False, True]]),
    ("ints", [[100, 541], [101, 547]]),
]


@pytest.mark.parametrize("label,grid", PARITY_GRIDS, ids=[x[0] for x in PARITY_GRIDS])
def test_cython_python_flatten_components(label: str, grid: list[Any] | list[list[Any]]) -> None:
    """Direct flatten: Cython and stdlib produce equivalent buffer/strings/kinds/shape."""
    with cython_accelerator_context(enabled=True):
        buf_c, strings_c, kinds_c, shape_c = _flatten_grid_to_components(grid)
    with cython_accelerator_context(enabled=False):
        buf_p, strings_p, kinds_p, shape_p = _flatten_grid_to_components(grid)

    assert shape_c == shape_p, label
    assert kinds_c == kinds_p, label
    assert strings_c == strings_p, label
    assert _nan_equal_buffers(buf_c, buf_p), label


@pytest.mark.parametrize("label,grid", PARITY_GRIDS, ids=[x[0] for x in PARITY_GRIDS])
def test_cython_python_host_pack_envelope(label: str, grid: list[Any] | list[list[Any]]) -> None:
    """Packed split_grid envelopes must be byte-identical across flatten backends."""
    assert_cython_vs_python_flatten_parity(grid, label=label)


@pytest.mark.parametrize("case", all_codec_ab_cases(), ids=lambda c: c.id)
def test_cython_python_named_fixture_grids(case) -> None:
    grid = prepare_grid(case)
    if not grid:
        pytest.skip("empty grid")
    assert_cython_vs_python_flatten_parity(grid, label=case.id)


def test_cython_canary_matches_loader() -> None:
    assert _verify_accelerator(pc.fast_flatten_grid_2d, pc.fast_flatten_grid_1d) is True


def test_host_pack_falls_back_when_cython_disabled() -> None:
    grid = [[1.0, "x"], [2.0, "y"]]
    with cython_accelerator_context(enabled=False):
        assert pc.fast_flatten_grid_2d is None
        wire = host_pack_data(grid, force="always")
    assert wire["strings"] == {1: "x", 3: "y"}
    assert wire["shape"] == [2, 2]
