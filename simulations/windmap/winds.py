# Wind time series for Level 2: a step, a discrete gust and Dryden turbulence (assumptions A10, A11).
# Each function returns the wind along x [m/s] at every time in t [s].
import numpy as np

FT = 3.281  # feet per metre (the MIL-F-8785C formulas are written in feet)


def step(t, t0, w0, w1):
    # Wind jumps from w0 to w1 [m/s] at time t0 [s].
    return np.where(np.asarray(t) >= t0, w1, w0).astype(float)

def ramp(t, t0, t1, w0, w1):
    # Wind rises linearly from w0 to w1 [m/s] between times t0 and t1 [s].
    return np.interp(t, [t0, t1], [w0, w1])

def one_minus_cos(t, t0, U, A, T_g):
    # Discrete gust: mean U [m/s] plus a smooth bump of height A [m/s] lasting T_g [s], starting at t0 [s].
    t = np.asarray(t, dtype=float)
    s = np.clip((t - t0) / T_g, 0.0, 1.0)              # 0 before the gust, 1 after it
    return U + 0.5 * A * (1 - np.cos(2 * np.pi * s))


def dryden_low_altitude(h, W20):
    # MIL-F-8785C low-altitude Dryden values at height h [m], for a wind of W20 [m/s] measured at 6 m (20 ft).
    # Returns (sigma_u [m/s], L_u [m]). The formulas hold from 3 m to 300 m (10-1000 ft).
    h_ft = h * FT
    c = 0.177 + 0.000823 * h_ft
    sigma_u = 0.1 * W20 / c**0.4                       # sigma_w = 0.1*W20, and sigma_u = sigma_w / c^0.4
    L_u = h_ft / c**1.2 / FT                           # longitudinal length scale, converted back to metres
    return sigma_u, L_u


def dryden_u(t, U, sigma_u, L_u, rng):
    # Longitudinal Dryden turbulence on a uniform time grid t [s]: mean U plus gusts with std sigma_u [m/s].
    # The spectrum is first-order with time constant L_u/U, so its exact discrete form is AR(1) (D9):
    #   u[i] = a*u[i-1] + kick,   a = exp(-U*dt/L_u),   kick std = sigma_u*sqrt(1 - a^2)
    t = np.asarray(t, dtype=float)
    dt = t[1] - t[0]
    a = np.exp(-U * dt / L_u)
    kicks = rng.normal(0.0, sigma_u * np.sqrt(1 - a**2), t.size)
    u = np.empty(t.size)
    u[0] = rng.normal(0.0, sigma_u)                    # start inside the turbulence, not at zero
    for i in range(1, t.size):
        u[i] = a * u[i - 1] + kicks[i]
    return U + u