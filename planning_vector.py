"""
planning_vector.py - Fraction-Based Search Space Definition

Role: Defines search space bounds, variable names, and vector clipping routines
for 6 continuous decision variables:
  x[0] = pv_bus13_fraction    : 0.0 to 1.0
  x[1] = pv_bus30_fraction    : 0.0 to 1.0
  x[2] = wind_fraction        : 0.0 to 1.0
  x[3] = battery_power_kw     : 0.0 to 500.0 kW
  x[4] = battery_capacity_kwh : 100.0 to 5000.0 kWh
  x[5] = grid_import_limit_kw : 0.0 to 2000.0 kW
"""

from typing import Any, Dict, List
import numpy as np

PV_BUS13_KW = 851.5
PV_BUS30_KW = 1157.6
WIND_BUS6_KW = 2097.97

VAR_NAMES: List[str] = [
    "pv_bus13_frac",
    "pv_bus30_frac",
    "wind_frac",
    "battery_kw",
    "battery_kwh",
    "grid_limit_kw",
]

VAR_TYPES: List[str] = ["continuous"] * 6
INTEGER_INDICES: List[int] = []

LOWER_BOUNDS = np.array([0.0, 0.0, 0.0, 0.0, 100.0, 0.0], dtype=np.float64)
UPPER_BOUNDS = np.array([1.0, 1.0, 1.0, 500.0, 5000.0, 2000.0], dtype=np.float64)


def get_planning_bounds(battery_available: bool = True) -> Dict[str, Any]:
    lb = LOWER_BOUNDS.copy()
    ub = UPPER_BOUNDS.copy()

    if not battery_available:
        lb[3] = 0.0
        ub[3] = 0.0
        lb[4] = 0.0
        ub[4] = 0.0

    return {
        "var_names": VAR_NAMES,
        "lb": lb,
        "ub": ub,
        "types": VAR_TYPES,
        "dim": 6,
        "integer_indices": [],
    }


def clip_and_cast_vector(
    x: np.ndarray,
    battery_available: bool = True,
) -> np.ndarray:
    """Clips vector x to bounds."""
    bounds = get_planning_bounds(battery_available=battery_available)
    x_clipped = np.clip(np.array(x, dtype=np.float64), bounds["lb"], bounds["ub"])
    if not battery_available:
        x_clipped[3] = 0.0
        x_clipped[4] = 0.0
    return x_clipped


def sample_random_vector(
    rng: np.random.Generator = None,
    battery_available: bool = True,
) -> np.ndarray:
    """Generates a valid random planning vector within bounds."""
    if rng is None:
        rng = np.random.default_rng()
    bounds = get_planning_bounds(battery_available=battery_available)
    lb = bounds["lb"]
    ub = bounds["ub"]
    x = lb + rng.random(6) * (ub - lb)
    return clip_and_cast_vector(x, battery_available=battery_available)


if __name__ == "__main__":
    bounds = get_planning_bounds()
    print("--- FRACTION PLANNING VECTOR BOUNDS VERIFICATION ---")
    print(f"Lower Bounds: {bounds['lb']}")
    print(f"Upper Bounds: {bounds['ub']}")
