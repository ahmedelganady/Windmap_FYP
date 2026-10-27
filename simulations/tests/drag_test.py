# Tests for windmap/drag.py. Run from simulations/:  python -m pytest -v

import numpy as np
import pytest

from windmap.drag import DragModel

LINEAR = DragModel(k=0.230)
QUADRATIC = DragModel(a=0.01)
COMBINED = DragModel(k=0.230, a=0.01)
MODELS = [LINEAR, QUADRATIC, COMBINED]
MODEL_IDS = ["linear", "quadratic", "combined"]


def test_linear_force():
    np.testing.assert_allclose(LINEAR.force(5.0), 1.15, rtol=1e-12)


def test_quadratic_force_is_odd():
    np.testing.assert_allclose(QUADRATIC.force([-2, 0, 2]), [-0.04, 0, 0.04], rtol=1e-12, atol=1e-15)


@pytest.mark.parametrize("model", MODELS, ids=MODEL_IDS)
def test_round_trip(model):
    V = np.linspace(-10, 10, 41)
    np.testing.assert_allclose(model.speed(model.force(V)), V, rtol=1e-12, atol=1e-12)


def test_speed_at_zero_drag_is_zero_not_nan():
    assert QUADRATIC.speed(0.0) == 0.0


def test_tiny_quadratic_term_is_stable():
    # The textbook root gives 4.996 here; the rationalised root must give 5.000.
    np.testing.assert_allclose(DragModel(k=0.23, a=1e-15).speed(1.15), 5.0, rtol=1e-9)


@pytest.mark.parametrize("model", MODELS, ids=MODEL_IDS)
def test_dforce_matches_finite_difference(model):
    V = np.array([-7.0, -1.5, 0.5, 3.0, 9.0])  # avoid V = 0 (see notes)
    h = 1e-6
    fd = (model.force(V + h) - model.force(V - h)) / (2 * h)
    np.testing.assert_allclose(model.dforce(V), fd, rtol=1e-6)


def test_invalid_coefficients_raise():
    with pytest.raises(ValueError):
        DragModel()
    with pytest.raises(ValueError):
        DragModel(k=-1)
    with pytest.raises(ValueError):
        DragModel(a=-0.01)