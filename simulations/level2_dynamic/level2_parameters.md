# Level 2 parameters, decisions and results

Dynamic simulation of the wind estimators in RotorPy 3.0.0 (Python 3.13). Built and run 28 Oct 2026. Level 1's assumptions A1–A7 and decisions D1–D8 still apply; this file adds A8–A13 and D9–D14 and records the results. Level 1's sources are in `level1_steady/error_parameters.md`.

## Summary

| Question | Answer | Figure |
|---|---|---|
| Does the RotorPy drone reproduce Level 1 in steady wind? | Yes, to within 1.8 %. RotorPy matches Level 1 corrected for rotor speed (tan θ/√cos θ = kV/mg) to 10⁻⁵°. | Fig. 4 |
| How fast does each estimator follow a wind step? | Tilt-only (E1): t63 = 0.24 s / 0.47 s, overshoot 23 % / 15 % (RotorPy / PX4-default gains). Accelerometer (E3): within 0.03 m/s throughout. | Fig. 5 |
| Which gusts can each estimator follow? | E1: −3 dB bandwidth 1.19 Hz / 0.47 Hz, i.e. gusts longer than 4.2 m / 10.6 m at U = 5 m/s; it exaggerates mid-frequency gusts by up to 27 % / 16 %. E3: |H| ≈ 1 up to 3 Hz. | Fig. 6 |
| Does lag matter after averaging? | Only for windows under ~5 s (25 m at 5 m/s). By 5 s every estimator is within 0.02 m/s of the 0.03 m/s floor. | Fig. 6c |
| Does n_eff = 30 hold with correlated tilt noise? | Only if errors fade within ~0.1 s. For τ_c = 1 s, n_eff = 11; for 10 s, n_eff = 2. 30 s noise rises from 0.058 to 0.22 m/s, still below the 0.44 m/s offset bias for any τ_c. | Fig. 7 |

**Conclusion.** Calibration (offset b and k/m) still limits accuracy, as in Level 1; the accelerometer estimator removes lag but shares the same calibration. Lag and correlated noise together set a practical minimum averaging window of about 5 s, i.e. about 25 m resolution at 5 m/s.

---

## 1. Assumptions (new in Level 2)

| ID | Assumption | Value | Basis |
|---|---|---|---|
| A8 | RotorPy airframe | Hattenberger (measured) m = 0.554 kg, k = 0.153 N·s/m via k_d = k/(4ω_h) = 7.74×10⁻⁵ kg/rad at ω_h = 494 rad/s. Inertia, arm, thrust/torque coefficients, motor time constant (5 ms) from RotorPy's AscTec Hummingbird (0.50 kg). k_z, k_h, k_flap, parasitic drag = 0 | Steady tilt depends only on k/m; the transient depends on the borrowed inertia and motors |
| A9 | Controller | RotorPy SE3 (geometric PD, no integrator), true-state feedback, attitude gains 544 s⁻², 46.6 s⁻¹. Position gains: RotorPy default k_p = 6.5 s⁻², k_d = 4.0 s⁻¹; PX4-default equivalent k_p = MPC_XY_P × MPC_XY_VEL_P_ACC = 0.95 × 1.8 = 1.71 s⁻², k_d = 1.8 s⁻¹ (velocity integrator and D-term omitted) | Brackets a stiff research controller and a stock autopilot |
| A10 | Wind geometry | Horizontal along x, uniform in space at each instant; longitudinal turbulence only; no vertical wind | Keeps the 1D comparison with Level 1; E3 needs w_z = 0 |
| A11 | Turbulence | MIL-F-8785C low-altitude Dryden, h = 10 m, W20 = U: σ_u = 0.94 m/s (19 %), L_u = 67 m at U = 5 m/s (integral time 13.5 s). Frozen turbulence converts time to distance at U | Standard model, light turbulence near the ground |
| A12 | Sensor errors | Added after each run, open loop. Tilt: Gauss–Markov, σ = 0.5° per 1 s mean (Level 1 value, an upper bound because it also contains estimator dynamics), τ_c swept 0.1–10 s | Separates physics from sensing |
| A13 | Constant errors | Offset b and k-error stay in Level 1's budget; Level 2 estimators use the true k/m | Isolates the dynamics |

