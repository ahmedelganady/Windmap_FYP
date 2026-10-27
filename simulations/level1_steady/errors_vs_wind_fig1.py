"""Figure 1: how big is the wind-estimate error, and what does it look like?

(a) error of the estimate vs true wind: bias line + band holding 95 % of estimates.
(b) total error (RMSE) as a % of the true wind.
Run from simulations/:  python -m level1_steady.fig1_errors_vs_wind
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from windmap import airframes, montecarlo, plotstyle, targets

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER
OFFSET_DEG = 0.7                       # D4: constant tilt offset b [deg] (Hattenberger 2022, see error_parameters.md)
SIGMA_DEG = 0.5                        # D4: noise std of one 1 s tilt sample [deg] (derived, weakest value)
N_EFF = 30                             # D4: 30 s hover average of 1 s samples, assumed independent (A5)
V_GRID = np.linspace(0.5, 10.0, 20)    # D5: true wind speeds [m/s], 0.5 m/s steps
N_TRIALS = 10_000                      # D5
SEED = 0


def main():
    plotstyle.apply()
    blue, orange = plotstyle.COLOURS[0], plotstyle.COLOURS[1]

    rng = np.random.default_rng(SEED)
    r = montecarlo.run_mc(V_GRID, AIRFRAME, AIRFRAME, OFFSET_DEG, SIGMA_DEG, N_EFF, N_TRIALS, rng)
    mean, std = r["mean_err"], r["std"]
    rel_err = 100 * r["rmse"] / V_GRID                       # total error as % of true wind

    fig, (top, bottom) = plt.subplots(2, 1, sharex=True, figsize=(plotstyle.TEXT_WIDTH_IN, 4.6),
                                      gridspec_kw={"height_ratios": [3, 2], "hspace": 0.08})

    # (a) Where the estimates land, relative to the truth
    top.axhline(0, color="0.3", lw=0.8, ls="--", label="Perfect estimate")
    top.fill_between(V_GRID, mean - 2 * std, mean + 2 * std, color=blue, alpha=0.2, lw=0,
                     label=r"95 % of estimates ($\pm2\sigma$, from noise)")
    top.plot(V_GRID, mean, "o-", color=blue, label="Mean error (bias, from offset)")
    top.set_ylabel(r"Estimate error $\hat{V} - V$ [m/s]")
    top.set_ylim(-0.2, 1.0)
    top.legend(loc="center right", bbox_to_anchor=(1.0, 0.3))

    # (b) How big that error is compared with the wind being measured
    bottom.plot(V_GRID, rel_err, "s-", color=orange, label="Estimator (this study)")
    V_fine = np.linspace(0.4, 10.5, 200)
    bottom.plot(V_fine, 100 * targets.research(V_fine) / V_fine, color="0.2", lw=1.0, label=f"Research target ({targets.RESEARCH_RMSE} m/s)")
    bottom.plot(V_fine, 100 * targets.wmo(V_fine) / V_fine, color="0.2", lw=1.0, ls="--", label="WMO standard (0.5 m/s, or 10 % above 5 m/s)")
    bottom.legend(loc="upper right", fontsize=8)
    bottom.set_yscale("log")
    bottom.set_ylim(5, 250)
    bottom.set_yticks([5, 10, 20, 50, 100], labels=["5", "10", "20", "50", "100"])
    bottom.set_ylabel(r"RMSE / $V$ [%]")
    bottom.set_xlabel(r"True wind speed $V$ [m/s]")
    bottom.set_xlim(0, 10.5)

    for ax, tag in ((top, "(a)"), (bottom, "(b)")):
        ax.text(0.01, 0.96, tag, transform=ax.transAxes, va="top", fontweight="bold")

    fig.text(0.0, -0.01,
             f"{AIRFRAME.name}: m = {AIRFRAME.m} kg, k = {AIRFRAME.drag.k} N·s/m.\n"
             f"Tilt offset b = {OFFSET_DEG}°, noise σ = {SIGMA_DEG}° per sample, n_eff = {N_EFF} "
             f"(placeholders, D4). {N_TRIALS:,} trials per wind speed, seed {SEED}.",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):                       # PNG to share, PDF (vector) for the report
        fig.savefig(out / f"fig1_errors_vs_wind.{ext}")
    print(f"Saved {out / 'fig1_errors_vs_wind'}.png/.pdf")
    print(f"Bias {mean.min():.3f}-{mean.max():.3f} m/s, std {std.min():.3f}-{std.max():.3f} m/s, "
          f"RMSE/V {rel_err.max():.0f}% at {V_GRID[0]} m/s -> {rel_err.min():.1f}% at {V_GRID[-1]} m/s")
    print(f"RMSE below 10 % of the wind from {V_GRID[np.argmax(rel_err < 10)]} m/s")


if __name__ == "__main__":
    main()