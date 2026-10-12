"""
objective_function.py - Fitness Evaluation for Real Pipeline

Role: Evaluates single scalar fitness F for fraction-based candidate vector X given explicit per-unit profile arrays
(solar_profile, wind_profile, load_profile) and availability flags (grid_available, battery_available).
Supports custom multi-objective weights (e.g., Shannon Entropy weights).
"""

from typing import Dict, Tuple
import numpy as np

from constraints import check_constraints
from dispatch_simulation_real import dispatch_simulation_real

NORM_C_CAPITAL = 80_000.0    # ₹80,000/day max capital
NORM_C_OP      = 400_000.0   # ₹400,000/day max operational
NORM_LOSS      = 5_000.0     # 5,000 kWh/day max loss
NORM_UNMET     = 10_000.0    # 10,000 kWh max unmet load
NORM_CURTAIL   = 10_000.0    # 10,000 kWh max curtailment

DEFAULT_WEIGHTS = np.array([0.20, 0.25, 0.15, 0.30, 0.10], dtype=np.float64)


def compute_fitness(
    x: np.ndarray,
    solar_profile: np.ndarray,
    wind_profile: np.ndarray,
    load_profile: np.ndarray,
    grid_available: bool = True,
    battery_available: bool = True,
    weights: np.ndarray = None,
    **kwargs
) -> float:
    """
    Evaluates scalar fitness F for candidate vector x.
    If weights is None, default heuristic weights [0.20, 0.25, 0.15, 0.30, 0.10] are used.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    weights = np.asarray(weights, dtype=np.float64)

    x_eval = np.array(x, dtype=np.float64).copy()

    if not battery_available:
        x_eval[3] = 0.0   # battery_power_kw = 0
        x_eval[4] = 0.0   # battery_capacity_kwh = 0

    dispatch_results = dispatch_simulation_real(
        planning_vector=x_eval,
        solar_profile=solar_profile,
        wind_profile=wind_profile,
        load_profile=load_profile,
        grid_available=grid_available,
        battery_available=battery_available,
    )

    totals = dispatch_results["totals"]
    c_capital = totals["c_capital"]
    c_op      = totals["c_op"]
    loss      = totals["total_loss"]
    unmet     = totals["total_unmet_load"]
    curtail   = totals.get("total_curtailment", 0.0)

    # Oversizing penalty
    total_solar_cap = (x_eval[0] * 851.5 + x_eval[1] * 1157.6) * solar_profile.sum()
    total_wind_cap  = x_eval[2] * 2097.97 * wind_profile.sum()
    total_gen_kwh   = total_solar_cap + total_wind_cap
    total_load_kwh  = load_profile.sum()
    oversize_ratio  = max(0.0, total_gen_kwh / max(total_load_kwh, 1e-3) - 1.2)
    oversize_penalty = oversize_ratio * 0.5

    norm_capital = c_capital / NORM_C_CAPITAL
    norm_op      = c_op / NORM_C_OP
    norm_loss    = loss / NORM_LOSS
    norm_unmet   = unmet / NORM_UNMET
    norm_curtail = (curtail / NORM_CURTAIL) + oversize_penalty

    if len(weights) == 5:
        w1, w2, w3, w4, w5 = weights
        fitness = (
            w1 * norm_capital  +
            w2 * norm_op       +
            w3 * norm_loss     +
            w4 * norm_unmet    +
            w5 * norm_curtail
        )
    else:
        w1, w2, w3, w4 = weights[:4]
        fitness = (
            w1 * norm_capital  +
            w2 * norm_op       +
            w3 * norm_loss     +
            w4 * norm_unmet    +
            0.10 * norm_curtail
        )

    penalty, _ = check_constraints(x_eval, dispatch_results, grid_cap_kw=x_eval[5] if grid_available else 0.0)
    fitness += penalty

    return float(fitness)


evaluate_fitness = compute_fitness


if __name__ == "__main__":
    dummy_x = np.array([0.5, 0.5, 0.8, 200.0, 1500.0, 500.0])
    dummy_s = np.array([0, 0, 0, 0, 0, 0, 0, 0.008, 0.05, 0.125, 0.418, 0.511,
                        0.516, 0.475, 0.418, 0.254, 0.05, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    dummy_w = np.array([0.815, 0.88, 0.886, 0.88, 0.881, 0.881, 0.953, 0.987,
                        0.985, 0.962, 1.0, 0.979, 0.945, 0.776, 0.673, 0.591,
                        0.487, 0.466, 0.373, 0.339, 0.339, 0.372, 0.393, 0.339], dtype=float)
    dummy_l = np.array([1454, 969, 808, 646, 646, 646, 808, 1131,
                        1293, 1615, 1938, 2197, 2423, 2746, 3069, 3230,
                        3392, 3586, 3715, 3457, 3230, 2746, 2423, 1938], dtype=float)
    f_default = compute_fitness(dummy_x, dummy_s, dummy_w, dummy_l)
    test_w = np.array([0.18, 0.32, 0.04, 0.39, 0.07])
    f_entropy = compute_fitness(dummy_x, dummy_s, dummy_w, dummy_l, weights=test_w)
    print(f"Default weights fitness: {f_default:.4f}")
    print(f"Entropy weights fitness: {f_entropy:.4f}")
