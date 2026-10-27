# Level 1 error parameters: values and sources

Sources for the sensor-error values (decision D4) and the drag-calibration error (D7) used in the Level 1 figures. Researched 27 Oct 2026.

## Summary

| Symbol | Meaning | Old placeholder | **Value used** | Source | Confidence |
|---|---|---|---|---|---|
| b | Constant tilt offset | 1.0° | **0.7°** | Measured on Hattenberger's quadrotor (Hattenberger et al. 2022) | High: same drone family, direct measurement |
| σ | Noise std of one 1 s tilt sample | 0.5° | **0.5°** (now defined per 1 s sample) | Derived from DLR fleet data (Wetz et al. 2021); cross-checked against IMU datasheets | **Low**: order-of-magnitude only |
| n_eff | Independent samples averaged | 10 | **30** (30 s hover, 1 s samples) | 30 s averaging window used by the DJI Air 3S study (2026) | Medium: the window is a design choice; independence is an assumption |
| k-error | Estimator drag coefficient error | ±10 % | **±15 %** | 14–20 % wind-tunnel vs flight gap (Hattenberger et al. 2023) | Medium–high |

Set in: `OFFSET_DEG`, `SIGMA_DEG`, `N_EFF` (Figures 1 and 2) and `K_ERR` (Figure 2).

---

## 1. Tilt offset b = 0.7°

**What it is.** A constant fake tilt: the attitude estimate reads non-zero when the drone is not tilting for wind. Causes: IMU not mounted level, accelerometer bias left after calibration, centre of mass not under the thrust centre.

**Evidence**

| Source | Drone | Offset | Notes |
|---|---|---|---|
| Hattenberger, Bronz & Condomines (2022) | ENAC custom quadrotor (same group as our airframe) | **≈ 0.7°** mean bank angle in no-wind hover | "due to the Inertial Measurement Unit alignment and calibration errors"; gives < 1 m/s wind error; they remove it by hand after a short no-wind flight |
| DJI Air 3S study (EGUsphere preprint, 2026) | DJI Air 3S, 0.724 kg | **−0.8°** roll intercept | From a linear fit of roll vs ground speed; cause not established; not corrected in their baseline |
| Wetz, Wildmann & Beyrich (2021) | DLR SWUF-3D quadrotors | Calibrated per drone (value not reported) | Pitch offset added "because of misalignment in the installation of the IMU … and slight differences in the mass distribution" |

**Cross-check from IMU datasheets.** Tilt error ≈ accelerometer bias / g (20 mg ≈ 1.15°):

| IMU | Zero-g offset (board level, before calibration) | Drift with temperature | Over a 20 °C change |
|---|---|---|---|
| TDK ICM-42688-P | ±20 mg → ±1.15° | ±0.15 mg/°C | 3 mg → 0.17° |
| TDK ICM-20602 | ±40 mg → ±2.3° | ±0.5 mg/°C | 10 mg → 0.57° |
| Bosch BMI088 | 20 mg → 1.15° (plus 0.5° package alignment error) | < 0.2 mg/K | 4 mg → 0.23° |

Flight-controller calibration removes most of the initial offset; temperature drift and mounting misalignment remain. That residual is consistent with the 0.7–0.8° seen in flight.

**Assumption.** Our 1D model applies all of b along the wind direction, which is the worst case. If the offset points in a random direction relative to the wind, the part along the wind is on average about 0.64 b.

---

## 2. Tilt noise σ = 0.5° per 1 s sample

**What it is.** The random scatter of the tilt reading about its mean in hover: attitude-estimate noise, controller corrections and small gusts. Level 1 lumps these together; Level 2 (RotorPy) will separate them.

**Evidence (weakest value in the set)**
- **Raw sensor noise is negligible.** ICM-42688-P: 0.65 mg-rms at 100 Hz bandwidth, i.e. about 0.04°. The scatter in flight comes from vibration, control and turbulence, not the chip.
- **Derived from DLR fleet data.** At 1 Hz, quadrotor wind-speed variance was 1.76 m²/s² against 1.65 m²/s² from a sonic anemometer (Wetz et al. 2021, one case). The excess, about 0.33 m/s, divided by a QAV250-class sensitivity of about 0.75–0.91 m/s per degree, gives **≈ 0.4° per 1 s sample**. We use 0.5° as a slightly conservative round value.
- **Consistent with averaging results.** Simma et al. (2020) report wind RMSE falling from 0.49–0.56 m/s (0.5 s bins) to 0.26–0.29 m/s (10 s moving average). A large random part therefore averages away.

**To improve:** log the attitude of a real hover in calm air and compute the std of 1 s means. That is a 5-minute flight.

---

## 3. n_eff = 30 (30 s hover average)

