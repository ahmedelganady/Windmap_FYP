# Monte Carlo error analysis - add random (Gaussian) sensor errors ("noise") to the tilt, estimate the wind, measure the error.
import numpy as np

from windmap import steady


def _metrics(V_hat, V_grid):
    # Error stats over the trials. Each output has one value per wind speed [m/s].
    e = V_hat - V_grid                                # error of every trial at every wind speed
    return {
        "mean_err": np.mean(e, axis=0),               # systematic part (bias)
        "std": np.std(e, axis=0),                     # random part (spread)
        "rmse": np.sqrt(np.mean(e**2, axis=0)),       # total
    }


def run_mc(V_grid, truth, est, offset_deg, sigma_deg, n_eff, n_trials, rng):
    """Simulate n_trials tilt measurements at each wind speed and return the wind-estimate errors.

    V_grid      true wind speeds [m/s]
    truth       drone that generates the real tilt
    est         drone model the estimator assumes (same as truth = perfect model)
    offset_deg  constant tilt offset b [deg]
    sigma_deg   noise std of one tilt sample [deg]
    n_eff       number of independent samples averaged (A5)
    n_trials    Monte Carlo trials per wind speed
    rng         random number generator, e.g. np.random.default_rng(0)
    """
    
    V_grid = np.asarray(V_grid, dtype=float)
    theta_true = steady.tilt_from_wind(V_grid, truth)            # one tilt per wind speed [rad]
    b = np.deg2rad(offset_deg)
    sigma_avg = np.deg2rad(sigma_deg) / np.sqrt(n_eff)           # noise left after averaging (D2)
    noise = rng.normal(0.0, sigma_avg, size=(n_trials, V_grid.size))
    theta_meas = theta_true + b + noise                          # rows = trials, columns = wind speeds
    V_hat = steady.wind_from_tilt(theta_meas, est)
    return _metrics(V_hat, V_grid)


def run_mc_heading_flip(V_grid, truth, est, offset_deg, sigma_deg, n_eff, n_trials, rng):
    """Same as run_mc, but the drone spends half the time facing the other way (D8).

    The offset b is fixed to the drone, so it keeps its sign; the wind tilt flips sign.
    Half the difference of the two readings cancels b. Each half averages n_eff/2 samples.
    Assumes b and the wind are the same on both halves.
    """
    V_grid = np.asarray(V_grid, dtype=float)
    theta_true = steady.tilt_from_wind(V_grid, truth)
    b = np.deg2rad(offset_deg)
    sigma_half = np.deg2rad(sigma_deg) / np.sqrt(n_eff / 2)
    shape = (n_trials, V_grid.size)
    theta_0 = theta_true + b + rng.normal(0.0, sigma_half, size=shape)      # facing 0°
    theta_180 = -theta_true + b + rng.normal(0.0, sigma_half, size=shape)   # facing 180°
    theta_hat = 0.5 * (theta_0 - theta_180)                                 # b cancels here
    V_hat = steady.wind_from_tilt(theta_hat, est)
    return _metrics(V_hat, V_grid)