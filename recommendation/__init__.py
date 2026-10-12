"""
recommendation package - Autonomous Capacity Sizing & Financial Recommendation Engine
"""

from .cost_model import (
    calculate_pv_capital_cost,
    calculate_wind_capital_cost,
    calculate_battery_capital_cost,
    calculate_grid_capital_cost,
    calculate_daily_amortized_cost,
    calculate_cost_effectiveness,
    classify_priority,
)
from .engine import (
    analyze_load_gap,
    recommend_pv,
    recommend_battery,
    recommend_grid,
    generate_scenario_recommendations,
    generate_full_report,
    save_recommendations,
)

__all__ = [
    "calculate_pv_capital_cost",
    "calculate_wind_capital_cost",
    "calculate_battery_capital_cost",
    "calculate_grid_capital_cost",
    "calculate_daily_amortized_cost",
    "calculate_cost_effectiveness",
    "classify_priority",
    "analyze_load_gap",
    "recommend_pv",
    "recommend_battery",
    "recommend_grid",
    "generate_scenario_recommendations",
    "generate_full_report",
    "save_recommendations",
]
