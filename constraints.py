"""
constraints.py - Constraint Checker for Microgrid Optimization (Real Pipeline)

Role: Validate candidate solutions and hourly dispatch logs against technical constraints.

Constraint Checks:
1. Energy balance check
2. Battery power limit check
3. SOC bounds check
4. Generation ramp limits
5. Grid import capacity limit
6. Unmet load penalty (max ₹50/kWh)
"""

from typing import Dict, Tuple
import numpy as np


def check_constraints(
    planning_vector: np.ndarray,
    dispatch_results: dict,
    grid_cap_kw: float = 10000.0,
    max_ramp_kw: float = 3000.0,
    eps: float = 1e-3,
) -> Tuple[float, Dict[str, float]]:
    """Evaluates constraint violations and returns (total_penalty, penalty_breakdown)."""
    Ps, Pw, Pb, Ns, Nw, Cb = planning_vector
    hourly = dispatch_results["hourly"]

    solar_used = hourly["solar_used"]
    wind_used = hourly["wind_used"]
    bat_dis = hourly["bat_dis"]
    bat_chg = hourly["bat_chg"]
    grid_import = hourly["grid_import"]
    unmet_load = hourly["unmet_load"]
    load = hourly["load"]
    soc = hourly["soc"]

    penalty_weights = {
        "energy_balance": 100.0,
        "power_limits": 50.0,
        "soc_bounds": 200.0,
        "ramp_limits": 20.0,
        "grid_cap": 80.0,
        "unmet_load": 50.0,  # max ₹50/kWh unmet load penalty
    }

    penalties = {
        "energy_balance": 0.0,
        "power_limits": 0.0,
        "soc_bounds": 0.0,
        "ramp_limits": 0.0,
        "grid_cap": 0.0,
        "unmet_load": 0.0,
    }

    # 1. Energy balance check per hour
    generation_sum = solar_used + wind_used + bat_dis + grid_import
    mismatch = np.abs(generation_sum - (load - unmet_load))
    balance_violations = np.maximum(0.0, mismatch - eps)
    penalties["energy_balance"] = penalty_weights["energy_balance"] * float(np.sum(balance_violations))

    # 2. Power limit checks
    chg_overflow = np.maximum(0.0, bat_chg - Pb)
    dis_overflow = np.maximum(0.0, bat_dis - Pb)
    penalties["power_limits"] = penalty_weights["power_limits"] * float(np.sum(chg_overflow + dis_overflow))

    # 3. SOC bound checks
    soc_underflow = np.maximum(0.0, 0.20 - soc)
    soc_overflow = np.maximum(0.0, soc - 0.95)
    penalties["soc_bounds"] = penalty_weights["soc_bounds"] * float(np.sum(soc_underflow + soc_overflow))

    # 4. Ramp limits check
    total_gen = solar_used + wind_used
    gen_ramp = np.abs(np.diff(total_gen))
    ramp_violations = np.maximum(0.0, gen_ramp - max_ramp_kw)
    penalties["ramp_limits"] = penalty_weights["ramp_limits"] * float(np.sum(ramp_violations))

    # 5. Grid import cap check
    grid_overflow = np.maximum(0.0, grid_import - grid_cap_kw)
    penalties["grid_cap"] = penalty_weights["grid_cap"] * float(np.sum(grid_overflow))

    # 6. Unmet load penalty
    penalties["unmet_load"] = penalty_weights["unmet_load"] * float(np.sum(unmet_load))

    total_penalty = float(sum(penalties.values()))
    return total_penalty, penalties


if __name__ == "__main__":
    dummy_vector = np.array([100.0, 80.0, 50.0, 2.0, 2.0, 200.0])
    dummy_results = {
        "hourly": {
            "solar_used": np.zeros(24),
            "wind_used": np.zeros(24),
            "bat_dis": np.zeros(24),
            "bat_chg": np.zeros(24),
            "grid_import": np.zeros(24),
            "unmet_load": np.zeros(24),
            "load": np.full(24, 100.0),
            "soc": np.full(24, 0.50),
        }
    }
    pen, breakd = check_constraints(dummy_vector, dummy_results)
    print("--- CONSTRAINTS MODULE VERIFICATION ---")
    print(f"Dummy Penalty Score: {pen:.2f}")
