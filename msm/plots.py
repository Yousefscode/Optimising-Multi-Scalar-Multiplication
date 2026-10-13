"""Figures for the benchmark results (matplotlib, saved as PNG)."""

from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Fixed colour per algorithm (never re-assigned by rank). Variants of the
# same family are dashed so identity never relies on colour alone.
STYLE = {
    "Bos-Coster":                     ("#2a78d6", "-",  "o"),
    "Bos-Coster (Efficient)":         ("#eb6834", "--", "o"),
    "Bucketing":                      ("#1baf7a", "-",  "s"),
    "Bucketing (Interleaved)":        ("#eda100", "--", "s"),
    "Comb-Bucketing":                 ("#e87ba4", ":",  "s"),
    "Pippenger":                      ("#008300", "-",  "^"),
    "Pippenger (Input Partitioning)": ("#4a3aa7", "--", "^"),
}

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _series(rows, x_key, y_key, fixed_key, fixed_value, per_point=False):
    data = defaultdict(list)
    for r in rows:
        if r[fixed_key] == fixed_value:
            y = r[y_key] / r["points"] if per_point else r[y_key]
            data[r["algorithm"]].append((r[x_key], y))
    return {k: sorted(v) for k, v in data.items()}


def _line_chart(series, title, xlabel, ylabel, path, logx=True, logy=True):
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    fig.patch.set_facecolor("white")
    for name, (color, ls, marker) in STYLE.items():
        if name not in series:
            continue
        xs, ys = zip(*series[name])
        ax.plot(xs, ys, color=color, linestyle=ls, linewidth=2, marker=marker,
                markersize=6, markeredgecolor="white", markeredgewidth=1, label=name)
    if logx:
        ax.set_xscale("log", base=2)
    if logy:
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(sorted({x for s in series.values() for x, _ in s}))
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=12)
    ax.set_xlabel(xlabel, color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_all_figures(rows, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    _line_chart(_series(rows, "points", "total_operations", "scalar_bits", 32),
                "Point operations vs number of points (32-bit scalars)",
                "Number of points (n)", "Point additions + doublings",
                out / "ops_vs_points.png")
    _line_chart(_series(rows, "points", "time_s", "scalar_bits", 32),
                "Execution time vs number of points (32-bit scalars)",
                "Number of points (n)", "Median time (s)",
                out / "time_vs_points.png")
    _line_chart(_series(rows, "scalar_bits", "total_operations", "points", 20),
                "Point operations vs scalar bit length (n = 20)",
                "Scalar bit length", "Point additions + doublings",
                out / "ops_vs_bits.png")
    _line_chart(_series(rows, "points", "total_operations", "scalar_bits", 32, per_point=True),
                "Operations per point (32-bit scalars)",
                "Number of points (n)", "Operations per point",
                out / "ops_per_point.png", logy=False)
    _line_chart(_series(rows, "points", "peak_memory_kib", "scalar_bits", 32),
                "Peak memory vs number of points (32-bit scalars)",
                "Number of points (n)", "Peak Python allocation (KiB)",
                out / "memory_vs_points.png")
