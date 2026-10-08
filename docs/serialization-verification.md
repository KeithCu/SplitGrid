# Serialization verification

`src/splitgrid/codec.py` carries `@deal` contracts and `# crosshair: off` markers. Pytest oracles live in:

- `tests/test_payload_codec.py` (default `make test`)
- `tests/test_payload_codec_policy_verification.py`
- `tests/test_serialization_verification.py` (module is `pytest.mark.slow`)
- `tests/test_serialization_ab.py` (codec-level always-vs-never parity; no venv worker)

```bash
make test          # pytest -m "not slow"
make verify        # deal + hypothesis round-trips, no CrossHair subprocess
pytest -m slow     # includes CrossHair when the `crosshair` executable is installed
```

`splitgrid.deal_shim` is a no-op when `deal` is not installed. Pytest uses the wide domain (`DEAL_MAX_ROW_INDEX` 1_048_575, `DEAL_MAX_COL_INDEX` 18277, `DEAL_MAX_SHAPE_DIM` 256). Set `SPLITGRID_CROSSHAIR=1` (or `WRITERAGENT_CROSSHAIR=1`) before import to bind the short table. Do not branch on that flag inside a `@deal.pre` lambda; `_profile` picks the predicate once at import.

## What the contracts cover

Policy and shape: `cell_count`, `should_use_binary_envelope`, `binary_envelope_skip_reason`, `is_numeric_coercible`, `is_numeric_grid`, `wire_cell_count`, `grid_from_nested_list`, `column_kinds_for_grid`.

Detectors: `is_split_grid`, `is_multi_data`, `is_image_payload`, `is_dataframe_payload`, `is_calc_range_payload`. Shape extents are non-negative ints. `True` is not a shape extent.

Pack and unpack: `host_pack_split_grid`, `host_pack_data`, `host_pack_multi_data`, `host_unpack_split_grid`, `host_unpack_data`, `child_unpack_split_grid`, `child_unpack_data`, `child_pack_split_grid`, `child_pack_result`.

`host_pack_data`, `child_unpack_data`, and `child_pack_result` keep a minimal pre/post. Branch results (ndarray vs list vs envelope) are pytest oracles. Keyword-only parameters use `@deal.pre(lambda arg, *_, **__: ...)` so Deal/CrossHair does not collide on `result`.

Round-trips are not `@deal.ensure`. Host unpack is compared with semantic equality (buffer NaN matches a Python `None` in the oracle; the host value itself stays `float('nan')`). Mixed child unpack is strict equality. Pure-numeric child unpack checks the non-`None` cells.

## Invariants pinned in pytest

- `strings` keys are ints. Duplicate stringified keys raise. `wire_str_key` is the same error on egress dicts.
- `float()` overflow is text, on both the Python and Cython flatten. Integers `float()` accepts stay numeric, including past 53 bits.
- A NumPy complex scalar is text. Builtin `complex` was already text.
- A non-sequence row raises `ValueError`, not `TypeError` from `len()`.
- A numeric grid with mixed column kinds stays float64 in the child. Host unpack restores column types.
- Bool mixed with int in one column is kind `int`.
- Rank 3+ is a list of planes. The detector accepts rank 1 or 2 only.
- `host_unpack_data` shallow-copies dataframe and calc_range envelopes and replaces `data`, so extra keys survive.
- Pure-float `frombuffer` is read-only. Uniform int and bool allocate.
- `wire_cell_count` and the unpackers raise at depth 128 on a cycle.
- A plain dict larger than `DEAL_MAX_SHAPE_DIM` still unpacks. Detector preconditions are total on the pytest profile.

Pack/unpack entry points are mostly `# crosshair: off`. Preferred CrossHair targets are the detectors and policy helpers (`splitgrid.codec.is_split_grid`, and the same module for `is_multi_data`, `is_image_payload`, `is_dataframe_payload`, `is_calc_range_payload`, `is_numeric_coercible`, `is_numeric_grid`, `cell_count`, `should_use_binary_envelope`). A `: error:` line is a counterexample. `Not confirmed` is not a failure. Exploration logs from bad envelopes are expected during `cover`.
