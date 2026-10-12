"""
scenarios.py - Scenario Definitions for Real Microgrid Pipeline

Defines 10 operational scenarios testing microgrid resilience under load variations,
renewable generation fluctuations, component failures, and extreme stress conditions.
"""

from typing import Any, Dict, List

CONFIG: Dict[str, Any] = {
    "num_scenarios": 10,
}

SCENARIOS: List[Dict[str, Any]] = [
    {
        "name": "Normal Operation",
        "load_multiplier": 1.0,
        "solar_multiplier": 1.0,
        "wind_multiplier": 1.0,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "Peak Summer",
        "load_multiplier": 1.3,
        "solar_multiplier": 1.1,
        "wind_multiplier": 1.0,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "Battery Failure",
        "load_multiplier": 1.0,
        "solar_multiplier": 1.0,
        "wind_multiplier": 1.0,
        "grid_available": True,
        "battery_available": False,
    },
    {
        "name": "Grid Outage",
        "load_multiplier": 1.0,
        "solar_multiplier": 1.0,
        "wind_multiplier": 1.0,
        "grid_available": False,
        "battery_available": True,
    },
    {
        "name": "Low Renewable",
        "load_multiplier": 1.0,
        "solar_multiplier": 0.4,
        "wind_multiplier": 0.3,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "High Renewable Surplus",
        "load_multiplier": 1.0,
        "solar_multiplier": 1.5,
        "wind_multiplier": 1.4,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "Night Peak",
        "load_multiplier": 1.2,
        "solar_multiplier": 0.0,
        "wind_multiplier": 1.0,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "Partial Wind Failure",
        "load_multiplier": 1.0,
        "solar_multiplier": 1.0,
        "wind_multiplier": 0.2,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "Partial PV Failure",
        "load_multiplier": 1.0,
        "solar_multiplier": 0.2,
        "wind_multiplier": 1.0,
        "grid_available": True,
        "battery_available": True,
    },
    {
        "name": "Extreme Stress",
        "load_multiplier": 1.4,
        "solar_multiplier": 1.0,
        "wind_multiplier": 0.3,
        "grid_available": False,
        "battery_available": True,
    },
]


def get_scenarios() -> List[Dict[str, Any]]:
    """Returns the list of 10 scenario definitions."""
    return SCENARIOS.copy()


def apply_scenario_real_data(data: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Applies scenario multipliers to real data profiles."""
    sc_data = data.copy()
    sc_data["hourly_load"] = data["hourly_load"] * scenario["load_multiplier"]
    sc_data["hourly_pv"] = data["hourly_pv"] * scenario["solar_multiplier"]
    sc_data["hourly_wind"] = data["hourly_wind"] * scenario["wind_multiplier"]
    sc_data["grid_cap_kw"] = 1000.0 if scenario["grid_available"] else 0.0
    sc_data["battery_available"] = scenario["battery_available"]
    return sc_data


if __name__ == "__main__":
    scs = get_scenarios()
    print(f"Loaded {len(scs)} real pipeline scenarios.")
