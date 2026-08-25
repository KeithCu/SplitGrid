# SplitGrid
# Copyright (c) 2026 KeithCu
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared deep-Hypothesis budget flag.

``SPLITGRID_VHS_EXTENSIVE`` is preferred. WriterAgent aliases remain so older
docs/Make targets keep working.
"""

from __future__ import annotations

import os

_VHS_EXTENSIVE_ENV = "SPLITGRID_VHS_EXTENSIVE"
_SERIALIZATION_EXTENSIVE_ENV = "SPLITGRID_SERIALIZATION_EXTENSIVE"
_WA_VHS_EXTENSIVE_ENV = "WRITERAGENT_VHS_EXTENSIVE"
_WA_SERIALIZATION_EXTENSIVE_ENV = "WRITERAGENT_SERIALIZATION_EXTENSIVE"


def vhs_extensive() -> bool:
    """True when deep Hypothesis fuzzing is requested (not default pytest)."""
    for key in (
        _VHS_EXTENSIVE_ENV,
        _SERIALIZATION_EXTENSIVE_ENV,
        _WA_VHS_EXTENSIVE_ENV,
        _WA_SERIALIZATION_EXTENSIVE_ENV,
    ):
        if os.environ.get(key, "").lower() in ("1", "true", "yes"):
            return True
    return False


def vhs_max_examples(light: int, extensive: int) -> int:
    """Pick light vs deep Hypothesis example counts."""
    return extensive if vhs_extensive() else light
