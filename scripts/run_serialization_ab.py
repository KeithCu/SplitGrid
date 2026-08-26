#!/usr/bin/env python3
# SplitGrid - manual A/B codec round-trip runner (always vs never).
"""Compare force=always (split_grid) vs force=never (nested list) at the codec.

Example:
  python scripts/run_serialization_ab.py --list
  python scripts/run_serialization_ab.py --grid numeric_4x4
  python scripts/run_serialization_ab.py --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from tests.serialization_ab_support import (  # noqa: E402
    all_codec_ab_cases,
    assert_codec_split_vs_nosplit_parity,
    prepare_grid,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual always vs never codec A/B runner")
    parser.add_argument("--list", action="store_true", help="List named grid fixture ids")
    parser.add_argument("--grid", default="numeric_4x4", help="Fixture id from --list")
    parser.add_argument("--all", action="store_true", help="Run every named fixture")
    args = parser.parse_args()

    cases = {c.id: c for c in all_codec_ab_cases()}
    if args.list:
        for cid in sorted(cases):
            print(cid)
        return 0

    ids = sorted(cases) if args.all else [args.grid]
    failed = 0
    for gid in ids:
        if gid not in cases:
            print(f"Unknown grid {gid!r}. Use --list.", file=sys.stderr)
            return 1
        case = cases[gid]
        grid = prepare_grid(case)
        try:
            assert_codec_split_vs_nosplit_parity(grid, label=gid)
            print(f"{gid}: OK")
        except AssertionError as e:
            print(f"{gid}: FAIL — {e}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
