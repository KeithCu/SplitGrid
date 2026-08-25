# SplitGrid
# Copyright (c) 2026 KeithCu (modifications and relicensing)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
"""Comprehensive A/B serialization testing (split_grid vs nested list).

Every parity test compares force="always" (split_grid wire) vs force="never"
(nested list wire) and asserts the same final decoded semantics.

Codec-level only — no LibreOffice/UNO and no venv worker harness.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, assume, example, given, settings

from splitgrid.codec import (
    child_pack_result,
    host_pack_data,
    host_unpack_data,
    is_split_grid,
)
from tests.payload_codec_test_support import MIXED_WITH_ZIP
from tests.serialization_ab_support import (
    AbGridCase,
    MULTI_RANGE_FIXTURES,
    ab_hypothesis_max_examples,
    all_codec_ab_cases,
    assert_codec_split_vs_nosplit_parity,
    codec_child_materialization,
    expect_child_list_not_ndarray,
    fancier_result_strategy,
    flatten_semantic_cells,
    grid_cell_count,
    hypothesis_grid_ok,
    multi_range_child_materialization,
    multi_range_grid,
    prepare_grid,
    rectangular_grid,
)

_EX = ab_hypothesis_max_examples()


def _case_id(case: AbGridCase) -> str:
    return case.id


def _cases() -> list[AbGridCase]:
    return all_codec_ab_cases()


def _materialization_type_cases() -> list[AbGridCase]:
    """Multi-cell grids only — single-cell inputs unwrap to scalar in the child sandbox."""
    return [case for case in _cases() if grid_cell_count(prepare_grid(case)) > 1]


@pytest.mark.parametrize("case", _cases(), ids=_case_id)
def test_codec_child_and_host_decode_parity(case: AbGridCase) -> None:
    """split_grid vs nested list: child unpack and host unpack must match."""
    grid = prepare_grid(case)
    assert_codec_split_vs_nosplit_parity(grid, label=case.id)


@pytest.mark.parametrize("case", _cases(), ids=_case_id)
def test_split_wire_format(case: AbGridCase) -> None:
    """always → split_grid envelope; never → nested list only."""
    grid = prepare_grid(case)
    assert is_split_grid(host_pack_data(grid, force="always"))
    assert not is_split_grid(host_pack_data(grid, force="never"))


@pytest.mark.parametrize("case", _materialization_type_cases(), ids=_case_id)
def test_child_materialization_type(case: AbGridCase) -> None:
    """Under force=always: numeric-only → ndarray; any string → nested list."""
    np = pytest.importorskip("numpy")
    grid = prepare_grid(case)
    child = codec_child_materialization(grid, force="always")
    if expect_child_list_not_ndarray(grid if isinstance(grid, list) else [grid]):
        assert isinstance(child, list)
        assert not isinstance(child, np.ndarray)
    else:
        assert isinstance(child, np.ndarray)


@pytest.mark.parametrize("grids,label", MULTI_RANGE_FIXTURES, ids=[label for _, label in MULTI_RANGE_FIXTURES])
def test_multi_range_codec_decode(grids: list[list[Any] | list[list[Any]]], label: str) -> None:
    """multi_data envelope: child materialization leaf cells match source grids."""
    result = multi_range_child_materialization(grids, force="auto")
    assert len(result) == len(grids), label
    for idx, grid in enumerate(grids):
        assert flatten_semantic_cells(grid) == flatten_semantic_cells(result[idx]), f"{label}[{idx}]"


@given(grid=rectangular_grid())
@settings(max_examples=_EX["codec"], deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
@example([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]])
@example(MIXED_WITH_ZIP)
@example([[42.0]])
@example([["02138"]])
@example(["1", "2", "3"])
@example([1, 2, 3.5])
@example([True, False, 1])
@example(["long_string_" * 8])
@example([[1.0, 2.0], [3.0, 4.0]])
def test_hypothesis_codec_decode_parity(grid: list[Any] | list[list[Any]]) -> None:
    """Fuzz: codec child/host decode always vs never."""
    assume(hypothesis_grid_ok(grid))
    assert_codec_split_vs_nosplit_parity(grid, label="hypothesis codec")


@given(grids=multi_range_grid())
@settings(max_examples=_EX["multi_range"], deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_hypothesis_multi_range_codec_decode(grids: list[list[Any] | list[list[Any]]]) -> None:
    """Fuzz: multi-range child materialization leaf cells."""
    assume(all(hypothesis_grid_ok(g) for g in grids))
    result = multi_range_child_materialization(grids, force="auto")
    assert len(result) == len(grids)
    for idx, grid in enumerate(grids):
        assert flatten_semantic_cells(grid) == flatten_semantic_cells(result[idx]), f"index {idx}"


@given(result=fancier_result_strategy())
@settings(max_examples=_EX.get("fancier_result", 100), deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_hypothesis_fancier_result_roundtrip(result: Any) -> None:
    """Fuzz: roundtrip complex/fancier results through child_pack_result and host_unpack_data."""
    packed = child_pack_result(result)
    unpacked = host_unpack_data(packed)

    def normalize(val: Any) -> Any:
        if isinstance(val, tuple):
            return [normalize(x) for x in val]
        if isinstance(val, list):
            return [normalize(x) for x in val]
        if isinstance(val, dict):
            return {k: normalize(v) for k, v in val.items()}
        try:
            import math

            if math.isnan(val):
                return "NaN_sentinel"
        except (TypeError, ValueError):
            pass
        return val

    assert normalize(unpacked) == normalize(result)
