"""Four short animations of the Level 2 drone (RotorPy's own 3D animation, side view):
a wind step (0 to 8 m/s), a 1-cos gust (+4 m/s over 6 s on a 3 m/s mean), a ramp (0 to 8 m/s over 8 s)
and 30 s of Dryden turbulence (the Fig. 6 settings). The red arrow is the wind.
Saved as MP4 if ffmpeg is installed, otherwise as GIF.
Run from simulations/:  python -m level2_dynamic.clips   (about 5 min)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # draw off-screen: no window pops up while frames render
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from rotorpy.utils.animate import animate
from rotorpy.world import World
from scipy.spatial.transform import Rotation

from windmap import airframes, quad, winds

# --- Assumptions: every number lives here and nowhere else --------------------
AIRFRAME = airframes.HATTENBERGER          # A8
DT = 0.01                                  # D12: 100 Hz
BOX = 0.6                                  # half-width of the view [m]: small, so the drone and its lean are visible


def clips():
    # Each clip: (file name, length [s], wind series as a function of t, title)
    return [
        ("clip1_step", 6.0, lambda t: winds.step(t, 1.0, 0.0, 8.0),
         "Wind steps from 0 to 8 m/s: the drone leans into it and drifts downwind"),
        ("clip2_gust", 14.0, lambda t: winds.one_minus_cos(t, 2.0, 3.0, 4.0, 6.0),
         "1-cos gust, 3 to 7 m/s and back over 6 s: the lean rises and falls with it, slightly late"),
        ("clip3_ramp", 14.0, lambda t: winds.ramp(t, 2.0, 10.0, 0.0, 8.0),
         "Wind ramps from 0 to 8 m/s over 8 s: the lean grows steadily, just behind the wind"),
        ("clip4_dryden", 30.0,
         lambda t: winds.dryden_u(t, 5.0, *winds.dryden_low_altitude(10.0, 5.0), np.random.default_rng(0)),
         "30 s of Dryden turbulence (5 m/s mean, as in Fig. 6): the lean follows the slow swings"),
    ]


def main():
    out = Path(__file__).parent / "figures"
    out.mkdir(exist_ok=True)
    writer, ext = ("ffmpeg", "mp4") if animation.writers.is_available("ffmpeg") else ("pillow", "gif")

    for name, T, wind_fn, title in clips():
        t = np.arange(0, T + DT / 2, DT)
        r = quad.simulate(AIRFRAME, t, wind_fn(t), "rotorpy")
        n = r["t"].size
        position = np.column_stack([r["x"], np.zeros(n), r["z"]])         # animate() wants (N, 3) arrays
        wind = np.column_stack([r["wind"], np.zeros(n), np.zeros(n)])
        rotation = Rotation.from_quat(r["q"]).as_matrix()                 # (N, 3, 3), RotorPy's [x, y, z, w] order

        ani = animate(r["t"], position, rotation, wind, animate_wind=True,
                      world=World.empty((-BOX, BOX, -BOX, BOX, -BOX, BOX)), filename=None)
        fig = plt.gcf()                                                   # the figure animate() just made
        fig.axes[0].view_init(elev=0, azim=-90)
        fig.suptitle(title, fontsize=10)
        path = out / f"{name}.{ext}"
        ani.save(path, writer=writer, fps=30, dpi=100)
        plt.close(fig)
        print(f"Saved {path}  (max lean {np.rad2deg(r['theta'].max()):.1f}°, max drift {r['x'].max():.2f} m)")
        
if __name__ == "__main__":
    main()
    
