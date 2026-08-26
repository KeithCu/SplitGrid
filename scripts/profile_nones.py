#!/usr/bin/env python3
# SplitGrid - cProfile host_pack_data on a 20_000 x 5 grid with None holes.

import time
import cProfile
import pstats
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root))

try:
    import deal as _deal

    _deal.disable()
except ImportError:
    pass

from splitgrid.codec import host_pack_data

def bench_with_nones():
    # 100k cells, with some Nones
    nrows = 20000
    ncols = 5
    grid = [[float(i + j) if (i+j) % 10 != 0 else None for j in range(ncols)] for i in range(nrows)]
    
    print("Benchmarking 100k cells with Nones...")
    t0 = time.perf_counter()
    for _ in range(10):
        host_pack_data(grid, force="always")
    t1 = time.perf_counter()
    print(f"Average time: {(t1 - t0) * 100:.2f} ms")

if __name__ == "__main__":
    bench_with_nones()
    
    profiler = cProfile.Profile()
    profiler.enable()
    bench_with_nones()
    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(20)