## 2. Decisions

| ID | Decision | Why |
|---|---|---|
| D9 | Own Dryden generator: exact AR(1) form of the longitudinal spectrum, a = exp(−U·dt/L_u) | RotorPy's DrydenGust needs PyTorch, fixes the advection speed at 1 m/s and outputs 1–3 % of the requested σ (asked 1.0 m/s, got 0.010–0.031 m/s depending on dt) |
| D10 | Dynamic estimator = accelerometer drag sensing: ŵ = v_x + v_z·tan θ + (m/k)·f_x/cos θ | The thrust-based world-frame form needs a thrust model and is biased by cos²θ when rotor drag acts in the rotor plane (−2.4 % at 5 m/s, about −9 % at 10 m/s). The accelerometer form is used in the field by Wetz & Wildmann (2022) |
| D11 | Metrics: step (t63, overshoot, 2 % settling) and frequency response from Welch cross-spectra (64 s segments); λ_min = U/f_c | The tilt estimator is not first-order (it overshoots), so one time constant would mislead |
| D12 | 100 Hz; runs start at the steady tilt of the first wind value; `terminate=False`; first 20 s of turbulence runs discarded; long runs cached in `data/` | Run time (~0.5 s wall per simulated second) and start-up transient |
| D13 | RotorPy pinned at 3.0.0 | Behaviour checked on this version only |
| D14 | All randomness from `np.random.default_rng(seed)`; RotorPy's own sensor noise unused | Reproducible figures |