**What it is.** The number of independent tilt samples averaged into one wind estimate. Noise falls as σ/√n_eff.

**Evidence**
- **The DJI Air 3S study** uses 30 s windows. It tested 10, 30 and 60 s: errors fell with longer windows, and 30 s was kept to limit loss of time resolution.
- **Other studies average** for 10 s (Simma et al. 2020), 20 s (Neumann & Bartholmai 2015) and 10 min (Wetz et al. 2021).

**Value.** A 30 s hover with 1 s samples gives n_eff = 30.

**Assumption (optimistic).** It treats 1 s samples as independent. If tilt fluctuations stay correlated for longer than 1 s, the true n_eff is smaller (n_eff ≈ T/(2τ) for correlation time τ). Level 2 will measure τ.

---

## 4. Drag-calibration error (k-error) = ±15 %

**What it is.** The estimator's k differs from the drone's real k in flight (see the airframe notes).

**Evidence.** For the same drone, Hattenberger et al. (2023) found k/m from wind-tunnel calibration was 14–20 % higher than k/m estimated in outdoor flight (Table 3). We use ±15 % in both directions because the sign for a new drone is unknown.

---

## 5. Effect on the results

| Result | Placeholders (b = 1.0°, n_eff = 10, k ±10 %) | **Sourced values** |
|---|---|---|
| Fig. 1 bias (0.5–10 m/s) | 0.62–0.67 m/s | **0.43–0.47 m/s** |
| Fig. 1 noise std | 0.10–0.11 m/s | **0.056–0.061 m/s** |
| Fig. 1 RMSE / V at 0.5 m/s | 126 % | **88 %** |
| Fig. 1 RMSE below 10 % of wind from | 7.0 m/s | **4.5 m/s** |
| Fig. 2 k-error overtakes offset at | 4–5 m/s (k ±15 %) | **2.5–3.5 m/s** |
| Fig. 2 combined RMSE at 5 m/s | 0.13–1.63 m/s | **0.27–1.41 m/s** |
| Fig. 2 with heading flip at 5 m/s | 0.66–0.89 m/s | **0.65–0.88 m/s** |

**The conclusion is unchanged and now stronger:** the offset limits accuracy only below about 3 m/s; drag calibration (k) limits it everywhere else, and the heading flip cannot remove it.

**Benchmark.** Real systems with calibrated drag and averaging reach about 0.2–0.4 m/s RMSE:
- 0.19 m/s, Kistner et al. 2024, wind tunnel
- < 0.3 m/s, Wetz et al. 2021
- 0.26–0.29 m/s, Simma et al. 2020
- 0.39 m/s, DJI Air 3S, 2026

## 6. Open items

1. Measure σ and the correlation time τ from a real calm-air hover log (sets σ and n_eff properly).
2. Decide whether the 1D worst-case alignment of b is kept, or b is projected onto a random wind direction.
3. Check the wind-tunnel vs flight k gap on our own drone once it is chosen.

## References

- Hattenberger, G., Bronz, M., Condomines, J.-P. (2022). Estimating wind using a quadrotor. *Int. J. Micro Air Vehicles* 14. doi:10.1177/17568293211070824
- Hattenberger, G., Bronz, M., Condomines, J.-P. (2023). Evaluation of drag coefficient for a quadrotor model. *Int. J. Micro Air Vehicles* 15. doi:10.1177/17568293221148378
- Wetz, T., Wildmann, N., Beyrich, F. (2021). Distributed wind measurements with multiple quadrotor unmanned aerial vehicles in the atmospheric boundary layer. *Atmos. Meas. Tech.* 14, 3795. https://amt.copernicus.org/articles/14/3795/2021/
- Kistner, J., Neuhaus, L., Wildmann, N. (2024). High-resolution wind speed measurements with quadcopter uncrewed aerial systems. *Atmos. Meas. Tech.* 17, 4941–4955. doi:10.5194/amt-17-4941-2024
- Horizontal wind estimation from consumer-drone hover telemetry: comparing machine-learning and calibration approaches (2026). EGUsphere preprint, doi:10.5194/egusphere-2026-5393 (not yet peer reviewed)
- Simma, M., Mjøen, H., Boström, T. (2020). Measuring wind speed using the internal stabilization system of a quadrotor drone. *Drones* 4(2), 23.
- Neumann, P.P., Bartholmai, M. (2015). Real-time wind estimation on a micro unmanned aerial vehicle using its inertial measurement unit. *Sensors and Actuators A* 235, 300. doi:10.1016/j.sna.2015.09.036
- TDK InvenSense ICM-42688-P datasheet DS-000347 v1.6; ICM-20602 datasheet v1.1; Bosch BMI088 datasheet BST-BMI088-DS001.
