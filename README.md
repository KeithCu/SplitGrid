# SplitGrid

[![PyPI](https://img.shields.io/pypi/v/splitgrid.svg)](https://pypi.org/project/splitgrid/)

Asymmetric **split-grid** serialization for rectangular numeric and mixed-type grids.

This package was **pulled out of [WriterAgent](https://github.com/KeithCu/writeragent)** (LibreOffice Writer/Calc/Draw AI extension). It is the host flatten + child unpack codec that lived in `plugin.scripting.payload_codec`, plus the optional Cython flatten accelerator from `native/writeragent_vec`.

## Why this exists

A spreadsheet host often cannot import NumPy: LibreOffice’s embedded Python is a different interpreter from the user’s venv, and loading the user’s C extensions into the host is an ABI footgun. Heavy compute therefore runs in a **child** process that *does* have NumPy. The range still has to cross that boundary.

On the wire, a Calc-style range is a nested list: `list[list[float | int | str | None]]`. Standard pickle walks **one heap object per cell**. On a 20,000 × 5 grid that is ~12 ms for dump + load. Pack the same numbers into a contiguous `float64` buffer and Pickle Protocol 5 moves the bytes in ~0.015 ms; the child can `np.frombuffer` in ~0.002 ms.

Almost all of the remaining time is **host flatten** — turning nested Python objects into that buffer without NumPy (~8.3 ms pure Python on that shape; ~3 ms with the Cython helper). SplitGrid is that flatten/unpack. Length-prefixed Pickle 5 framing stays in the application; this package is the codec only.

Column-wise blobs and JSON + Base64 were tried first. Transposing columns on the host builds extra object graphs; Base64 and per-column reconstructs lose the `frombuffer` win. One row-major float64 buffer plus a sparse string map is faster and simpler.

## How it works

The path is **asymmetric**:

- **Host pack** (stdlib only) flattens a 1D or 2D rectangular grid into a contiguous `float64` buffer plus a sparse **integer-keyed** `strings` map. Empty cells become `NaN`. Zip codes like `"02138"` stay strings — they are never parsed as floats.
- **Child unpack** (NumPy) materializes a **pure-numeric** grid (`strings == {}`) with `np.frombuffer` (ndarray). Mixed grids use a vectorized object-masking path and return nested lists, restoring `None` for NaN holes.
- **Host unpack** preserves `float('nan')` from the buffer (does **not** coerce holes to `None`). That is the locked egress policy: NaN becomes a spreadsheet error, not a silent blank.

Grids with fewer than **100 cells** (`BINARY_MIN_CELLS`) stay nested Python lists. Force `"always"` / `"never"` overrides that threshold (used by A/B tests).

Wire envelope (Pickle5-friendly dict):

```python
{
    "__wa_payload__": "split_grid",
    "dtype": "float64",
    "column_kinds": ["int", "float"],  # per column: int / float / bool
    "shape": [rows, cols],             # or [n] for 1D
    "buffer": b"...",                  # row-major float64 bytes
    "strings": {7: "banana"},          # integer keys, not str(idx)
}
```

| Cell value | `buffer` (float64) | `strings` |
|------------|--------------------|-----------|
| `None` (empty cell) | `NaN` | — |
| `int` / `float` | numeric value | — |
| `bool` | `0.0` / `1.0` | — |
| `str` (including `"02138"`) | `NaN` | text by flat index |

There is **no datetime lane** on the float64 buffer. Python `datetime` objects stringify into `strings`. Do not add a `'date'` column kind.

Jagged 2D grids raise `ValueError` (spreadsheet ranges are rectangular).

## Numbers

Median timings from an asymmetric bench (host = stdlib pack; child = deserialize + materialize).

Ingress, **20,000 × 5** (100k cells):

| Format | Pack | Dump | Load | Materialize | Total |
|--------|------|------|------|-------------|-------|
| JSON nested lists | 6.2 ms | 22.8 ms | 14.6 ms | 2.1 ms | 45.7 ms |
| Pickle 5 nested lists | 6.1 ms | 1.4 ms | 2.9 ms | 2.0 ms | 12.4 ms |
| **Pickle 5 + split-grid** | 8.3 ms | **0.013 ms** | **0.015 ms** | **0.002 ms** | **8.3 ms** |

Child materialize of a **100 × 100** numeric grid: nested-list pickle then `np.array` ~0.6 ms; split-grid `frombuffer` ~**0.016 ms**. Below 100 cells the envelope is not worth it — that is why `BINARY_MIN_CELLS` exists. Host pack still dominates large ingress; Cython only speeds that loop.

## Python vs Cython

Host flatten is an optimized **pure-Python** loop:

- identity type checks (`type(val) is float`, `val is None`)
- bound-method capture (`buf_append = buf.append`)
- `None` as NaN on the fast path
- lazy column-state upgrades
- rectangular validation before the hot loop

The optional **Cython** module `splitgrid.pack` exposes `fast_flatten_grid_1d` / `fast_flatten_grid_2d`. It is loaded dynamically and **canary-tested** at import. If the extension is missing or fails the canary, the codec uses pure Python. Importing `splitgrid` never requires a compiler. Extension builds use release flags (`-O3 -DNDEBUG -g0` on Unix, `/O2 /DNDEBUG` on Windows).

## Install

```bash
pip install splitgrid
```

PyPI wheels include the compiled Cython flatten accelerator. From a source checkout (Cython is built if a compiler is available):

```bash
pip install .
pip install -e ".[test]"      # editable + pytest, hypothesis, deal, numpy
pip install -e ".[numpy]"     # child unpack/pack
pip install -e ".[verify]"    # crosshair-tool
```

Host pack stays NumPy-free. Child `child_unpack_*` / `child_pack_*` import NumPy locally.

## Test

```bash
pytest                  # default: -m "not slow"
pytest -m "not slow"    # same
pytest -m slow          # CrossHair subprocess checks (optional)
make verify             # deal contracts + hypothesis round-trips, no CrossHair
```

Default pytest **does not require** the compiled extension. When `splitgrid.pack` is built, `tests/test_cython_parity.py` compares Cython and Python flatten components on the same grids.

## Bench

Requires NumPy (and the optional Cython extension if you want the accelerated pack row). From a source checkout:

```bash
python scripts/bench_serialization.py --direction both
python scripts/bench_serialization.py --child-only
python scripts/bench_unpacking_opt.py
python scripts/profile_pack.py
python scripts/profile_nones.py
python scripts/run_serialization_ab.py --all
make bench
```

## Public API

```python
from splitgrid import (
    BINARY_MIN_CELLS,
    host_pack_split_grid,
    host_unpack_split_grid,
    child_unpack_split_grid,
    child_pack_split_grid,
    host_pack_data,
    host_unpack_data,
    child_unpack_data,
    child_pack_result,
    is_split_grid,
    load_cython_accelerator,
    get_cython_status_info,
)
```

`host_pack_data(..., force="auto"|"always"|"never")` chooses split-grid vs nested list. `host_pack_multi_data` is a thin `multi_data` wrapper over the same per-grid packing.

## License

GPL-3.0-or-later.
