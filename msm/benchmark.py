"""
Benchmark every MSM algorithm on the same inputs and save the results.

    python -m msm.benchmark                 # full run, writes results/
    python -m msm.benchmark --quick         # small smoke-test run

For each (number of points, scalar bit length) case this records:
  * execution time   - median of several timed runs (time.perf_counter)
  * peak memory      - peak Python allocation during one run (tracemalloc)
  * point operations - additions and doublings, counted exactly
Every result is also checked against the naive MSM before it is recorded.
"""

import argparse
import csv
import gc
import random
import statistics
import time
import tracemalloc
from pathlib import Path

from . import ALGORITHMS
from .curve_utils import count_operations, generate_test_case, get_curve, naive_msm

# Same input grid as the dissertation: vary size, vary bit length, vary both.
DISSERTATION_CASES = [
    (5, 32), (10, 32), (20, 32), (50, 32), (100, 32),
    (20, 8), (20, 16), (20, 64), (20, 128),
    (5, 16), (50, 128), (100, 256),
]
QUICK_CASES = [(5, 16), (10, 32), (20, 32)]


def _time_once(func, scalars, points):
    gc.collect()
    start = time.perf_counter()
    func(scalars, points)
    return time.perf_counter() - start


def _peak_memory_kib(func, scalars, points):
    gc.collect()
    tracemalloc.start()
    func(scalars, points)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024


def run(cases, trials=3, curve_name="secp256k1", seed=42):
    """Run every algorithm on every case. Returns a list of result rows."""
    curve = get_curve(curve_name)
    rows = []
    for n, bits in cases:
        random.seed(f"{seed}-{n}-{bits}")
        scalars, points = generate_test_case(curve, n, bits)
        expected = naive_msm(scalars, points)

        for name, func in ALGORITHMS.items():
            if func(scalars, points) != expected:
                raise AssertionError(f"{name} returned a wrong result for n={n}, bits={bits}")

            with count_operations() as ops:
                func(scalars, points)

            times = [_time_once(func, scalars, points) for _ in range(trials)]
            rows.append({
                "algorithm": name,
                "points": n,
                "scalar_bits": bits,
                "time_s": statistics.median(times),
                "peak_memory_kib": _peak_memory_kib(func, scalars, points),
                "additions": ops["additions"],
                "doublings": ops["doublings"],
                "total_operations": ops["additions"] + ops["doublings"],
            })
            print(f"  {name:<32} n={n:<4} bits={bits:<4} "
                  f"ops={rows[-1]['total_operations']:<6} time={rows[-1]['time_s']:.4f}s")
    return rows


def load_csv(path):
    """Load rows written by :func:`save_csv`, with numeric columns converted."""
    ints = {"points", "scalar_bits", "additions", "doublings", "total_operations"}
    floats = {"time_s", "peak_memory_kib"}
    with Path(path).open(newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ints:
            r[k] = int(r[k])
        for k in floats:
            r[k] = float(r[k])
    return rows


def save_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true", help="run a small subset of cases")
    parser.add_argument("--trials", type=int, default=3, help="timed runs per case (median)")
    parser.add_argument("--out", default="results", help="output directory")
    parser.add_argument("--no-plots", action="store_true", help="skip figure generation")
    args = parser.parse_args()

    cases = QUICK_CASES if args.quick else DISSERTATION_CASES
    print(f"Benchmarking {len(ALGORITHMS)} algorithms on {len(cases)} cases...")
    rows = run(cases, trials=args.trials)

    out = Path(args.out)
    save_csv(rows, out / "benchmark_results.csv")
    print(f"Saved {out / 'benchmark_results.csv'}")

    if not args.no_plots:
        import matplotlib
        matplotlib.use("Agg")
        from .plots import make_all_figures
        make_all_figures(rows, out / "figures")
        print(f"Saved figures to {out / 'figures'}")


if __name__ == "__main__":
    main()
