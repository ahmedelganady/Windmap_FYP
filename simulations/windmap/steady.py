# Physics of Drone in steady hover assuming constant horizontal wind: tan(theta) = D(V) / W, with W = m*g (assumption A3).
import numpy as np


def tilt_from_wind(V, af):
    # TRUTH: tilt [rad] the drone af needs to hold position in wind V [m/s].
    return np.arctan(af.drag.force(V) / af.weight)


def wind_from_tilt(theta, af):
    # ESTIMATOR: wind [m/s] worked out from a measured tilt theta [rad], using drone af's model.
    return af.drag.speed(af.weight * np.tan(theta))


def sensitivity(V, af):
    # How much the wind estimate moves per radian of tilt error [m/s per rad], at wind V [m/s].
    # From differentiating W*tan(theta) = D(V):  dV/dtheta = W * (1 + tan^2) / D'(V).
    
    tan_theta = af.drag.force(V) / af.weight
    return af.weight * (1 + tan_theta**2) / af.drag.dforce(V)