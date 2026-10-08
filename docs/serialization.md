# Split-grid wire format

This is the codec contract for `splitgrid` 0.2.0. Framing (Pickle 5, JSON, HTTP) stays in the application. This package only builds and reads the envelope.

## Envelope

```python
{
    "__wa_payload__": "split_grid",
    "dtype": "float64",
    "column_kinds": ["int", "float", "bool"],
    "shape": [rows, cols],  # or [n] for 1D
    "buffer": b"...",        # row-major float64; legacy "b64" still decodes
    "strings": {7: "banana"},
}
```

`BINARY_MIN_CELLS` is 100. Smaller grids stay nested lists unless `force="always"`. `force="never"` always stays a nested list.

Other tags this module detects, and unpacks where noted:

| Tag | Role |
|-----|------|
| `multi_data` | List of per-grid payloads in `items` |
| `image` | `data` bytes plus `format` (`svg` or `png`) |
| `dataframe` | `columns` plus inner `data` (list or split_grid) |
| `calc_range` | `shape` plus inner `data`. Unpack replaces `data` and keeps every other key. There is no CalcRange type here |

## Cell encoding

| Cell value | `buffer` | `strings` |
|------------|----------|-----------|
| `None` | `NaN` | — |
| `int` / `float` that `float()` accepts | numeric value; ints past ±2^53 round | — |
| `int` that `float()` rejects (`10**400`) | `NaN` | decimal text |
| `bool` | `0.0` / `1.0` | — |
| `str` (including `"02138"`) | `NaN` | text at the flat index |
| Python `complex` or a NumPy complex scalar | `NaN` | `str(val)` |

A column that mixes bool and int is kind `"int"`. Bool next to float is `"float"`. The child returns one float64 ndarray when `strings` is empty, including mixed numeric kinds. It casts to int or bool only when every column is that one kind. Host unpack restores per-column Python types and keeps buffer NaN as `float('nan')`. Mixed grids (`strings` non-empty) become nested lists; NaN holes become `None`.

The numeric ndarray lane is dtype kinds `i`, `u`, `f`, and `b`. Complex, void, datetime64, and timedelta64 are not cast. A direct `child_pack_split_grid` / `child_pack_result` on datetime64 or timedelta64 raises `ValueError`. Stdlib `datetime` on a grid becomes text in `strings`. Do not add a `'date'` column kind.

## Shape rules

- Rectangular 2D only. Uneven rows raise `ValueError`. Short rows are not padded.
- A row that is not a list or tuple raises `ValueError`.
- Rank other than 1 or 2 is not written into `shape`. Rank 3+ becomes a list of planes.
- A rectangular list whose cells are themselves lists or tuples is packed element-wise, not as one grid (those cells used to stringify to `"[0]"`).
- A rectangular tuple-of-tuples egresses as a list of lists. `host_unpack_data` restores a tuple only when the wire value is still a tuple.

## Keys, buffers, depth

- `strings` keys are integers in range. `1` and `"1"` collide and raise. Values must be `str`.
- `wire_str_key` raises when two dict keys stringify to the same wire key. The first value is not overwritten.
- `buffer` must be `bytes` whose length is `8 * cells`. A short buffer raises. Legacy `b64` must be valid ASCII base64.
- Pack, unpack, and `wire_cell_count` raise `ValueError` past depth 128 instead of `RecursionError`.
- `find_image_payloads` stops at depth 12 and returns `[]`. A shared image dict is reported once per parent; a shared wrapper is walked once.
- `write_image_payload_to_temp` leaves a successful file for the caller. A failed write deletes the file it created.
- A plain dict is walked so a nested envelope unpacks. List values inside that dict stay lists.
- Missing NumPy does not raise on a plain dict or list. Numeric `split_grid` still imports NumPy on its own.

## Host vs child

| Path | Numeric grid (`strings` empty) | Mixed grid |
|------|--------------------------------|------------|
| Host unpack | Nested lists. NaN stays `float('nan')`. Int and bool columns restore those types | Nested lists; string cells from the map |
| Child unpack | `ndarray` from `np.frombuffer`. Uniform float and mixed kinds are read-only. Uniform int and bool allocate a writable array | Nested lists; NaN holes are `None` |

`child_pack_result` without NumPy still packs plain lists and dicts. Top-level NumPy scalars become builtin `int` / `float` / `bool`.
