"""Figure 3: how good must the calibration be to hit the accuracy target?

Colour: worst-case RMSE over all wind speeds 0.5-10 m/s, for each combination of the two calibration
errors: tilt offset b (x) and drag-coefficient error (y). Worst case = the signs of b and k-error add.
Lines: where the research target (solid) and the WMO standard (dashed) are just met at every wind speed.
Run from simulations/:  python -m level1_steady.requirements_map_fig3
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
from matplotlib.lines import Line2D

from windmap import airframes, drag, montecarlo, plotstyle, targets

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER
SIGMA_DEG = 0.5                        # D4: noise std of one 1 s tilt sample [deg]
N_EFF = 30                             # D4: 30 s hover average
V_GRID = np.linspace(0.5, 10.0, 20)    # D5: wind speeds the target must hold over [m/s]
B_GRID = np.linspace(0.0, 1.2, 31)     # tilt offsets to test [deg]
K_GRID = np.linspace(0.0, 0.20, 31)    # drag-coefficient errors to test [fraction]
N_TRIALS = 2_000                       # fewer trials per point: 3,844 runs in total
SEED = 0
POINTS = {                             # (b [deg], k-error [fraction]) marked on the map
    "Today's values": (0.7, 0.15),
    "With heading flip": (0.0, 0.15),
}


def worst_rmse(b, k_err):
    """RMSE [m/s] at each wind speed, for whichever signs of b and k-error make it largest."""
    runs = []
    for s_b in (1, -1):
        for s_k in (1, -1):
            est = airframes.Airframe("estimator", AIRFRAME.m, drag.DragModel(k=(1 + s_k * k_err) * AIRFRAME.drag.k))
            rng = np.random.default_rng(SEED)
            runs.append(montecarlo.run_mc(V_GRID, AIRFRAME, est, s_b * b, SIGMA_DEG, N_EFF, N_TRIALS, rng)["rmse"])
    return np.max(runs, axis=0)


def main():
    plotstyle.apply()

    # One row per k-error, one column per offset
    worst = np.empty((K_GRID.size, B_GRID.size))           # worst RMSE over all winds [m/s]
    vs_research = np.empty_like(worst)                     # worst (RMSE / allowed) over all winds
    vs_wmo = np.empty_like(worst)
    for i, k_err in enumerate(K_GRID):
        for j, b in enumerate(B_GRID):
            r = worst_rmse(b, k_err)
            worst[i, j] = r.max()
            vs_research[i, j] = np.max(r / targets.research(V_GRID))
            vs_wmo[i, j] = np.max(r / targets.wmo(V_GRID))

    fig, ax = plt.subplots(figsize=(plotstyle.TEXT_WIDTH_IN, 4.2))
    blues = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
    levels = [0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    fill = ax.contourf(B_GRID, 100 * K_GRID, worst, levels=levels, cmap=blues, extend="max",
                       norm=BoundaryNorm(levels, blues.N, extend="max"))
    cbar = fig.colorbar(fill, ax=ax, pad=0.02)
    cbar.set_label("Worst-case RMSE over 0.5–10 m/s wind [m/s]")

    ax.contour(B_GRID, 100 * K_GRID, vs_research, levels=[1.0], colors="black", linewidths=1.6)
    ax.contour(B_GRID, 100 * K_GRID, vs_wmo, levels=[1.0], colors="black", linewidths=1.2, linestyles="--")

    for label, (b, k_err) in POINTS.items():
        ax.plot(b, 100 * k_err, "o", ms=6, mfc="white", mec="black", mew=1.2, clip_on=False, zorder=5)
        ax.annotate(label, (b, 100 * k_err), xytext=(6, 4), textcoords="offset points", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))

    ax.set_xlabel(r"Tilt offset $b$ [°]")
    ax.set_ylabel(r"Drag-coefficient error $|\Delta k| / k$ [%]")
    ax.legend(handles=[Line2D([], [], color="black", lw=1.6,
                              label=f"Research target met ({targets.RESEARCH_RMSE} m/s at all winds)"),
                       Line2D([], [], color="black", lw=1.2, ls="--",
                              label="WMO standard met (0.5 m/s, or 10 % above 5 m/s)")],
              loc="upper right", fontsize=8, frameon=True, framealpha=0.9, edgecolor="none")
    ax.minorticks_off()

    fig.text(0.0, -0.01,
             f"{AIRFRAME.name}: m = {AIRFRAME.m} kg, k = {AIRFRAME.drag.k} N·s/m. Noise σ = {SIGMA_DEG}° per 1 s sample, "
             f"n_eff = {N_EFF}.\nWorst case over the signs of b and k-error and over wind speeds 0.5–10 m/s. "
             f"{N_TRIALS:,} trials per point, seed {SEED}.",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig3_requirements_map.{ext}")
    print(f"Saved {out / 'fig3_requirements_map'}.png/.pdf")

    for name, ratio in (("Research", vs_research), ("WMO", vs_wmo)):
        b_max = B_GRID[ratio[0] <= 1].max() if np.any(ratio[0] <= 1) else 0.0
        k_max = K_GRID[ratio[:, 0] <= 1].max() if np.any(ratio[:, 0] <= 1) else 0.0
        print(f"{name:8s}: offset alone up to {b_max:.2f}°, k-error alone up to {100 * k_max:.1f} %")
    for label, (b, k_err) in POINTS.items():
        r = worst_rmse(b, k_err)
        print(f"{label:18s}: worst RMSE {r.max():.2f} m/s | meets research: {np.all(r <= targets.research(V_GRID))}"
              f" | meets WMO: {np.all(r <= targets.wmo(V_GRID))}")


if __name__ == "__main__":
    main()