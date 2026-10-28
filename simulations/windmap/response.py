# How well an estimate follows the true wind: step metrics, frequency response, and RMSE of window means (D11).
import numpy as np
from scipy import signal


def step_metrics(t, y, t0, y0, y1):
    # Response y to a step from y0 to y1 at time t0 [s]. Returns (t63 [s], overshoot [%], 2 % settling time [s]).
    after = t >= t0
    tt, frac = t[after] - t0, (y[after] - y0) / (y1 - y0)   # time since the step, fraction of the way there
    t63 = tt[np.argmax(frac >= 0.632)]                      # first time it covers 63.2 % of the step
    overshoot = 100 * max(frac.max() - 1, 0.0)
    outside = np.flatnonzero(np.abs(frac - 1) > 0.02)       # samples still more than 2 % away from the end value
    settle = tt[outside[-1] + 1] if outside.size else 0.0   # first sample after the last one outside the band
    return t63, overshoot, settle


def freq_response(w, w_hat, fs, seg_s=64.0):
    # Transfer function H(f) = w_hat/w from a long run [complex], via averaged spectra over seg_s-second segments.
    n = int(seg_s * fs)
    f, P_wy = signal.csd(w, w_hat, fs=fs, nperseg=n)        # cross-spectrum: what w_hat shares with w
    _, P_ww = signal.welch(w, fs=fs, nperseg=n)             # power spectrum of the true wind
    return f[1:], P_wy[1:] / P_ww[1:]                       # drop f = 0 (the mean is removed in each segment)


def bandwidth(f, H_mag):
    # -3 dB bandwidth f_c [Hz]: first frequency where |H| falls below 1/sqrt(2), interpolated on log f.
    # Returns nan if |H| never falls that low in the range covered (e.g. a near-perfect estimator).
    below = np.flatnonzero(H_mag < 1 / np.sqrt(2))
    if below.size == 0 or below[0] == 0:
        return np.nan
    i = below[0]
    frac = (H_mag[i - 1] - 1 / np.sqrt(2)) / (H_mag[i - 1] - H_mag[i])
    return np.exp(np.log(f[i - 1]) + frac * (np.log(f[i]) - np.log(f[i - 1])))


def window_rmse(e, n):
    # RMSE [same units as e] of the means of consecutive n-sample windows of the error e (the tail is dropped).
    m = e.size // n
    return np.sqrt(np.mean(e[: m * n].reshape(m, n).mean(axis=1) ** 2))