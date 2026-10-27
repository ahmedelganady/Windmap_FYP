#Airframe parameter sets. One entry per drone; never mix airframes.

from dataclasses import dataclass
from windmap.drag import DragModel

G = 9.81  # gravitational acceleration [m/s²] (assumption A6)


@dataclass(frozen=True)
class Airframe:
    #One drone: name, mass and drag model.

    name: str
    m: float          # mass [kg]
    drag: DragModel

    @property
    def weight(self):
        """Weight m*g [N]."""
        return self.m * G

# Comparison Airframes

# Hattenberger's drone uses the same method as ours
# Their simulated drone. Linear drag, valid up to ~8-9 m/s.
# Their simulated drone matches their measured "sphere" setup (0.902 kg, k = 0.235) within 2%.
HATTENBERGER_SIM_VAL = Airframe("Hattenberger (sim)", 0.897, DragModel(k=0.230))

# Same paper, real drone measured in a wind tunnel.
HATTENBERGER = Airframe("Hattenberger (measured)", 0.554, DragModel(k=0.153))

# Holybro QAV250 (PX4), DLR wind fleet. Kistner et al. (2024), doi:10.5194/amt-17-4941-2024
# k and a fitted by us to their curve; up to 0.43 m/s off at low wind.
QAV250 = Airframe("Holybro QAV250 (DLR)", 0.645, DragModel(k=0.117, a=0.00194))

# Crazyflie 2.0. Drag measured by Forster (2015), via RotorPy. Indoor drone.
CRAZYFLIE = Airframe("Crazyflie 2.0", 0.030, DragModel(k=0.00733))

# AscTec Hummingbird, RotorPy values. Low confidence: drag hand-tuned.
HUMMINGBIRD = Airframe("AscTec Hummingbird (RotorPy)", 0.500, DragModel(k=0.223, a=0.005))

ALL_AIRFRAMES = [HATTENBERGER_SIM_VAL, HATTENBERGER, QAV250, CRAZYFLIE, HUMMINGBIRD]




