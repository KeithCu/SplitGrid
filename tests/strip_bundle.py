# SplitGrid
# Copyright (c) 2026 KeithCu
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Helpers for deal-contract tests (unstripped source vs deal-shim no-op)."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any


def module_source_contains(obj: object, needle: str) -> bool:
    """True when *needle* appears in the source file of *obj* (module or function)."""
    target: object = obj
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        target = inspect.unwrap(obj)
    try:
        path = inspect.getfile(target)  # type: ignore[arg-type]
        source = Path(path).read_text(encoding="utf-8")
    except (OSError, TypeError):
        return False
    return needle in source


def _decorator_header(source: str) -> str:
    """Decorator lines from ``inspect.getsource`` through the ``def`` line."""
    header: list[str] = []
    for line in source.splitlines(keepends=True):
        header.append(line)
        stripped = line.lstrip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            break
    return "".join(header)


def deal_pre_present(obj: object) -> bool:
    """True when ``@deal.pre`` remains on *obj*'s definition."""
    target: object = obj
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        target = inspect.unwrap(obj)
    try:
        source = inspect.getsource(target)  # type: ignore[arg-type]
    except (OSError, TypeError):
        return module_source_contains(obj, "@deal.pre")
    return "@deal.pre" in _decorator_header(source)
