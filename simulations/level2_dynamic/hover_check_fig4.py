"""Figure 4: does the RotorPy drone reproduce Level 1's steady tilt?

(a) Steady tilt vs wind: Level 1 model (line) and Level 2 RotorPy runs (dots).
(b) The gap, as the error of Level 1's wind estimate on the Level 2 drone, and the rotor-speed effect that explains it.
Run from simulations/:  python -m level2_dynamic.hover_check_fig4   (about 1.5 min)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from windmap import airframes, dynamic, plotstyle, quad, steady

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER          # A8: RotorPy drone with this m and k
V_RUNS = [0.5, 1, 2, 3, 4, 6, 8, 10]       # constant winds flown [m/s]
T_RUN = 15.0                               # length of each run [s]
T_AVG = 5.0                                # tilt averaged over the last T_AVG seconds [s]
DT = 0.01                                  # D12: 100 Hz
GAINS = "rotorpy"                          # A9 (steady tilt does not depend on the gains)


def corrected_tilt(V, af, n_iter=30):
    """Steady tilt [rad] when rotor drag scales with rotor speed: tan(theta)/sqrt(cos(theta)) = k*V/(m*g).

    In-plane rotor drag carries part of the weight, so thrust falls to m*g*cos(theta); rotor speed goes as
    sqrt(thrust), and so does the effective k. Solved by fixed-point iteration (converges in a few steps).
    """
    c = af.drag.k * np.asarray(V, dtype=float) / af.weight
    theta = np.arctan(c)                                   # start from Level 1's answer
    for _ in range(n_iter):
        theta = np.arctan(c * np.sqrt(np.cos(theta)))
    return theta


def main():
    plotstyle.apply()
    blue, orange = plotstyle.COLOURS[0], plotstyle.COLOURS[1]

    t = np.arange(0, T_RUN + DT / 2, DT)
    theta_sim = []
    for V in V_RUNS:
        r = quad.simulate(AIRFRAME, t, np.full(t.size, float(V)), GAINS)
        theta_sim.append(r["theta"][r["t"] > T_RUN - T_AVG].mean())
        print(f"V = {V:4.1f} m/s done")
    V = np.array(V_RUNS, dtype=float)
    theta_sim = np.array(theta_sim)
    err_sim = 100 * (dynamic.tilt_only(theta_sim, AIRFRAME) / V - 1)       # Level 1 estimate vs truth [%]

    V_fine = np.linspace(0.2, 10.5, 200)
    theta_l1 = steady.tilt_from_wind(V_fine, AIRFRAME)
    theta_corr = corrected_tilt(V_fine, AIRFRAME)
    err_corr = 100 * (steady.wind_from_tilt(theta_corr, AIRFRAME) / V_fine - 1)

    fig, (top, bottom) = plt.subplots(2, 1, sharex=True, figsize=(plotstyle.TEXT_WIDTH_IN, 4.8),
                                      gridspec_kw={"height_ratios": [3, 2], "hspace": 0.08})
    top.set_title(f"Steady wind: Level 2 (RotorPy) reproduces Level 1 to within {abs(err_sim).max():.1f} %",
                  loc="left", fontsize=10, fontweight="bold")

    # (a) The comparison itself: Level 1's formula vs the Level 2 drone, at the same wind speeds
    top.plot(V_fine, np.rad2deg(theta_l1), color="0.3", lw=1.2, label=r"Level 1 model: $\tan\theta = kV/mg$")
    top.plot(V, np.rad2deg(theta_sim), "o", color=blue, label="Level 2 simulation (RotorPy)")
    top.set_ylabel(r"Steady tilt $\theta$ [°]")
    top.legend(loc="lower right")

    # (b) The difference, magnified and expressed as what it costs: error of Level 1's wind estimate
    bottom.axhline(0, color="0.3", lw=1.2, label="Level 1 model (no error by definition)")
    bottom.plot(V_fine, err_corr, "--", color=orange, lw=1.2,
                label=r"Explained by rotor speed: $\tan\theta/\sqrt{\cos\theta} = kV/mg$")
    bottom.plot(V, err_sim, "o", color=blue, label="Level 2 simulation (RotorPy)")
    bottom.set_ylabel("Level 1 wind\nestimate error [%]")
    bottom.set_xlabel(r"Wind speed $V$ [m/s]")
    bottom.set_xlim(0, 10.5)
    bottom.set_ylim(-2.2, 0.5)
    bottom.legend(loc="lower left", fontsize=7.5)
    bottom.text(0.99, 0.88, "For scale: Level 1's k-calibration error is ±15 %",
                transform=bottom.transAxes, ha="right", fontsize=7.5, color="0.35")

    for ax, tag in ((top, "(a)"), (bottom, "(b)")):
        ax.text(0.01, 0.96, tag, transform=ax.transAxes, va="top", fontweight="bold")

    fig.text(0.0, -0.01,
             f"{AIRFRAME.name}: m = {AIRFRAME.m} kg, k = {AIRFRAME.drag.k} N·s/m at hover rotor speed "
             f"({quad.hover_speed(AIRFRAME):.0f} rad/s); other RotorPy aerodynamics off (A8).\n"
             f"Each point: {T_RUN:.0f} s hover in constant wind, {1/DT:.0f} Hz, tilt averaged over the last {T_AVG:.0f} s.",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig4_hover_check.{ext}")
    print(f"Saved {out / 'fig4_hover_check'}.png/.pdf")

    theta_c = corrected_tilt(V, AIRFRAME)
    theta_1 = steady.tilt_from_wind(V, AIRFRAME)
    print("  V [m/s] | RotorPy [°] | Level 1 [°] | corrected [°] | RotorPy - corrected [°] | Vhat error [%]")
    for v, ts, t1, tc, e in zip(V, theta_sim, theta_1, theta_c, err_sim):
        print(f"  {v:7.1f} | {np.rad2deg(ts):11.4f} | {np.rad2deg(t1):11.4f} | {np.rad2deg(tc):13.4f} | "
              f"{np.rad2deg(ts - tc):23.5f} | {e:+14.2f}")


if __name__ == "__main__":
    main()
    
