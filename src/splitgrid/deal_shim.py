# SplitGrid - Deal contract shim (from WriterAgent plugin.framework.deal_shim)
# Copyright (c) 2026 KeithCu
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Deal contract shim.

Provides actual ``deal`` decorators when deal is installed, or no-op stubs
when it is absent (PyPI install without extras).

``DEAL_MAX_*`` are finite ``@deal.pre`` domains, not production limits.
Pytest binds the wide table (Calc-sized row/column, shape_dim=256 so 100×100
pack tests fit). CrossHair binds the short table when ``SPLITGRID_CROSSHAIR=1``
or ``WRITERAGENT_CROSSHAIR=1`` at import. Do not sniff ``sys.modules["crosshair"]``
or branch inside ``@deal.pre`` lambdas.

Only the maxima the codec uses live here. WriterAgent's full table (paths,
URLs, HTML) stays in that project.
"""

from __future__ import annotations

import os
from typing import Any, NamedTuple

CROSSHAIR_ENV_PRIMARY = "SPLITGRID_CROSSHAIR"
CROSSHAIR_ENV_ALIAS = "WRITERAGENT_CROSSHAIR"


class DealMaxima(NamedTuple):
    """Finite ``@deal.pre`` domains. Pytest is product-faithful; CrossHair is tiny."""

    shape_dim: int
    shape_rank: int
    row_index: int
    col_index: int
    source: int


def deal_maxima(*, crosshair: bool) -> DealMaxima:
    """Return the pytest (wide) or CrossHair (tiny) ``DEAL_MAX_*`` table.

    Import-time only. Do not call from inside ``@deal.pre`` lambdas.
    """
    if crosshair:
        return DealMaxima(
            shape_dim=4,  # 100×100 pack tests are pytest-only
            shape_rank=2,
            row_index=20,
            col_index=25,  # A–Z
            source=16,
        )
    return DealMaxima(
        shape_dim=256,  # 100×100 pack tests fit; CrossHair uses 4
        shape_rank=4,  # ndarray rank; grids are 2-D, pytest uses up to 4
        row_index=1_048_575,  # Calc max 0-based row
        col_index=26 + 26**2 + 26**3 - 1,  # 18277, A–ZZZ
        source=8192,
    )


_CROSSHAIR = os.environ.get(CROSSHAIR_ENV_PRIMARY) == "1" or os.environ.get(CROSSHAIR_ENV_ALIAS) == "1"
UNDER_CROSSHAIR = _CROSSHAIR
_MAXIMA = deal_maxima(crosshair=_CROSSHAIR)
DEAL_MAX_SHAPE_DIM = _MAXIMA.shape_dim
DEAL_MAX_SHAPE_RANK = _MAXIMA.shape_rank
DEAL_MAX_ROW_INDEX = _MAXIMA.row_index
DEAL_MAX_COL_INDEX = _MAXIMA.col_index
DEAL_MAX_SOURCE = _MAXIMA.source

deal: Any

try:
    import deal as _deal  # type: ignore[no-redef]
    deal = _deal
except ImportError:

    class _DealStub:
        """No-op stub for deal contract decorators when deal is not installed."""

        def pre(self, *args, **kwargs):
            return lambda f: f

        def post(self, *args, **kwargs):
            return lambda f: f

        def inv(self, *args, **kwargs):
            return lambda f: f

        def pure(self, f=None, *args, **kwargs):
            return f if f is not None else (lambda fn: fn)

        def chain(self, *args, **kwargs):
            return lambda f: f

        def raises(self, *args, **kwargs):
            return lambda f: f

        def example(self, *args, **kwargs):
            return lambda f: f

        def ensure(self, *args, **kwargs):
            return lambda f: f

        def reason(self, *args, **kwargs):
            return lambda f: f

    deal = _DealStub()


def ascii_bounded(s: object, max_len: int, min_len: int = 0) -> bool:
    """True iff *s* is an ASCII str with min_len <= len(s) <= max_len."""
    return isinstance(s, str) and s.isascii() and min_len <= len(s) <= max_len


def _identity_contract(*args: Any, **kwargs: Any) -> Any:
    """No-op decorator: skip nested inverse ensures under CrossHair."""
    return lambda f: f


def inverse_ensure_for(*, crosshair: bool) -> Any:
    """Nested inverse ``@deal.ensure``: live under pytest, no-op under CrossHair.

    Bound at import, not inside a ``@deal.pre`` lambda — CrossHair would explore
    both branches of an in-lambda ``if``. Cheap ``@deal.post`` still runs.
    """
    if crosshair:
        return _identity_contract
    return deal.ensure


def _profile(crosshair_fn: Any, pytest_fn: Any = lambda *args, **kwargs: True) -> Any:
    """Pick the contract predicate once at import.

    Do not branch on ``UNDER_CROSSHAIR`` inside ``@deal.pre``; CrossHair would
    explore both arms. ``pytest_fn`` defaults to always-true when only the
    CrossHair domain is restricted.
    """
    # crosshair: off
    return crosshair_fn if UNDER_CROSSHAIR else pytest_fn


inverse_ensure = inverse_ensure_for(crosshair=_CROSSHAIR)
