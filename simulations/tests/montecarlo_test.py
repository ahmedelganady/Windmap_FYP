# Tests for windmap/montecarlo.py. Run from simulations/:  python -m pytest -v
import numpy as np

from windmap import airframes, drag, montecarlo, steady

H = airframes.HATTENBERGER
H_K_PLUS_10 = airframes.Airframe("Hattenberger k+10%", H.m, drag.DragModel(k=1.1 * H.drag.k))  # wrong model
V_GRID = np.linspace(0.5, 10.0, 20)  # [m/s]


def mc(V=V_GRID, est=H, offset_deg=0.0, sigma_deg=0.0, n_eff=10, n_trials=10_000, seed=0):
    """Run run_mc with Hattenberger as truth. Defaults: no errors. Change only what a test needs."""
    return montecarlo.run_mc(V, H, est, offset_deg, sigma_deg, n_eff, n_trials, np.random.default_rng(seed))


def test_no_errors_gives_zero():
    r = mc()
    for key in ("mean_err", "std", "rmse"):
        np.testing.assert_allclose(r[key], 0.0, atol=1e-12)


def test_offset_only_gives_exact_bias():
    r = mc(V=[5.0], offset_deg=1.0)
    theta = steady.tilt_from_wind(5.0, H)
    exact = H.weight / H.drag.k * (np.tan(theta + np.deg2rad(1.0)) - np.tan(theta))  # by hand
    np.testing.assert_allclose(r["mean_err"], exact, rtol=1e-12)
    np.testing.assert_allclose(exact, 0.634, rtol=2e-3)
    np.testing.assert_allclose(r["std"], 0.0, atol=1e-12)


def test_noise_only_std_matches_sensitivity():
    r = mc(V=[5.0], sigma_deg=0.5, n_eff=10)
    expected_std = steady.sensitivity(5.0, H) * np.deg2rad(0.5 / np.sqrt(10))
    np.testing.assert_allclose(r["mean_err"], 0.0, atol=0.01)
    np.testing.assert_allclose(r["std"], expected_std, rtol=0.03)


def test_rmse_identity():
    r = mc(est=H_K_PLUS_10, offset_deg=1.0, sigma_deg=0.5)
    np.testing.assert_allclose(r["rmse"]**2, r["mean_err"]**2 + r["std"]**2, rtol=1e-10)


def test_k_too_big_underestimates_wind_by_one_eleventh():
    r = mc(est=H_K_PLUS_10)
    np.testing.assert_allclose(r["mean_err"], -V_GRID * 0.1 / 1.1, rtol=1e-12)


def test_heading_flip_removes_offset_keeps_noise():
    rng = np.random.default_rng(1)
    flip = montecarlo.run_mc_heading_flip(V_GRID, H, H, 1.0, 0.5, 10, 10_000, rng)
    plain = mc(sigma_deg=0.5)
    np.testing.assert_allclose(flip["mean_err"], 0.0, atol=0.01)     # offset cancelled
    np.testing.assert_allclose(flip["std"], plain["std"], rtol=0.05)  # same flight time, same noise