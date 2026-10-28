"""Figure 7: does Level 1's n_eff = 30 hold if the tilt error is correlated in time?

Noise left in the wind estimate after averaging over T seconds, for tilt errors that stay correlated for tau_c
seconds (Gauss-Markov, A12), with Level 1's 0.5 deg per 1 s sample held fixed. Curves: exact formula.
Dots: Monte Carlo check. numpy only (no RotorPy).
Run from simulations/:  python -m level2_dynamic.noise_averaging_fig7   (under 1 min)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from windmap import airframes, noise, plotstyle, steady, targets

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER
V = 5.0                                    # wind speed at which tilt noise is converted to wind noise [m/s]
SIGMA_1S_DEG = 0.5                         # Level 1 (D4): noise std of one 1 s tilt sample [deg]
OFFSET_DEG = 0.7                           # Level 1 (D4): tilt offset b [deg], shown for scale
T_LEVEL1 = 30.0                            # Level 1's averaging window [s] (n_eff = 30)
TAUS = [0.1, 0.5, 1, 2, 5, 10]             # A12: correlation times tried [s] (unknown for a real drone)
T_GRID = np.logspace(0, 2, 60)             # averaging windows for the curves: 1-100 s
T_MC = [1, 3, 10, 30]                      # windows checked by Monte Carlo [s]
N_WINDOWS = 400                            # Monte Carlo windows of the longest T
DT = 0.05                                  # Monte Carlo time step [s]
SEED = 0


def main():
    plotstyle.apply()
    colours = plotstyle.COLOURS

    S = steady.sensitivity(V, AIRFRAME)                    # wind error per radian of tilt error [m/s per rad]
    sigma_1 = np.deg2rad(SIGMA_1S_DEG)                     # [rad]
    offset_err = S * np.deg2rad(OFFSET_DEG)                # wind bias from the offset [m/s] (first order)
    rng = np.random.default_rng(SEED)

    fig, ax = plt.subplots(figsize=(plotstyle.TEXT_WIDTH_IN, 3.6))
    ax.set_title("Correlated tilt noise: Level 1's n_eff = 30 needs errors that fade within ~0.1 s,\n"
                 "but the noise stays below the offset bias for any correlation time",
                 loc="left", fontsize=10, fontweight="bold")

    # Level 1's assumption: independent 1 s samples, so the noise falls as 1/sqrt(T)
    ax.plot(T_GRID, S * sigma_1 / np.sqrt(T_GRID), color="0.2", lw=1.4,
            label=r"Level 1 assumption: independent 1 s samples ($\sigma/\sqrt{T}$)")

    print(f"tau_c [s] | n_eff for {T_LEVEL1:.0f} s | noise after {T_LEVEL1:.0f} s [m/s] (Level 1: "
          f"{S * sigma_1 / np.sqrt(T_LEVEL1):.3f})")
    for tau, colour in zip(TAUS, colours):
        sigma_x = sigma_1 / np.sqrt(noise.mean_var_ratio(1.0, tau))        # process std giving 0.5 deg per 1 s
        ax.plot(T_GRID, S * sigma_x * np.sqrt(noise.mean_var_ratio(T_GRID, tau)), color=colour, lw=1.2,
                label=rf"Level 2: correlated, $\tau_c$ = {tau:g} s")

        x = noise.gauss_markov(int(N_WINDOWS * max(T_MC) / DT), DT, sigma_x, tau, rng)   # one long record
        mc = [S * x.reshape(-1, int(round(T / DT))).mean(axis=1).std() for T in T_MC]
        ax.plot(T_MC, mc, "o", color=colour, ms=3.5)

        print(f"{tau:9g} | {noise.n_eff(T_LEVEL1, tau):15.1f} | "
              f"{S * sigma_x * np.sqrt(noise.mean_var_ratio(T_LEVEL1, tau)):.3f}")

    ax.axhline(offset_err, color="0.4", ls="--", lw=1.0)
    ax.text(1.05, offset_err + 0.01, f"Offset bias, b = {OFFSET_DEG}° (Level 1): {offset_err:.2f} m/s",
            fontsize=7.5, color="0.35")
    ax.axhline(targets.RESEARCH_RMSE, color="0.4", ls=":", lw=1.0)
    ax.text(98, targets.RESEARCH_RMSE + 0.01, f"Research target: {targets.RESEARCH_RMSE} m/s",
            ha="right", fontsize=7.5, color="0.35")
    ax.axvline(T_LEVEL1, color="0.6", lw=0.8)
    ax.text(T_LEVEL1 * 0.95, 0.38, f"Level 1 window: {T_LEVEL1:.0f} s", ha="right", fontsize=7.5, color="0.35")

    ax.set_xscale("log")
    ax.set_xlim(1, 100)
    ax.set_ylim(0, 0.5)
    ax.set_xticks([1, 2, 5, 10, 20, 50, 100], labels=["1", "2", "5", "10", "20", "50", "100"])
    ax.set_xlabel("Averaging window $T$ [s]")
    ax.set_ylabel("Wind noise left after averaging [m/s]")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=7.5)   # below the axes

    fig.text(0.0, -0.31,
             f"{AIRFRAME.name} at V = {V:.0f} m/s ({np.deg2rad(S):.2f} m/s per degree). Tilt noise "
             f"{SIGMA_1S_DEG}° per 1 s sample held fixed (D4); Gauss-Markov correlation time τ_c (A12).\n"
             f"Curves: exact variance of a T-second mean. Dots: Monte Carlo, {N_WINDOWS} windows of the longest T, "
             f"seed {SEED}. Offset bias to first order (sensitivity × b).",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig7_noise_averaging.{ext}")
    print(f"Saved {out / 'fig7_noise_averaging'}.png/.pdf")


if __name__ == "__main__":
    main()
    
    
