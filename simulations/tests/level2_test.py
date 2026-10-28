# Tests for the Level 2 package files (winds, dynamic, noise, response). No RotorPy, so they run in seconds.
# Run from simulations/:  python -m pytest -v
import numpy as np
from scipy import signal

from windmap import airframes, dynamic, noise, response, steady, winds

H = airframes.HATTENBERGER
RNG = np.random.default_rng


# winds.py
def test_step_and_gust_shapes():
    t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    np.testing.assert_allclose(winds.step(t, 2.0, 1.0, 5.0), [1, 1, 5, 5, 5])
    np.testing.assert_allclose(winds.one_minus_cos(t, 1.0, 3.0, 4.0, 2.0), [3, 3, 7, 3, 3], atol=1e-12)


def test_dryden_low_altitude_values():
    sigma_u, L_u = winds.dryden_low_altitude(10, 5)
    np.testing.assert_allclose([sigma_u, L_u], [0.944, 67.4], rtol=2e-3)


def test_dryden_std_and_memory():
    t = np.arange(0, 1000, 0.01)                       # L_u/U = 0.1 s, so 10^5 samples settle the statistics
    u = winds.dryden_u(t, 10.0, 1.0, 1.0, RNG(0)) - 10.0
    np.testing.assert_allclose(u.std(), 1.0, rtol=0.03)
    np.testing.assert_allclose(np.corrcoef(u[:-1], u[1:])[0, 1], np.exp(-10 * 0.01 / 1.0), atol=0.01)


# dynamic.py
def test_estimators_agree_in_steady_hover():
    V = np.linspace(0.5, 10, 20)
    theta = steady.tilt_from_wind(V, H)
    f_x = 9.81 * np.sin(theta)                         # steady state: accelerometer reads gravity's share
    np.testing.assert_allclose(dynamic.tilt_only(theta, H), V, rtol=1e-12)
    np.testing.assert_allclose(dynamic.accel_based(theta, f_x, 0.0, 0.0, H), V, rtol=1e-12)


def test_accel_based_inverts_the_drag_law_while_moving():
    rng = RNG(1)
    w, v_x, v_z = rng.uniform(-8, 8, 50), rng.uniform(-2, 2, 50), rng.uniform(-1, 1, 50)
    theta = rng.uniform(-0.3, 0.3, 50)
    f_x = -(H.drag.k / H.m) * ((v_x - w) * np.cos(theta) + v_z * np.sin(theta))   # in-plane rotor drag / m
    np.testing.assert_allclose(dynamic.accel_based(theta, f_x, v_x, v_z, H), w, rtol=1e-12)


# noise.py
def test_n_eff_values_and_limits():
    np.testing.assert_allclose(noise.n_eff(30, 1.0), 11.42, rtol=1e-3)
    np.testing.assert_allclose(noise.mean_var_ratio(1000, 1.0), 2 / 1000, rtol=2e-3)   # long average: white-noise limit
    np.testing.assert_allclose(noise.mean_var_ratio(0.001, 1.0), 1.0, rtol=1e-3)       # short average: no reduction


def test_gauss_markov_averaging_matches_formula():
    tau, dt = 1.0, 0.05
    sigma = 0.5 / np.sqrt(noise.mean_var_ratio(1, tau))      # 0.5 per 1 s mean, as in Level 1
    x = noise.gauss_markov(2000 * 600, dt, sigma, tau, RNG(0))
    np.testing.assert_allclose(x.reshape(-1, 20).mean(axis=1).std(), 0.5, rtol=0.03)
    np.testing.assert_allclose(x.reshape(2000, 600).mean(axis=1).std(),
                               sigma * np.sqrt(noise.mean_var_ratio(30, tau)), rtol=0.05)


# response.py
def test_metrics_on_a_first_order_lag():
    dt, tau = 0.01, 0.5
    t = np.arange(0, 10, dt)
    y = np.where(t >= 1, 1 - np.exp(-(t - 1) / tau), 0.0)
    t63, overshoot, settle = response.step_metrics(t, y, 1.0, 0.0, 1.0)
    np.testing.assert_allclose([t63, overshoot, settle], [tau, 0.0, tau * np.log(50)], atol=0.011)

    a = np.exp(-dt / tau)
    x = RNG(0).normal(size=200_000)
    f, Hf = response.freq_response(x, signal.lfilter([1 - a], [1, -a], x), 1 / dt)
    np.testing.assert_allclose(response.bandwidth(f, np.abs(Hf)), 1 / (2 * np.pi * tau), rtol=0.02)


def test_window_rmse():
    e = np.tile([1.0, -1.0], 50)                        # alternating error averages out in 2-sample windows
    np.testing.assert_allclose(response.window_rmse(e, 2), 0.0, atol=1e-12)
    np.testing.assert_allclose(response.window_rmse(e, 1), 1.0)