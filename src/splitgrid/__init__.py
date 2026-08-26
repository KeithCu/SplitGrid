# SplitGrid - split-grid serialization extracted from WriterAgent
# Copyright (c) 2026 KeithCu
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Asymmetric split-grid codec: host flatten (stdlib) + optional Cython, child NumPy unpack.

Public names match WriterAgent's ``plugin.scripting.payload_codec`` split-grid surface
so WriterAgent can switch imports later without changing the wire dict.
"""

from splitgrid.codec import (
    BINARY_MIN_CELLS,
    MAX_BENCH_CELLS,
    PAYLOAD_CALC_RANGE,
    PAYLOAD_DATAFRAME,
    PAYLOAD_IMAGE,
    PAYLOAD_MULTI_DATA,
    PAYLOAD_SPLIT_GRID,
    SPLIT_GRID_WIRE_DTYPE,
    ForceBinary,
    _flatten_append_cell_slow,
    _flatten_grid_to_components,
    _iter_split_grid_cells,
    _verify_accelerator,
    binary_envelope_skip_reason,
    cell_count,
    child_pack_result,
    child_pack_split_grid,
    child_unpack_data,
    child_unpack_split_grid,
    column_kinds_for_grid,
    describe_wire_value,
    envelope_column_kinds,
    envelope_uniform_column_kind,
    get_cython_status_info,
    grid_from_nested_list,
    host_cython_status_line,
    host_pack_data,
    host_pack_multi_data,
    host_pack_split_grid,
    host_unpack_data,
    host_unpack_split_grid,
    invalidate_host_cython_accelerator,
    is_dataframe_payload,
    is_calc_range_payload,
    is_image_payload,
    is_multi_data,
    is_numeric_coercible,
    is_numeric_grid,
    is_split_grid,
    load_cython_accelerator,
    reload_host_cython_accelerator,
    should_use_binary_envelope,
    wire_cell_count,
)

__version__ = "0.1.2"


def __getattr__(name: str):
    """Bind accelerator function names to codec globals (may be None until load)."""
    if name in ("fast_flatten_grid_1d", "fast_flatten_grid_2d"):
        from splitgrid import codec as _codec

        return getattr(_codec, name)
    raise AttributeError(f"module 'splitgrid' has no attribute {name!r}")

__all__ = [
    "BINARY_MIN_CELLS",
    "MAX_BENCH_CELLS",
    "PAYLOAD_CALC_RANGE",
    "PAYLOAD_DATAFRAME",
    "PAYLOAD_IMAGE",
    "PAYLOAD_MULTI_DATA",
    "PAYLOAD_SPLIT_GRID",
    "SPLIT_GRID_WIRE_DTYPE",
    "ForceBinary",
    "__version__",
    "_flatten_append_cell_slow",
    "_flatten_grid_to_components",
    "_iter_split_grid_cells",
    "_verify_accelerator",
    "binary_envelope_skip_reason",
    "cell_count",
    "child_pack_result",
    "child_pack_split_grid",
    "child_unpack_data",
    "child_unpack_split_grid",
    "column_kinds_for_grid",
    "describe_wire_value",
    "envelope_column_kinds",
    "envelope_uniform_column_kind",
    "fast_flatten_grid_1d",
    "fast_flatten_grid_2d",
    "get_cython_status_info",
    "grid_from_nested_list",
    "host_cython_status_line",
    "host_pack_data",
    "host_pack_multi_data",
    "host_pack_split_grid",
    "host_unpack_data",
    "host_unpack_split_grid",
    "invalidate_host_cython_accelerator",
    "is_calc_range_payload",
    "is_dataframe_payload",
    "is_image_payload",
    "is_multi_data",
    "is_numeric_coercible",
    "is_numeric_grid",
    "is_split_grid",
    "load_cython_accelerator",
    "reload_host_cython_accelerator",
    "should_use_binary_envelope",
    "wire_cell_count",
]
