# WindMap
Turning ordinary quadrotors into flying wind sensors - estimating wind from the flight data every drone already records, with no added hardware, and combining estimates across a drone swarm into a shared map of the wind field.

## About
Wind affects how a drone flies. It tilts into the wind and works harder to hold position. WindMap uses that effect to measure the wind, with no extra sensors, using only the data a standard quadrotor already records (IMU, GPS, motor commands). The long-term aim is for multiple drones to combine their estimates into a shared map of the wind field.

## Status
Simulation phase: testing how accurately wind can be estimated, and what limits it.

## Repository
simulations/
├── windmap/          shared code: drag models, airframes, physics, error analysis, plotting
├── tests/            tests for windmap/
├── level1_steady/    steady-hover error analysis and figures
└── level2_dynamic/   dynamic simulation (RotorPy)

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
cd simulations
pip install -e . pytest
python -m pytest
python -m level1_steady.errors_vs_wind_fig1
```

Run scripts from `simulations/`. Figures are saved to each level's `figures/` folder.

## Licence
All rights reserved. No licence is granted at this stage; contact the author for permission to use or adapt this code.