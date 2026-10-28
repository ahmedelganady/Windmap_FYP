# Correlated sensor error (A12): a Gauss-Markov process, and how much averaging really reduces it.
import numpy as np


def gauss_markov(n, dt, sigma, tau, rng):
    # n samples, dt [s] apart, of a random error with std sigma that stays correlated for about tau [s].
    # Exact AR(1) form: x[i] = a*x[i-1] + kick,  a = exp(-dt/tau),  kick std = sigma*sqrt(1 - a^2)
    a = np.exp(-dt / tau)
    kicks = rng.normal(0.0, sigma * np.sqrt(1 - a**2), n)
    x = np.empty(n)
    x[0] = rng.normal(0.0, sigma)
    for i in range(1, n):
        x[i] = a * x[i - 1] + kicks[i]
    return x


def mean_var_ratio(T, tau):
    # Variance of a T-second average of the process, as a fraction of its own variance (r = T/tau).
    # Short tau: falls like 2*tau/T, as for white noise. Long tau: stays near 1, so averaging barely helps.
    r = T / tau
    return (2 / r) * (1 - (1 - np.exp(-r)) / r)


def n_eff(T, tau, T1=1.0):
    # How many independent T1-second samples a T-second average is really worth (Level 1 assumed T/T1 = 30).
    return mean_var_ratio(T1, tau) / mean_var_ratio(T, tau)