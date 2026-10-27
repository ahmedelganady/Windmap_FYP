"""Figure 2: what limits accuracy, and what is left after the heading-flip fix?

(a) Before any fix: each error source on its own, and all of them together.
(b) After the heading flip (offset cancelled): what remains.
Sources whose sign is unknown (k-error, and the combined case) are shown as a band
between the sign that cancels and the sign that adds.
Run from simulations/:  python -m level1_steady.error_budget_fig2
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from windmap import airframes, drag, montecarlo, plotstyle

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER
OFFSET_DEG = 0.7                       # D4: constant tilt offset b [deg] (Hattenberger 2022, see error_parameters.md)
SIGMA_DEG = 0.5                        # D4: noise std of one 1 s tilt sample [deg] (derived, weakest value)
N_EFF = 30                             # D4: 30 s hover average of 1 s samples, assumed independent (A5)
K_ERR = 0.15                           # D7: estimator k off by ±15 % (Hattenberger 2023: 14-20 % tunnel vs flight)
V_GRID = np.linspace(0.5, 10.0, 20)    # D5: true wind speeds [m/s]
N_TRIALS = 10_000                      # D5
SEED = 0


def rmse(fn, offset, sigma, k_factor):
    """RMSE [m/s] at every wind speed for one error setting. Same seed every time, so lines are comparable."""
    est = airframes.Airframe("estimator", AIRFRAME.m, drag.DragModel(k=k_factor * AIRFRAME.drag.k))
    rng = np.random.default_rng(SEED)
    return fn(V_GRID, AIRFRAME, est, offset, sigma, N_EFF, N_TRIALS, rng)["rmse"]


def sign_range(fn, offset, sigma):
    """Lowest and highest RMSE over the unknown signs of the offset and the k-error."""
    runs = [rmse(fn, s_b * offset, sigma, 1 + s_k * K_ERR) for s_b in (1, -1) for s_k in (1, -1)]
    return np.min(runs, axis=0), np.max(runs, axis=0)


def main():
    plotstyle.apply()
    blue, orange, aqua = plotstyle.COLOURS[:3]
    grey = "0.25"

    # (a) no fix
    offset_only = rmse(montecarlo.run_mc, OFFSET_DEG, 0.0, 1.0)
    noise_only = rmse(montecarlo.run_mc, 0.0, SIGMA_DEG, 1.0)
    k_lo, k_hi = sign_range(montecarlo.run_mc, 0.0, 0.0)
    all_lo, all_hi = sign_range(montecarlo.run_mc, OFFSET_DEG, SIGMA_DEG)
    # (b) heading flip: offset is still there, but cancels
    noise_flip = rmse(montecarlo.run_mc_heading_flip, OFFSET_DEG, SIGMA_DEG, 1.0)
    flip_lo, flip_hi = sign_range(montecarlo.run_mc_heading_flip, OFFSET_DEG, SIGMA_DEG)

    fig, (top, bottom) = plt.subplots(2, 1, sharex=True, sharey=True,
                                      figsize=(plotstyle.TEXT_WIDTH_IN, 5.2),
                                      gridspec_kw={"hspace": 0.08})

    for ax, noise, lo, hi in ((top, noise_only, all_lo, all_hi), (bottom, noise_flip, flip_lo, flip_hi)):
        ax.fill_between(V_GRID, lo, hi, color=grey, alpha=0.18, lw=0, label="All combined (range over signs)")
        ax.plot(V_GRID, lo, color=grey, lw=0.8)
        ax.plot(V_GRID, hi, color=grey, lw=0.8)
        ax.fill_between(V_GRID, k_lo, k_hi, color=aqua, alpha=0.45, lw=0,
                        label=rf"k-error only ($\pm${K_ERR:.0%})")
        ax.plot(V_GRID, noise, "^-", color=orange, label="Noise only")
        ax.set_ylabel("RMSE [m/s]")

    top.plot(V_GRID, offset_only, "o-", color=blue)
    bottom.plot(V_GRID, offset_only, "o--", color=blue, alpha=0.35, label="Offset only (faded: cancelled by flip)")

    top.set_ylim(0, 2.7)
    bottom.set_xlabel(r"True wind speed $V$ [m/s]")
    bottom.set_xlim(0, 10.5)
    for ax, tag in ((top, "(a) No correction"), (bottom, "(b) With heading flip")):
        ax.text(0.01, 0.96, tag, transform=ax.transAxes, va="top", fontweight="bold")
    handles, labels = bottom.get_legend_handles_labels()            # one legend serves both panels
    bottom.legend(handles[::-1], labels[::-1], loc="upper left", bbox_to_anchor=(0.0, 0.88))  # reversed: offset first

    fig.text(0.0, -0.01,
             f"{AIRFRAME.name}: m = {AIRFRAME.m} kg, k = {AIRFRAME.drag.k} N·s/m. "
             f"Tilt offset b = ±{OFFSET_DEG}°, noise σ = {SIGMA_DEG}° per sample, n_eff = {N_EFF} (placeholders, D4).\n"
             f"Estimator k off by ±{K_ERR:.0%} (D7, from the 14-20 % wind-tunnel vs flight gap in Hattenberger et al. 2023). "
             f"{N_TRIALS:,} trials per wind speed, seed {SEED}.",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig2_error_budget.{ext}")
    print(f"Saved {out / 'fig2_error_budget'}.png/.pdf")

    cross = V_GRID[np.argmax(k_lo > offset_only)], V_GRID[np.argmax(k_hi > offset_only)]
    print(f"k-error overtakes offset between {min(cross)} and {max(cross)} m/s")
    for v in (1.0, 5.0, 10.0):
        i = np.argmin(abs(V_GRID - v))
        print(f"V = {v:4.1f} m/s | combined {all_lo[i]:.2f}-{all_hi[i]:.2f} | "
              f"with flip {flip_lo[i]:.2f}-{flip_hi[i]:.2f} m/s")


if __name__ == "__main__":
    main()