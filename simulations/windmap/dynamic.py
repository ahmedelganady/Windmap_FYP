# Level 2 wind estimators: each turns the drone's own flight data into a wind estimate [m/s] at every time step.
import numpy as np

from windmap import steady

# E1, tilt-only: Level 1's estimator applied at every instant. Exact only in steady hover.
tilt_only = steady.wind_from_tilt


def accel_based(theta, f_x, v_x, v_z, af):
    # E3, accelerometer drag sensing (D10): wind [m/s] from lean theta [rad], body-x accelerometer f_x [m/s^2]
    # and velocity v_x, v_z [m/s]. Holds during gusts too. Assumes linear rotor drag and no vertical wind (A10).
    return v_x + v_z * np.tan(theta) + (af.m / af.drag.k) * f_x / np.cos(theta)