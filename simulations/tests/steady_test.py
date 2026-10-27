# Tests for windmap/airframes.py and windmap/steady.py. Run from simulations/:  python -m pytest -v
import numpy as np
import pytest

from windmap import airframes, drag, steady

H = airframes.HATTENBERGER
QUAD_AF = airframes.Airframe("test quadratic", 1.0, drag.DragModel(a=0.01))  # made-up drone, pure quadratic drag


# --- airframes.py --------------------------------------------------------------
def test_hattenberger_weight():
    np.testing.assert_allclose(H.weight, 0.554 * 9.81, rtol=1e-12)


def test_hattenberger_k():
    assert H.drag.k == 0.153


# --- steady.py: known answers for Hattenberger (measured) ----------------------
def test_tilt_at_5():
    np.testing.assert_allclose(np.rad2deg(steady.tilt_from_wind(5.0, H)), 8.0124, rtol=1e-5)


def test_tilt_at_10():
    np.testing.assert_allclose(np.rad2deg(steady.tilt_from_wind(10.0, H)), 15.7231, rtol=1e-5)


def test_sensitivity_near_zero():
    np.testing.assert_allclose(steady.sensitivity(1e-6, H), 35.521, rtol=1e-5)


def test_sensitivity_at_10():
    np.testing.assert_allclose(steady.sensitivity(10.0, H), 38.3364, rtol=1e-5)


# --- steady.py: behaviour checks -----------------------------------------------
@pytest.mark.parametrize("af", airframes.ALL_AIRFRAMES, ids=[a.name for a in airframes.ALL_AIRFRAMES])
def test_round_trip(af):
    V = np.linspace(-10, 10, 41)
    V_hat = steady.wind_from_tilt(steady.tilt_from_wind(V, af), af)
    np.testing.assert_allclose(V_hat, V, rtol=1e-12, atol=1e-12)


def test_sensitivity_matches_finite_difference_quadratic():
    V = 3.0
    theta = steady.tilt_from_wind(V, QUAD_AF)
    h = 1e-6  # [rad]
    fd = (steady.wind_from_tilt(theta + h, QUAD_AF) - steady.wind_from_tilt(theta - h, QUAD_AF)) / (2 * h)
    np.testing.assert_allclose(steady.sensitivity(V, QUAD_AF), fd, rtol=1e-6)