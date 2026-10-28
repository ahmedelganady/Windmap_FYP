# The only file that touches RotorPy: builds our drone, flies it in a given wind, returns noise-free truth (A8, A9, D12).
import numpy as np
from rotorpy.vehicles.hummingbird_params import quad_params as HUMMINGBIRD
from rotorpy.vehicles.multirotor import Multirotor
from rotorpy.controllers.quadrotor_control import SE3Control
from rotorpy.trajectories.hover_traj import HoverTraj
from rotorpy.environments import Environment

from windmap import steady
from windmap.airframes import G

# Horizontal position gains (k_p [1/s^2], k_d [1/s]) of the SE3 controller (A9)
GAINS = {
    "rotorpy": (6.5, 4.0),     # RotorPy's default: a stiff research controller
    "px4": (1.71, 1.8),        # PX4 defaults: MPC_XY_P * MPC_XY_VEL_P_ACC = 0.95 * 1.8, and MPC_XY_VEL_P_ACC
}


def hover_speed(af):
    # Rotor speed [rad/s] at which 4 rotors lift the drone's weight: 4 * k_eta * w^2 = m*g.
    return np.sqrt(af.weight / (4 * HUMMINGBIRD["k_eta"]))


def quad_params(af):
    # RotorPy parameters: the Hummingbird's inertia and motors, with our airframe's mass and drag (A8).
    if af.drag.a != 0:
        raise ValueError("Level 2 supports linear-drag airframes only (A8)")
    p = dict(HUMMINGBIRD)                                  # copy, so RotorPy's own dict is never changed
    p["mass"] = af.m
    p["k_d"] = af.drag.k / (4 * hover_speed(af))           # 4 rotors x k_d x rotor speed = k at hover
    p.update(k_z=0.0, k_h=0.0, k_flap=0.0, c_Dx=0.0, c_Dy=0.0, c_Dz=0.0)   # no other aerodynamics
    return p


class _SeriesWind:
    # Hands RotorPy our pre-computed wind: RotorPy calls update(t, position) every step and wants [wx, wy, wz].
    def __init__(self, t, wind_x):
        self.t, self.wind_x = t, wind_x

    def update(self, t, position):
        return np.array([np.interp(t, self.t, self.wind_x), 0.0, 0.0])


def simulate(af, t, wind_x, gains="rotorpy"):
    """Hover at the origin in the wind wind_x [m/s] (along x) on the time grid t [s]. Noise-free truth.

    Returns a dict of arrays, one value per time step:
    t [s], wind [m/s], x, z [m], v_x, v_z [m/s], theta = lean into the wind [rad],
    f_x = accelerometer reading along body x [m/s^2], q = attitude quaternion [x, y, z, w].
    """
    params = quad_params(af)
    kp, kd = GAINS[gains]

    # Start already balanced in the first wind value, so there is no start-up transient (D12)
    theta0 = steady.tilt_from_wind(wind_x[0], af)
    start = {"x": np.array([G * np.tan(theta0) / kp, 0.0, 0.0]),    # where a PD controller holds that lean
             "v": np.zeros(3),
             "q": np.array([0.0, np.sin(-theta0 / 2), 0.0, np.cos(-theta0 / 2)]),   # pitch back by theta0
             "w": np.zeros(3),
             "wind": np.zeros(3),
             "rotor_speeds": np.full(4, hover_speed(af))}

    controller = SE3Control(params)
    controller.kp_pos = np.array([kp, kp, 15.0])          # set AFTER creating it: SE3Control hard-codes its gains
    controller.kd_pos = np.array([kd, kd, 9.0])

    env = Environment(vehicle=Multirotor(params, initial_state=start),
                      controller=controller,
                      trajectory=HoverTraj(),
                      wind_profile=_SeriesWind(t, wind_x),
                      sim_rate=round(1 / (t[1] - t[0])))
    r = env.run(t_final=t[-1], terminate=False)           # terminate=False: keep flying after it settles

    s = r["state"]
    q = s["q"]
    b3_x = 2 * (q[:, 0] * q[:, 2] + q[:, 1] * q[:, 3])    # x and z parts of the thrust axis (body z in the world)
    b3_z = 1 - 2 * (q[:, 0]**2 + q[:, 1]**2)
    return {"t": r["time"], "wind": np.interp(r["time"], t, wind_x),   # wind acting at each logged instant (RotorPy's own log runs one step ahead)
            "x": s["x"][:, 0], "z": s["x"][:, 2], "v_x": s["v"][:, 0], "v_z": s["v"][:, 2],
            "theta": np.arctan2(-b3_x, b3_z),
            "f_x": r["imu_gt"]["accel"][:, 0],
            "q": q}