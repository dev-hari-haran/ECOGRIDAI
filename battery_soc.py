"""
battery_soc.py - Battery State of Charge Tracking (Real Pipeline)

Role: Track and enforce battery state of charge (SOC) limits across 24 hours.

Algorithm:
Initialize: SOC(0) = SOC_initial (e.g., 50% / 0.50)
For each hour t:
  - Discharge: SOC(t) = SOC(t-1) - (P_discharge * dt / Cb) / eta_discharge
  - Charge: SOC(t) = SOC(t-1) + (P_charge * dt / Cb) * eta_charge
  - Enforce bounds: SOC_min <= SOC(t) <= SOC_max
"""

from typing import Any, Dict, Tuple
import numpy as np


class BatteryTracker:
    def __init__(
        self,
        capacity_kwh: float,
        power_rating_kw: float,
        soc_initial: float = 0.50,
        soc_min: float = 0.20,
        soc_max: float = 0.95,
        eta_charge: float = 0.95,
        eta_discharge: float = 0.95,
        dt: float = 1.0,
    ):
        self.capacity_kwh = max(capacity_kwh, 1e-3)
        self.power_rating_kw = power_rating_kw
        self.soc_initial = soc_initial
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.eta_charge = eta_charge
        self.eta_discharge = eta_discharge
        self.dt = dt

        self.current_soc = soc_initial
        self.soc_history = [soc_initial]
        self.violation_count = 0
        self.curtailment_events = 0

    def step(self, p_charge: float = 0.0, p_discharge: float = 0.0) -> Tuple[float, float, float]:
        """Simulate battery operation for 1 hour."""
        available_energy_kwh = max(0.0, (self.current_soc - self.soc_min) * self.capacity_kwh)
        max_discharge_kw = min(self.power_rating_kw, (available_energy_kwh * self.eta_discharge) / self.dt)
        actual_discharge = min(p_discharge, max_discharge_kw)

        if p_discharge > max_discharge_kw + 1e-5:
            self.violation_count += 1

        remaining_capacity_kwh = max(0.0, (self.soc_max - self.current_soc) * self.capacity_kwh)
        max_charge_kw = min(self.power_rating_kw, (remaining_capacity_kwh / self.eta_charge) / self.dt)
        actual_charge = min(p_charge, max_charge_kw)

        if p_charge > max_charge_kw + 1e-5:
            self.curtailment_events += 1

        delta_soc_charge = (actual_charge * self.dt / self.capacity_kwh) * self.eta_charge
        delta_soc_discharge = (actual_discharge * self.dt / self.capacity_kwh) / self.eta_discharge

        new_soc = self.current_soc + delta_soc_charge - delta_soc_discharge
        new_soc = float(np.clip(new_soc, self.soc_min, self.soc_max))

        self.current_soc = new_soc
        self.soc_history.append(new_soc)

        return actual_charge, actual_discharge, new_soc

    def get_soc_history(self) -> np.ndarray:
        return np.array(self.soc_history[1:], dtype=np.float64)


def simulate_battery_soc(
    p_charge_arr: np.ndarray,
    p_discharge_arr: np.ndarray,
    capacity_kwh: float,
    power_rating_kw: float,
    soc_initial: float = 0.50,
    soc_min: float = 0.20,
    soc_max: float = 0.95,
) -> Dict[str, Any]:
    """Simulates battery SOC across 24 hours."""
    tracker = BatteryTracker(
        capacity_kwh=capacity_kwh,
        power_rating_kw=power_rating_kw,
        soc_initial=soc_initial,
        soc_min=soc_min,
        soc_max=soc_max,
    )

    actual_charge = []
    actual_discharge = []
    soc_list = []

    for t in range(len(p_charge_arr)):
        chg, dis, soc = tracker.step(p_charge_arr[t], p_discharge_arr[t])
        actual_charge.append(chg)
        actual_discharge.append(dis)
        soc_list.append(soc)

    return {
        "soc_array": np.array(soc_list),
        "actual_charge": np.array(actual_charge),
        "actual_discharge": np.array(actual_discharge),
        "violation_count": tracker.violation_count,
        "curtailment_events": tracker.curtailment_events,
    }


if __name__ == "__main__":
    chg_dummy = np.full(24, 10.0)
    dis_dummy = np.full(24, 5.0)
    res = simulate_battery_soc(chg_dummy, dis_dummy, capacity_kwh=100.0, power_rating_kw=50.0)
    print("--- BATTERY SOC MODULE VERIFICATION ---")
    print(f"24h SOC Range: {np.min(res['soc_array'])*100:.1f}% to {np.max(res['soc_array'])*100:.1f}%")
