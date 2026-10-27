# Drag models for a quadcopter hovering in 'horizontal' wind.
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DragModel:
    # Horizontal drag D(V) = k*V + a*V*|V|  [N]. Coefficients constant (A4).

    k: float = 0.0  # linear coefficient [N·s/m]
    a: float = 0.0  # quadratic coefficient [kg/m] = 0.5*rho*C_D*A

    def __post_init__(self):
        # Reject negative coefficients, and k = a = 0 (no drag -> no inverse).
        
        if self.k < 0 or self.a < 0:
            raise ValueError(f"Drag coefficients must be >= 0 (got k={self.k}, a={self.a})")
        if self.k == 0 and self.a == 0:
            raise ValueError("k and a cannot both be 0: zero drag cannot be inverted")

    def force(self, V):
        # Drag [N] for signed airspeed V [m/s]. Scalar or array.
        
        V = np.asarray(V, dtype=float)
        return self.k * V + self.a * V * np.abs(V)

    def speed(self, D):
        # Inverse of force: signed airspeed [m/s] from signed drag D [N].
        
        D = np.asarray(D, dtype=float)
        if self.k == 0:
            # Pure quadratic: D = a*V*|V|  ->  V = sign(D) * sqrt(|D| / a)
            return np.sign(D) * np.sqrt(np.abs(D) / self.a)
        
        # Rationalised root of a*V^2 + k*V = |D|, with signed D on top so the sign comes out right.
        # Denominator >= 2k > 0, so this never divides by zero.
        return 2 * D / (self.k + np.sqrt(self.k**2 + 4 * self.a * np.abs(D)))

    def dforce(self, V):
        # Derivative dD/dV [N·s/m] at airspeed V [m/s].
        
        V = np.asarray(V, dtype=float)
        return self.k + 2 * self.a * np.abs(V)