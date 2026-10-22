"""
dispatch_simulation_real.py - Real 24-Hour Energy Dispatch & Bus Loss Engine

Role: Simulates 24-hour priority dispatch using fraction-based decision variables (x[0..5])
and normalized per-unit profiles for solar and wind.
"""

from typing import Any, Dict, Tuple
import numpy as np

from battery_soc import BatteryTracker
from bus_network import get_loss_factor

CONFIG: Dict[str, Any] = {
    "c_om_solar": 1.2525,
    "c_om_wind": 2.0875,
    "c_om_bat": 0.835,
    "c_grid_import": 12.525,
    "bus_pv_1": 13,
    "bus_pv_2": 30,
    "bus_wind": 6,
    "pv_bus13_kw": 851.5,
    "pv_bus30_kw": 1157.6,
    "wind_bus6_kw": 2097.97,
    "grid_cap_kw": 2000.0,
}


def dispatch_simulation_real(
    planning_vector: np.ndarray,
    solar_profile: np.ndarray,
    wind_profile: np.ndarray,
    load_profile: np.ndarray,
    grid_available: bool = True,
    battery_available: bool = True,
    grid_cap_kw: float = None,
) -> Dict[str, Any]:
    """
    Executes 24-hour hourly dispatch simulation using fraction-based planning vector x.
      x[0]: pv_bus13_fraction (0-1)
      x[1]: pv_bus30_fraction (0-1)
      x[2]: wind_fraction (0-1)
      x[3]: battery_power_kw
      x[4]: battery_capacity_kwh
      x[5]: grid_import_limit_kw
    """
    if grid_cap_kw is None:
        grid_cap_kw = float(CONFIG.get("grid_cap_kw", 2000.0))

    x = planning_vector
    pv13_capacity = x[0] * CONFIG["pv_bus13_kw"]
    pv30_capacity = x[1] * CONFIG["pv_bus30_kw"]
    wind_capacity = x[2] * CONFIG["wind_bus6_kw"]

    battery_power = x[3] if battery_available else 0.0
    battery_cap = x[4] if battery_available else 0.0

    grid_limit = min(x[5], grid_cap_kw) if grid_available else 0.0

    battery = BatteryTracker(capacity_kwh=battery_cap, power_rating_kw=battery_power)

    # Bus Loss Factors
    lf_bus13 = get_loss_factor(CONFIG["bus_pv_1"])  # PV 1 (Bus 13)
    lf_bus30 = get_loss_factor(CONFIG["bus_pv_2"])  # PV 2 (Bus 30)
    lf_bus6 = get_loss_factor(CONFIG["bus_wind"])    # Wind (Bus 6)

    p_solar_avail_arr = np.zeros(24, dtype=np.float64)
    p_wind_avail_arr = np.zeros(24, dtype=np.float64)
    p_solar_used_arr = np.zeros(24, dtype=np.float64)
    p_wind_used_arr = np.zeros(24, dtype=np.float64)
    p_bat_dis_arr = np.zeros(24, dtype=np.float64)
    p_bat_chg_arr = np.zeros(24, dtype=np.float64)
    p_grid_import_arr = np.zeros(24, dtype=np.float64)
    curtailment_arr = np.zeros(24, dtype=np.float64)
    unmet_load_arr = np.zeros(24, dtype=np.float64)

    gen_bus13 = np.zeros(24, dtype=np.float64)
    gen_bus30 = np.zeros(24, dtype=np.float64)
    gen_bus6 = np.zeros(24, dtype=np.float64)

    loss_bus13 = np.zeros(24, dtype=np.float64)
    loss_bus30 = np.zeros(24, dtype=np.float64)
    loss_bus6 = np.zeros(24, dtype=np.float64)

    for t in range(24):
        p_load = float(load_profile[t])
        s_pu = float(solar_profile[t])
        w_pu = float(wind_profile[t])

        g13_avail = pv13_capacity * s_pu
        g30_avail = pv30_capacity * s_pu
        g6_avail = wind_capacity * w_pu

        ps_avail = g13_avail + g30_avail
        pw_avail = g6_avail

        p_solar_avail_arr[t] = ps_avail
        p_wind_avail_arr[t] = pw_avail

        # 1. Solar first
        ps_used = min(p_load, ps_avail)
        rem_load = p_load - ps_used
        excess_solar = ps_avail - ps_used

        # 2. Wind second
        pw_used = min(rem_load, pw_avail)
        rem_load -= pw_used
        excess_wind = pw_avail - pw_used

        excess_renewable = excess_solar + excess_wind

        # 3. Battery operation
        p_chg_req = 0.0
        p_dis_req = 0.0

        if rem_load > 0:
            p_dis_req = rem_load
        elif excess_renewable > 0:
            p_chg_req = excess_renewable

        if battery_available and battery_cap > 0 and battery_power > 0:
            actual_chg, actual_dis, _ = battery.step(p_charge=p_chg_req, p_discharge=p_dis_req)
        else:
            actual_chg, actual_dis = 0.0, 0.0
            if battery_available:
                battery.step(p_charge=0.0, p_discharge=0.0)

        p_bat_chg_arr[t] = actual_chg
        p_bat_dis_arr[t] = actual_dis

        if rem_load > 0:
            rem_load -= actual_dis
            if grid_available:
                p_grid_import = min(rem_load, grid_limit)
            else:
                p_grid_import = 0.0
            p_grid_import_arr[t] = p_grid_import
            unmet_load = max(0.0, rem_load - p_grid_import)
            unmet_load_arr[t] = unmet_load
        else:
            curtailment = max(0.0, excess_renewable - actual_chg)
            curtailment_arr[t] = curtailment

        p_solar_used_arr[t] = ps_used
        p_wind_used_arr[t] = pw_used

        # Calculate per-bus generation and transmission losses
        g13 = ps_used * (pv13_capacity / max(pv13_capacity + pv30_capacity, 1e-3)) if (pv13_capacity + pv30_capacity) > 0 else 0.0
        g30 = ps_used * (pv30_capacity / max(pv13_capacity + pv30_capacity, 1e-3)) if (pv13_capacity + pv30_capacity) > 0 else 0.0
        g6 = pw_used

        gen_bus13[t] = g13
        gen_bus30[t] = g30
        gen_bus6[t] = g6

        loss_bus13[t] = g13 * (lf_bus13 - 1.0)
        loss_bus30[t] = g30 * (lf_bus30 - 1.0)
        loss_bus6[t] = g6 * (lf_bus6 - 1.0)
    soc_history = battery.get_soc_history() if battery_available else np.full(24, 0.50)
    if len(soc_history) != 24:
        soc_history = np.full(24, 0.50)

    total_solar_gen = float(np.sum(p_solar_avail_arr))
    total_wind_gen = float(np.sum(p_wind_avail_arr))
    total_ren_gen = total_solar_gen + total_wind_gen

    total_solar_used = float(np.sum(p_solar_used_arr))
    total_wind_used = float(np.sum(p_wind_used_arr))
    total_ren_used = total_solar_used + total_wind_used + float(np.sum(p_bat_chg_arr))
    total_curtailment = float(np.sum(curtailment_arr))
    total_unmet_load = float(np.sum(unmet_load_arr))
    total_grid_import = float(np.sum(p_grid_import_arr))

    total_bat_dis = float(np.sum(p_bat_dis_arr))
    total_bat_chg = float(np.sum(p_bat_chg_arr))
    battery_loss = max(0.0, total_bat_chg - total_bat_dis)

    bus_trans_loss = float(np.sum(loss_bus13) + np.sum(loss_bus30) + np.sum(loss_bus6))
    total_loss = battery_loss + 0.02 * (total_ren_used + total_grid_import) + bus_trans_loss

    # Capital cost (daily amortized cost of installed assets):
    c_pv_per_kw       = 15.0    # ₹15/kW/day
    c_wind_per_kw     = 12.0    # ₹12/kW/day
    c_battery_kw      = 8.0     # ₹8/kW/day (power rating)
    c_battery_kwh     = 2.0     # ₹2/kWh/day (energy capacity)
    c_grid_connection = 1.0     # ₹1/kW/day (grid connection limit)

    c_capital = (
        pv13_capacity   * c_pv_per_kw   +
        pv30_capacity   * c_pv_per_kw   +
        wind_capacity   * c_wind_per_kw  +
        battery_power   * c_battery_kw   +
        battery_cap     * c_battery_kwh  +
        grid_limit      * c_grid_connection
    )

    c_op = (
        total_solar_used * CONFIG["c_om_solar"] +
        total_wind_used * CONFIG["c_om_wind"] +
        (total_bat_dis + total_bat_chg) * CONFIG["c_om_bat"] +
        total_grid_import * CONFIG["c_grid_import"]
    )

    utilization_pct = (total_ren_used / max(total_ren_gen, 1e-3)) * 100.0 if total_ren_gen > 0 else 0.0

    return {
        "planning_vector": planning_vector,
        "hourly": {
            "solar_avail": p_solar_avail_arr,
            "wind_avail": p_wind_avail_arr,
            "solar_used": p_solar_used_arr,
            "wind_used": p_wind_used_arr,
            "bat_dis": p_bat_dis_arr,
            "bat_chg": p_bat_chg_arr,
            "grid_import": p_grid_import_arr,
            "curtailment": curtailment_arr,
            "unmet_load": unmet_load_arr,
            "load": load_profile,
            "soc": soc_history,
            "gen_bus13": gen_bus13,
            "gen_bus30": gen_bus30,
            "gen_bus6": gen_bus6,
            "loss_bus13": loss_bus13,
            "loss_bus30": loss_bus30,
            "loss_bus6": loss_bus6,
        },
        "totals": {
            "c_capital": c_capital,
            "c_op": c_op,
            "total_cost": c_capital + c_op,
            "total_loss": total_loss,
            "bus_trans_loss": bus_trans_loss,
            "total_ren_gen": total_ren_gen,
            "total_ren_used": total_ren_used,
            "total_curtailment": total_curtailment,
            "total_unmet_load": total_unmet_load,
            "total_grid_import": total_grid_import,
            "utilization_pct": utilization_pct,
            "battery_violations": battery.violation_count if battery_available else 0,
            "total_generation": total_ren_gen,
        },
        "total_loss_kWh": total_loss,
        "bus_losses": {
            "Bus_13_PV1_kWh": float(np.sum(loss_bus13)),
            "Bus_30_PV2_kWh": float(np.sum(loss_bus30)),
            "Bus_6_Wind_kWh": float(np.sum(loss_bus6)),
        },
    }
