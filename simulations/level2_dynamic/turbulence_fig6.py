"""Figure 6: in realistic turbulence, which gusts can each estimator follow, and what map resolution follows?

(a) 20 s of Dryden turbulence: true wind and the estimates.
(b) Frequency response |H(f)| = estimate/true wind, with the -3 dB bandwidth f_c (top axis: gust length U/f).
(c) Error left after averaging over windows of T seconds (top axis: the distance U*T the wind travels).
No sensor noise: this isolates the dynamic (lag) error. Noise is Figure 7.
Run from simulations/:  python -m level2_dynamic.turbulence_fig6   (about 10 min first time, seconds after)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from windmap import airframes, dynamic, plotstyle, quad, response, winds

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER          # A8
U = 5.0                                    # mean wind [m/s]
HEIGHT = 10.0                              # A11: flight height [m]; W20 = U
T_RUN = 600.0                              # run length [s]
T_DISCARD = 20.0                           # D12: start-up discarded [s]
DT = 0.01                                  # D12: 100 Hz
SEED = 0
WINDOWS = [0.1, 0.2, 0.5, 1, 2, 5, 10, 30] # averaging windows [s]
F_MAX = 3.0                                # frequency range shown [Hz]; Dryden has little energy above
T_ZOOM = (100.0, 120.0)                    # excerpt shown in (a) [s]
NAMES = {"rotorpy": "RotorPy gains", "px4": "PX4-default gains"}   # A9
DATA = Path(__file__).parent / "data"      # cached runs (git-ignored)


def load_or_run(gains, t, wind):
    """RotorPy run in the turbulence, cached: re-runs only if no file exists for these settings."""
    path = DATA / f"dryden_{gains}_U{U}_T{T_RUN:.0f}_seed{SEED}.npz"
    if path.exists():
        return dict(np.load(path))
    print(f"Running RotorPy with {NAMES[gains]} ({T_RUN:.0f} s simulated, a few minutes)...")
    r = quad.simulate(AIRFRAME, t, wind, gains)
    keep = {key: r[key] for key in ("t", "wind", "theta", "f_x", "v_x", "v_z")}
    DATA.mkdir(exist_ok=True)
    np.savez(path, **keep)
    return keep


def main():
    plotstyle.apply()
    blue, orange, aqua = plotstyle.COLOURS[:3]

    sigma_u, L_u = winds.dryden_low_altitude(HEIGHT, U)
    t = np.arange(0, T_RUN + DT / 2, DT)
    wind = winds.dryden_u(t, U, sigma_u, L_u, np.random.default_rng(SEED))     # same gusts for both runs

    # Estimates and their errors, start-up removed
    est = {}
    for g in NAMES:
        r = load_or_run(g, t, wind)
        ok = r["t"] >= T_DISCARD
        est[f"E1, {NAMES[g]}"] = (r["t"][ok], r["wind"][ok], dynamic.tilt_only(r["theta"][ok], AIRFRAME))
        if g == "rotorpy":                  # E3 barely depends on the controller: one run is enough
            e3 = dynamic.accel_based(r["theta"], r["f_x"], r["v_x"], r["v_z"], AIRFRAME)
            est["E3"] = (r["t"][ok], r["wind"][ok], e3[ok])
    style = {"E1, RotorPy gains": (blue, "-"), "E1, PX4-default gains": (orange, "-"), "E3": (aqua, "--")}
    label = {"E1, RotorPy gains": "E1 tilt-only (Level 1 estimator), RotorPy gains",
             "E1, PX4-default gains": "E1 tilt-only (Level 1 estimator), PX4-default gains",
             "E3": "E3 accelerometer (Level 2 estimator)"}

    fig, (ax_a, ax_b, ax_c) = plt.subplots(3, 1, figsize=(plotstyle.TEXT_WIDTH_IN, 8.6),
                                           gridspec_kw={"height_ratios": [1, 1.1, 1.1], "hspace": 0.75})

    # (a) What the estimates look like
    tt, w, _ = est["E3"]
    zoom = (tt >= T_ZOOM[0]) & (tt <= T_ZOOM[1])
    ax_a.plot(tt[zoom], w[zoom], color="0.2", lw=1.0, label="True wind")
    for name, (tt, w, w_hat) in est.items():
        colour, ls = style[name]
        ax_a.plot(tt[zoom], w_hat[zoom], ls, color=colour, lw=1.1, label=label[name])
    ax_a.set_title("(a) A 20 s sample: the Level 1 estimates lag and smooth the gusts", loc="left", fontsize=9)
    ax_a.set_xlabel("Time $t$ [s]")
    ax_a.set_ylabel("Wind [m/s]")

    # (b) Which gust frequencies each estimate captures
    print(f"{'estimator':24s} | peak |H| | at f [Hz] | f_c [Hz] | lambda_min = U/f_c [m]")
    f_c = {}
    for name, (tt, w, w_hat) in est.items():
        f, H = response.freq_response(w, w_hat, 1 / DT)
        show = f <= F_MAX
        mag = np.abs(H[show])
        f_c[name] = response.bandwidth(f[show], mag)
        colour, ls = style[name]
        ax_b.semilogx(f[show], mag, ls, color=colour, lw=1.1)
        if np.isfinite(f_c[name]):
            ax_b.plot(f_c[name], 1 / np.sqrt(2), "o", color=colour, ms=5)
            right = name == "E1, RotorPy gains"         # put each label where its curve leaves space
            ax_b.annotate(f"$f_c$ = {f_c[name]:.2f} Hz ({U / f_c[name]:.0f} m)", (f_c[name], 1 / np.sqrt(2)),
                          xytext=(8, 8) if right else (-8, -8), textcoords="offset points",
                          ha="left" if right else "right", va="bottom" if right else "top",
                          fontsize=7.5, color=colour)
        i = np.argmax(mag)
        print(f"{name:24s} | {mag[i]:8.2f} | {f[show][i]:9.2f} | {f_c[name]:8.2f} | {U / f_c[name]:22.1f}")
    ax_b.axhline(1.0, color="0.2", lw=0.8)
    ax_b.axhline(1 / np.sqrt(2), color="0.5", lw=0.8, ls=":")
    ax_b.text(0.022, 0.74, r"$-3$ dB: only 71 % of the gust is seen", fontsize=7.5, color="0.4")
    ax_b.set_xlim(0.02, F_MAX)
    ax_b.set_ylim(0, 1.45)
    ax_b.set_xticks([0.02, 0.05, 0.1, 0.2, 0.5, 1, 2], labels=["0.02", "0.05", "0.1", "0.2", "0.5", "1", "2"])
    ax_b.set_xlabel("Gust frequency $f$ [Hz]")
    ax_b.set_ylabel("Estimate / true wind $|H(f)|$")
    top_b = ax_b.secondary_xaxis("top", functions=(lambda f: U / np.clip(f, 1e-6, None),
                                                   lambda lam: U / np.clip(lam, 1e-6, None)))
    top_b.set_xticks([200, 100, 50, 20, 10, 5, 2], labels=["200", "100", "50", "20", "10", "5", "2"])
    top_b.set_xlabel(f"Gust length $U/f$ at $U$ = {U:.0f} m/s [m]")
    ax_b.set_title("(b) Which gusts each estimate captures (1 = all of the gust)", loc="left", fontsize=9, pad=30)

    # (c) Error left after averaging
    print(f"\nRMSE of window means [m/s] (no sensor noise)\n{'T [s]':>6s} | {'U*T [m]':>7s} | "
          + " | ".join(f"{name:>22s}" for name in est))
    rmse = {name: [response.window_rmse(w_hat - w, int(round(T / DT))) for T in WINDOWS]
            for name, (tt, w, w_hat) in est.items()}
    for j, T in enumerate(WINDOWS):
        print(f"{T:6.1f} | {U * T:7.1f} | " + " | ".join(f"{rmse[name][j]:22.3f}" for name in est))
    for name in est:
        colour, ls = style[name]
        ax_c.semilogx(WINDOWS, rmse[name], ls, color=colour, marker="o", ms=3.5, lw=1.1)
    ax_c.text(WINDOWS[0], rmse["E3"][0] + 0.006, "Floor shared by all: the 0.5 % rotor-speed bias of Fig. 4",
              fontsize=7.5, color="0.4")
    ax_c.set_ylim(0, None)
    ax_c.set_xticks(WINDOWS, labels=[f"{T:g}" for T in WINDOWS])
    ax_c.set_xlabel("Averaging window $T$ [s]")
    ax_c.set_ylabel("RMSE of window means [m/s]")
    top_c = ax_c.secondary_xaxis("top", functions=(lambda T: U * T, lambda d: d / U))
    top_c.set_xticks([U * T for T in WINDOWS], labels=[f"{U * T:g}" for T in WINDOWS])
    top_c.set_xlabel(f"Distance the wind travels in $T$, $UT$ [m]")
    ax_c.set_title("(c) Error left after averaging over $T$ seconds", loc="left", fontsize=9, pad=30)

    fig.suptitle(f"Turbulence: controller lag hides gusts shorter than {U / f_c['E1, RotorPy gains']:.0f}–"
                 f"{U / f_c['E1, PX4-default gains']:.0f} m from the Level 1 estimator;\n"
                 "averaging over 5 s or more removes nearly all of that error",
                 x=0.02, y=0.995, ha="left", fontsize=10, fontweight="bold")
    handles, labels = ax_a.get_legend_handles_labels()       # one legend serves all three panels
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.02, 0.955), ncol=2, fontsize=7.5)
    fig.subplots_adjust(top=0.86)

    fig.text(0.0, 0.0,
             f"Level 2 simulation (RotorPy), {AIRFRAME.name} hovering. Dryden turbulence (MIL-F-8785C, h = {HEIGHT:.0f} m, "
             f"W20 = U): U = {U:.0f} m/s, σ_u = {sigma_u:.2f} m/s,\nL_u = {L_u:.0f} m; {T_RUN:.0f} s per run, first "
             f"{T_DISCARD:.0f} s discarded, seed {SEED}. No sensor noise. |H| from Welch spectra, 64 s segments.",
             ha="left", va="top", fontsize=7.5, color="0.35")

    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"fig6_turbulence.{ext}")
    print(f"Saved {out / 'fig6_turbulence'}.png/.pdf")


if __name__ == "__main__":
    main()
    
    
