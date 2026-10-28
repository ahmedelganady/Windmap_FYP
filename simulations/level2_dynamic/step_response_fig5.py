"""Figure 5: how fast does each estimator follow a sudden change in wind?

Wind steps from 0 to 5 m/s. Level 1's tilt-only estimator (E1), run on the Level 2 drone with two controllers,
against the accelerometer estimator (E3).
Run from simulations/:  python -m level2_dynamic.step_response_fig5   (about 20 s)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from windmap import airframes, dynamic, plotstyle, quad, response, winds

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER          # A8
W0, W1, T_STEP = 0.0, 5.0, 1.0             # wind steps from W0 to W1 [m/s] at T_STEP [s]
T_RUN = 12.0                               # run length [s]; settling needs ~3.5 s with PX4 gains
DT = 0.01                                  # D12: 100 Hz
T_PLOT = 6.0                               # plotted window [s]
NAMES = {"rotorpy": "RotorPy gains", "px4": "PX4-default gains"}   # A9


def main():
    plotstyle.apply()
    blue, orange, aqua = plotstyle.COLOURS[:3]

    t = np.arange(0, T_RUN + DT / 2, DT)
    wind = winds.step(t, T_STEP, W0, W1)
    runs = {g: quad.simulate(AIRFRAME, t, wind, g) for g in NAMES}     # one RotorPy run per gain set

    fig, ax = plt.subplots(figsize=(plotstyle.TEXT_WIDTH_IN, 3.6))
    ax.set_title("Wind step: the Level 1 tilt estimate lags and overshoots; the accelerometer does not",
                 loc="left", fontsize=10, fontweight="bold")
    r = runs["rotorpy"]
    ax.plot(r["t"], r["wind"], color="0.2", lw=1.0, label="True wind")

    print(f"{'estimator':32s} | t63 [s] | overshoot [%] | settling 2 % [s]")
    for g, colour in (("rotorpy", blue), ("px4", orange)):
        r = runs[g]
        e1 = dynamic.tilt_only(r["theta"], AIRFRAME)
        t63, over, settle = response.step_metrics(r["t"], e1, T_STEP, W0, W1)
        print(f"{'E1 tilt-only, ' + NAMES[g]:32s} | {t63:7.2f} | {over:13.1f} | {settle:16.2f}")
        ax.plot(r["t"], e1, color=colour,
                label=f"E1 tilt-only (Level 1 estimator), {NAMES[g]}: "
                      f"$t_{{63}}$ = {t63:.2f} s, overshoot {over:.0f} %")

    r = runs["rotorpy"]                     # E3 barely depends on the controller, so one run is enough
    e3 = dynamic.accel_based(r["theta"], r["f_x"], r["v_x"], r["v_z"], AIRFRAME)
    max_err = np.abs(e3 - r["wind"]).max()
    print(f"{'E3 accelerometer':32s} | max |error| = {max_err:.3f} m/s")
    ax.plot(r["t"], e3, "--", color=aqua, label=f"E3 accelerometer (Level 2 estimator): max error {max_err:.2f} m/s")

    ax.set_xlim(0, T_PLOT)
    ax.set_ylim(-0.3, 6.6)
    ax.set_xlabel("Time $t$ [s]")
    ax.set_ylabel("Wind and its estimates [m/s]")
    ax.legend(loc="lower right", fontsize=7.5)

    fig.text(0.0, -0.01,
             f"Level 2 simulation (RotorPy): {AIRFRAME.name} hovering; wind steps {W0:.0f} to {W1:.0f} m/s at "
             f"t = {T_STEP:.0f} s, {1/DT:.0f} Hz, no sensor noise.\n"
             r"SE3 position gains: RotorPy $k_p$ = 6.5 s$^{-2}$, $k_d$ = 4.0 s$^{-1}$; "
             r"PX4-default $k_p$ = 1.71 s$^{-2}$, $k_d$ = 1.8 s$^{-1}$ (A9).",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig5_step_response.{ext}")
    print(f"Saved {out / 'fig5_step_response'}.png/.pdf")


if __name__ == "__main__":
    main()
    
