# Accuracy targets for the wind estimate. Each function returns the allowed RMSE [m/s] at wind V [m/s].
import numpy as np

# Research target: match the best published calibrated multirotor systems (0.19-0.39 m/s RMSE;
# Kistner 2024, Wetz 2021, Simma 2020, DJI Air 3S 2026). See level1_steady/error_parameters.md.

RESEARCH_RMSE = 0.3  # [m/s]


def research(V):
    # Research target: 0.3 m/s at every wind speed.
    return np.full_like(np.asarray(V, dtype=float), RESEARCH_RMSE)


def wmo(V):
    # WMO-No. 8 standard for wind instruments: 0.5 m/s below 5 m/s, 10 % of the wind above.
    return np.maximum(0.5, 0.1 * np.abs(np.asarray(V, dtype=float)))