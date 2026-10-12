"""
cost_model.py - 20-Year Financial Sizing & Amortization Model for EcoGridAI

Role: Models capital expenditure (CapEx), 20-year daily amortized financial costs,
and cost-effectiveness metrics (Phi = CapEx / kW) for asset expansion options.
"""

from typing import Any, Dict

CONFIG: Dict[str, Any] = {
    # Capital cost benchmark unit rates (in INR ₹)
    "pv_capex_per_kw": 50000.0,       # ₹50,000 per kW Solar PV
    "wind_capex_per_kw": 60000.0,     # ₹60,000 per kW Wind Turbine
    "battery_capex_per_kwh": 15000.0, # ₹15,000 per kWh BESS capacity
    "grid_capex_per_kw": 5000.0,       # ₹5,000 per kW Grid Interconnect Substation upgrade
    # Amortization parameters
    "lifetime_years": 20,
    "days_per_year": 365,
    "total_amortization_days": 20 * 365,  # 7,300 days
    # Priority classification thresholds (₹ per kW served)
    "phi_recommended_threshold": 50000.0,
    "phi_alternative_threshold": 80000.0,
}


def calculate_pv_capital_cost(capacity_kw: float) -> float:
    """Calculates total capital cost for incremental Solar PV capacity in ₹."""
    return float(max(0.0, capacity_kw) * CONFIG["pv_capex_per_kw"])


def calculate_wind_capital_cost(capacity_kw: float) -> float:
    """Calculates total capital cost for incremental Wind capacity in ₹."""
    return float(max(0.0, capacity_kw) * CONFIG["wind_capex_per_kw"])


def calculate_battery_capital_cost(capacity_kwh: float) -> float:
    """Calculates total capital cost for incremental Battery Energy Storage in ₹."""
    return float(max(0.0, capacity_kwh) * CONFIG["battery_capex_per_kwh"])


def calculate_grid_capital_cost(capacity_kw: float) -> float:
    """Calculates total capital cost for Grid Interconnection capacity expansion in ₹."""
    return float(max(0.0, capacity_kw) * CONFIG["grid_capex_per_kw"])


def calculate_daily_amortized_cost(
    capital_cost: float,
    lifetime_years: int = 20,
) -> float:
    """
    Computes daily amortized cost over specified asset lifetime:
      Daily Amortized Cost = Capital Cost / (lifetime_years * 365)
    """
    total_days = max(1, lifetime_years * CONFIG["days_per_year"])
    return float(capital_cost / total_days)


def calculate_cost_effectiveness(capital_cost: float, additional_kw_served: float) -> float:
    """
    Calculates cost-effectiveness ratio Phi:
      Phi = Total Capital Cost (₹) / Additional kW Served
    """
    if additional_kw_served <= 0.0:
        return float("inf")
    return float(capital_cost / additional_kw_served)


def classify_priority(phi: float) -> str:
    """
    Classifies expansion intervention priority into:
      - 'RECOMMENDED': Phi <= 50,000 ₹/kW
      - 'ALTERNATIVE': 50,000 < Phi <= 80,000 ₹/kW
      - 'EXPENSIVE':   Phi > 80,000 ₹/kW
    """
    if phi <= CONFIG["phi_recommended_threshold"]:
        return "RECOMMENDED"
    elif phi <= CONFIG["phi_alternative_threshold"]:
        return "ALTERNATIVE"
    else:
        return "EXPENSIVE"
