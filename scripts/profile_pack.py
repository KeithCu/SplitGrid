#!/usr/bin/env python3
# SplitGrid - cProfile host_pack_data on a 20_000 x 5 numeric grid.

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

def bench():
    # 100k cells
    nrows = 20000
    ncols = 5
    grid = [[float(i + j) for j in range(ncols)] for i in range(nrows)]
    
    print("Benchmarking 100k cells...")
    t0 = time.perf_counter()
    for _ in range(10):
        host_pack_data(grid, force="always")
    t1 = time.perf_counter()
    print(f"Average time: {(t1 - t0) * 100:.2f} ms")

if __name__ == "__main__":
    # Run once to warm up
    nrows = 1000
    grid = [[float(i + j) for j in range(5)] for i in range(nrows)]
    host_pack_data(grid, force="always")
    
    profiler = cProfile.Profile()
    profiler.enable()
    bench()
    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(20)
