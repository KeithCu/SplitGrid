# SplitGrid

Asymmetric **split-grid** serialization for rectangular numeric and mixed-type grids.

This package was **pulled out of [WriterAgent](https://github.com/KeithCu/writeragent)** (LibreOffice Writer/Calc/Draw AI extension). It is the same host flatten + child unpack codec that lived in `plugin.scripting.payload_codec`, plus the optional Cython flatten accelerator from `native/writeragent_vec`. WriterAgent can later depend on `splitgrid` without changing the wire dict.

Repo: [github.com/KeithCu/writeragent](https://github.com/KeithCu/writeragent)

## What split-grid is

The compute path is **asymmetric by design**:

- **Host pack** (LibreOffice’s embedded Python, or any NumPy-free interpreter) flattens a 1D or 2D grid into a contiguous `float64` buffer plus a sparse **integer-keyed** `strings` map. Empty cells become `NaN`. Zip codes like `"02138"` stay strings — they are never parsed as floats.
- **Child unpack** (venv with NumPy) materializes a **pure-numeric** grid (`strings == {}`) with `np.frombuffer` (ndarray). Mixed grids use a vectorized object-masking path and return nested lists, restoring `None` for NaN holes.
- **Host unpack** preserves `float('nan')` from the buffer (does **not** coerce holes to `None`). That is the locked egress policy: NaN becomes a Calc error, not a silent blank.

Grids with fewer than **100 cells** (`BINARY_MIN_CELLS`) stay nested Python lists. Force `"always"` / `"never"` overrides that threshold (used by A/B tests).

Wire envelope (Pickle5-friendly dict, same keys as WriterAgent):

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

There is **no datetime lane** on the float64 buffer. Python `datetime` objects stringify into `strings`. Do not add a `'date'` column kind.

Jagged 2D grids raise `ValueError` (Calc ranges are rectangular).

## Python vs Cython

Host flatten is an optimized **pure-Python** loop:

- identity type checks (`type(val) is float`, `val is None`)
- bound-method capture (`buf_append = buf.append`)
- `None` as NaN on the fast path
- lazy column-state upgrades
- rectangular validation before the hot loop

The optional **Cython** module `splitgrid.pack` exposes `fast_flatten_grid_1d` / `fast_flatten_grid_2d`. It is loaded dynamically and **canary-tested** at import. If the extension is missing or fails the canary, the codec uses pure Python. Importing `splitgrid` never requires a compiler.

## Install

```bash
# Runtime (pure Python; Cython built if a compiler is available)
pip install .

# Editable + tests
pip install -e ".[test]"

# Optional extras
pip install -e ".[numpy]"     # child unpack/pack
pip install -e ".[test]"      # pytest, hypothesis, deal, numpy
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

## Public API (WriterAgent-compatible)

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

## How WriterAgent will consume this

In [WriterAgent](https://github.com/KeithCu/writeragent), replace `from plugin.scripting.payload_codec import host_pack_data, ...` with `from splitgrid import host_pack_data, ...`. The envelope tag stays `"split_grid"`, dtype `"float64"`, integer-keyed `strings`, and `column_kinds` `int`/`float`/`bool`. Pickle Protocol 5 framing stays in WriterAgent’s `ipc.py` — this package is the codec only.

## License

GPL-3.0-or-later (same as WriterAgent).