**RotorPy details handled in `windmap/quad.py`:** `terminate=False` (otherwise runs stop once settled); SE3 gains set after construction (hard-coded in `__init__`); logged wind taken from our own series (RotorPy's log runs one step ahead); `animate()` called with `filename=None` and saved by us (it otherwise writes into the installed package).

---

## 3. Results

### Fig. 4: hover check (steady wind)

| V [m/s] | RotorPy tilt [°] | Level 1 tilt [°] | Level 1 wind-estimate error [%] |
|---|---|---|---|
| 0.5 | 0.8064 | 0.8064 | −0.00 |
| 2 | 3.2201 | 3.2226 | −0.08 |
| 5 | 7.974 | 8.012 | −0.48 |
| 8 | 12.5447 | 12.6923 | −1.20 |
| 10 | 15.4502 | 15.7231 | −1.82 |

Cause: in-plane rotor drag carries part of the weight, so thrust falls to mg·cos θ, rotor speed to √cos θ and the effective k with it. RotorPy − corrected model = 0.00000° at every speed.

### Fig. 5: 0 → 5 m/s step

| Estimator | t63 [s] | Overshoot [%] | 2 % settling [s] |
|---|---|---|---|
| E1, RotorPy gains | 0.24 | 23.3 | 1.63 |
| E1, PX4-default gains | 0.47 | 15.2 | 3.44 |
| E3 accelerometer | ≈ 0 | – | max error 0.028 m/s |

### Fig. 6: Dryden turbulence (U = 5 m/s, no sensor noise)

| Estimator | Peak \|H\| | at f [Hz] | f_c [Hz] | λ_min = U/f_c [m] |
|---|---|---|---|---|
| E1, RotorPy gains | 1.27 | 0.41 | 1.19 | 4.2 |
| E1, PX4-default gains | 1.16 | 0.17 | 0.47 | 10.6 |
| E3 accelerometer | 1.00 | – | > 3 | < 1.7 |

RMSE of window means [m/s]:

| T [s] | U·T [m] | E1, RotorPy | E1, PX4 | E3 |
|---|---|---|---|---|
| 0.1 | 0.5 | 0.145 | 0.197 | 0.030 |
| 1 | 5 | 0.076 | 0.144 | 0.030 |
| 2 | 10 | 0.049 | 0.100 | 0.030 |
| 5 | 25 | 0.032 | 0.051 | 0.029 |
| 30 | 150 | 0.028 | 0.029 | 0.028 |

The common 0.03 m/s floor is the rotor-speed bias of Fig. 4 at the run's mean wind, not lag.

### Fig. 7: correlated tilt noise (σ = 0.5° per 1 s sample, V = 5 m/s)

| τ_c [s] | n_eff for 30 s | Noise after 30 s [m/s] |
|---|---|---|
| Level 1 (independent) | 30 | 0.058 |
| 0.1 | 27.1 | 0.061 |
| 0.5 | 17.3 | 0.076 |
| 1 | 11.4 | 0.094 |
| 2 | 6.8 | 0.121 |
| 5 | 3.4 | 0.172 |
| 10 | 2.1 | 0.217 |

Exact variance of a T-second mean of a Gauss–Markov process: σ_T² = σ_x² (2/r)[1 − (1 − e^−r)/r], r = T/τ_c. Level 1's note "n_eff ≈ T/(2τ)" is within ~30 % only for τ ≥ 1 s.

### Clips

`clip1_step` (0 → 8 m/s; max lean 15.6°, drift 0.32 m), `clip2_gust` (1−cos, 3 → 7 m/s over 6 s; 11.4°), `clip3_ramp` (0 → 8 m/s over 8 s; 12.8°), `clip4_dryden` (30 s, Fig. 6 settings; lean 4–8°).

---

## 4. Limitations

1. **E3 is optimistic.** RotorPy's rotor aerodynamics are quasi-steady (no inflow lag, no wake); DLR resolved turbulence only up to ~2 Hz in real data. Treat E3's flat |H| as an upper bound.
2. **Borrowed inertia and motors** (A8): the transients in Figs. 5–6 depend on them; the steady results do not.
3. **No integrator** in the SE3 controller: real PX4 holds position with an integral term; steady tilt is unchanged, transients differ slightly.
4. **Dryden under-represents fast gusts** (spectrum falls as f⁻² vs f⁻⁵/³ for von Kármán), so E1's dynamic error is slightly optimistic.
5. **Hover only, 1D wind, no vertical gusts.**

## 5. Open items

1. Measure σ, τ_c (tilt) and accelerometer noise from a 5-minute calm hover log: τ_c decides the averaging window needed (Fig. 7).
2. In-flight identification of k/m: the accuracy floor in both levels.
3. Extensions: vertical gusts (test E3's w_z = 0), moving drone, model-form check with RotorPy's full aerodynamics (+1.3 % at 5 m/s, +9.3 % at 10 m/s on the Hummingbird).

## References

- Folk, S. et al. RotorPy 3.0.0. https://github.com/spencerfolk/rotorpy (source read: `vehicles/multirotor.py`, `controllers/quadrotor_control.py`, `wind/dryden_winds.py`, `wind/dryden_utils.py`, `sensors/imu.py`, `simulate.py`, `environments.py`, `utils/animate.py`)
- Leishman, R.C., Macdonald, J.C., Beard, R.W., McLain, T.W. (2014). Quadrotors and accelerometers: state estimation with an improved dynamic model. *IEEE Control Systems Magazine* 34(1). doi:10.1109/MCS.2013.2287362
- Wetz, T., Wildmann, N. (2022). Spatially distributed and simultaneous wind measurements with a fleet of small quadrotor UAS. *J. Phys.: Conf. Ser.* 2265, 022086. doi:10.1088/1742-6596/2265/2/022086
- Allison, S., Bai, H., Jayaraman, B. (2020). Wind estimation using quadcopter motion: a machine learning approach. *Aerospace Science and Technology*, 105699. doi:10.1016/j.ast.2020.105699
- González-Rocha, J., Woolsey, C.A., Sultan, C., De Wekker, S.F.J. (2019). Sensing wind from quadrotor motion. *J. Guidance, Control, and Dynamics* 42(4). doi:10.2514/1.G003542
- MIL-F-8785C low-altitude Dryden model, as documented by MathWorks: Dryden Wind Turbulence Model (Continuous), Aerospace Blockset.
- PX4 Autopilot, `src/modules/mc_pos_control/mc_pos_control_params.c` (MPC_XY_P 0.95, MPC_XY_VEL_P_ACC 1.8, MPC_XY_VEL_I_ACC 0.4, MPC_XY_VEL_D_ACC 0.2).
