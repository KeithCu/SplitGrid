# SplitGrid - Deal contract shim (from WriterAgent plugin.framework.deal_shim)
# Copyright (c) 2026 KeithCu
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Deal contract shim.

Provides actual ``deal`` decorators when deal is installed, or no-op stubs
when it is absent (PyPI install without extras; LibreOffice host later).

``DEAL_MAX_*`` are finite ``@deal.pre`` domains, not production limits.
Pytest binds the wide table (shape_dim=256 so 100×100 pack tests fit).
CrossHair binds the short table when ``SPLITGRID_CROSSHAIR=1`` or
``WRITERAGENT_CROSSHAIR=1`` at import. Do not sniff ``sys.modules["crosshair"]``
or branch inside ``@deal.pre`` lambdas.
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


def deal_maxima(*, crosshair: bool) -> DealMaxima:
    """Return the pytest (wide) or CrossHair (tiny) ``DEAL_MAX_*`` table.

    Import-time only. Do not call from inside ``@deal.pre`` lambdas.
    """
    if crosshair:
        return DealMaxima(
            shape_dim=4,  # 100×100 pack tests are pytest-only
            shape_rank=2,
        )
    return DealMaxima(
        shape_dim=256,  # 100×100 pack tests fit; CrossHair uses 4
        shape_rank=4,  # ndarray rank; grids are 2-D, pytest uses up to 4
    )


_CROSSHAIR = os.environ.get(CROSSHAIR_ENV_PRIMARY) == "1" or os.environ.get(CROSSHAIR_ENV_ALIAS) == "1"
_MAXIMA = deal_maxima(crosshair=_CROSSHAIR)
DEAL_MAX_SHAPE_DIM = _MAXIMA.shape_dim
DEAL_MAX_SHAPE_RANK = _MAXIMA.shape_rank

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
