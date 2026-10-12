"""
engine.py - Autonomous Microgrid Capacity Recommendation & Expansion Intelligence

Role: Analyzes multi-scenario deficit gaps, performs heuristic asset sizing (PV, BESS, Grid),
calculates 20-year amortized financials, prioritizes actions via cost-effectiveness index Phi,
and generates structured JSON & executive text reports.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .cost_model import (
    calculate_pv_capital_cost,
    calculate_battery_capital_cost,
    calculate_grid_capital_cost,
    calculate_daily_amortized_cost,
    calculate_cost_effectiveness,
    classify_priority,
)

CONFIG: Dict[str, Any] = {
    "pv_bus13_rating": 851.5,     # Nameplate rating at Bus 13 (kW)
    "pv_bus30_rating": 1157.6,    # Nameplate rating at Bus 30 (kW)
    "wind_bus6_rating": 2097.97,  # Nameplate rating at Bus 6 (kW)
    "grid_default_cap": 3000.0,   # Baseline substation import limit (kW)
    "bess_energy_margin": 1.20,   # 20% safety margin for battery storage sizing
    "bess_power_margin": 1.10,    # 10% safety margin for battery inverter sizing
    "grid_power_margin": 1.10,    # 10% safety margin for grid limit expansion
}


def analyze_load_gap(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes unmet energy deficit, peak gap, and critical hours for a given scenario.

    Args:
        scenario_data: Scenario dictionary containing ABC/PSO results and scenario params.

    Returns:
        Dict with unmet_kwh, peak_gap_kw, load_satisfaction, and critical hours.
    """
    # Prefer ABC metrics as primary optimizer, fall back to PSO
    opt = scenario_data.get("abc", scenario_data.get("pso", {}))
    sc_params = scenario_data.get("scenario_params", {})

    load_sat = float(opt.get("load_satisfaction", 100.0))
    unmet_kwh = float(opt.get("unmet_load_kwh", 0.0))
    curtailment_kwh = float(opt.get("curtailment_kwh", 0.0))

    # If unmet_kwh is 0 but load_satisfaction < 100, calculate from baseline total load (approx 71,068 kWh)
    if unmet_kwh <= 0.0 and load_sat < 99.9:
        total_load_approx = 71067.9 * sc_params.get("load_multiplier", 1.0)
        unmet_kwh = total_load_approx * (1.0 - load_sat / 100.0)

    # Estimate peak deficit gap in kW
    if unmet_kwh > 0.0:
        # Typical deficit hours are concentrated in 4-6 peak evening/outage hours
        outage = not sc_params.get("grid_available", True)
        effective_deficit_hours = 8.0 if outage else 4.0
        peak_gap_kw = float(min(3715.0, (unmet_kwh / effective_deficit_hours) * 1.35))
    else:
        peak_gap_kw = 0.0

    # Determine critical time period
    if not sc_params.get("grid_available", True):
        critical_hours = "All Hours (Grid Outage / Islanded Mode)"
    elif unmet_kwh > 0.0:
        critical_hours = "17:00 – 22:00 (Evening Peak & Sunset Deficit)"
    else:
        critical_hours = "None (Fully Satisfied Demand)"

    return {
        "unmet_kwh": round(unmet_kwh, 2),
        "peak_gap_kw": round(peak_gap_kw, 2),
        "load_satisfaction": round(load_sat, 2),
        "curtailment_kwh": round(curtailment_kwh, 2),
        "critical_hours": critical_hours,
    }


def recommend_pv(
    gap_kw: float,
    current_vector: List[float],
) -> List[Dict[str, Any]]:
    """
    Evaluates headroom on existing PV buses (13 & 30) and suggests capacity expansion.

    Args:
        gap_kw: Peak load deficit gap in kW.
        current_vector: Optimal planning vector [x_pv1, x_pv2, x_wind, x_grid, p_bat, e_bat].

    Returns:
        List of actionable PV recommendation dicts.
    """
    recs: List[Dict[str, Any]] = []
    if gap_kw <= 0.0:
        return recs

    x0 = current_vector[0] if len(current_vector) > 0 else 1.0
    x1 = current_vector[1] if len(current_vector) > 1 else 1.0

    headroom_13 = CONFIG["pv_bus13_rating"] * max(0.0, 1.0 - x0)
    headroom_30 = CONFIG["pv_bus30_rating"] * max(0.0, 1.0 - x1)
    total_headroom = headroom_13 + headroom_30

    if total_headroom > 10.0:
        # Step 1: Maximize existing bus dispatch fractions
        add_kw = min(gap_kw, total_headroom)
        capex = calculate_pv_capital_cost(add_kw)
        daily_amort = calculate_daily_amortized_cost(capex)
        phi = calculate_cost_effectiveness(capex, add_kw)
        priority = classify_priority(phi)

        recs.append({
            "action": "Unlock Existing PV Headroom",
            "category": "Solar PV",
            "priority": priority,
            "additional_capacity": f"{add_kw:.1f} kW",
            "additional_capacity_kw": round(add_kw, 2),
            "capital_cost": round(capex, 2),
            "daily_amortized_cost": round(daily_amort, 2),
            "cost_effectiveness_phi": round(phi, 2),
            "description": (
                f"Increase PV dispatch fraction on existing installed arrays. Unlocks up to "
                f"{headroom_13:.1f} kW at Bus 13 and {headroom_30:.1f} kW at Bus 30 without new land acquisition."
            ),
        })
        gap_kw -= add_kw

    if gap_kw > 20.0:
        # Step 2: Install supplementary PV array at optimal low-loss candidate bus (e.g., Bus 18 or Bus 25)
        add_kw = gap_kw
        capex = calculate_pv_capital_cost(add_kw)
        daily_amort = calculate_daily_amortized_cost(capex)
        phi = calculate_cost_effectiveness(capex, add_kw)
        priority = classify_priority(phi)

        recs.append({
            "action": "Install Supplementary PV Farm (Candidate Bus 18)",
            "category": "Solar PV",
            "priority": priority,
            "additional_capacity": f"{add_kw:.1f} kW",
            "additional_capacity_kw": round(add_kw, 2),
            "capital_cost": round(capex, 2),
            "daily_amortized_cost": round(daily_amort, 2),
            "cost_effectiveness_phi": round(phi, 2),
            "description": (
                f"Deploy an additional ground-mount Solar PV array at IEEE 33-Bus Node 18. "
                f"Provides daytime resilience and reduces upstream line loading."
            ),
        })

    return recs


def recommend_battery(
    scenario_data: Dict[str, Any],
    gap: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Sizes Battery Energy Storage System (BESS) capacity and inverter rating.

    Args:
        scenario_data: Scenario details and simulation outputs.
        gap: Gap analysis metrics from analyze_load_gap.

    Returns:
        List of battery expansion recommendations.
    """
    recs: List[Dict[str, Any]] = []
    unmet_kwh = gap.get("unmet_kwh", 0.0)
    peak_gap_kw = gap.get("peak_gap_kw", 0.0)
    load_sat = gap.get("load_satisfaction", 100.0)

    # Battery recommended if unmet energy exists or if grid outage satisfaction < 85%
    if unmet_kwh > 10.0 or load_sat < 85.0:
        req_kwh = unmet_kwh * CONFIG["bess_energy_margin"]
        req_kw = peak_gap_kw * CONFIG["bess_power_margin"]

        capex = calculate_battery_capital_cost(req_kwh)
        daily_amort = calculate_daily_amortized_cost(capex)
        phi = calculate_cost_effectiveness(capex, max(1.0, req_kw))
        priority = classify_priority(phi)

        recs.append({
            "action": "Deploy Modular BESS Expansion",
            "category": "Battery Storage",
            "priority": priority,
            "additional_capacity": f"{req_kwh:,.1f} kWh / {req_kw:,.1f} kW",
            "additional_capacity_kw": round(req_kw, 2),
            "additional_capacity_kwh": round(req_kwh, 2),
            "capital_cost": round(capex, 2),
            "daily_amortized_cost": round(daily_amort, 2),
            "cost_effectiveness_phi": round(phi, 2),
            "description": (
                f"Install containerized Lithium Iron Phosphate (LFP) battery storage rated at {req_kwh:,.1f} kWh "
                f"with {req_kw:,.1f} kW bidirectional inverter (incorporates 20% resilience reserve). "
                f"Eliminates critical evening and islanded mode deficits."
            ),
        })

    return recs


def recommend_grid(
    scenario_data: Dict[str, Any],
    gap: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Evaluates Grid Interconnection transformer headroom and suggests capacity upgrade.

    Args:
        scenario_data: Scenario details and simulation outputs.
        gap: Gap analysis metrics from analyze_load_gap.

    Returns:
        List of grid interconnection expansion recommendations.
    """
    recs: List[Dict[str, Any]] = []
    sc_params = scenario_data.get("scenario_params", {})
    grid_available = sc_params.get("grid_available", True)
    peak_gap_kw = gap.get("peak_gap_kw", 0.0)
    load_sat = gap.get("load_satisfaction", 100.0)

    # Grid upgrade only applies if grid is available during normal operations with shortfall
    if grid_available and (load_sat < 98.0 or peak_gap_kw > 20.0):
        req_kw = peak_gap_kw * CONFIG["grid_power_margin"]
        capex = calculate_grid_capital_cost(req_kw)
        daily_amort = calculate_daily_amortized_cost(capex)
        phi = calculate_cost_effectiveness(capex, max(1.0, req_kw))
        priority = classify_priority(phi)

        recs.append({
            "action": "Substation Interconnect Capacity Upgrade",
            "category": "Grid Interconnect",
            "priority": priority,
            "additional_capacity": f"+{req_kw:,.1f} kW Substation Limit",
            "additional_capacity_kw": round(req_kw, 2),
            "capital_cost": round(capex, 2),
            "daily_amortized_cost": round(daily_amort, 2),
            "cost_effectiveness_phi": round(phi, 2),
            "description": (
                f"Upgrade distribution substation transformer and contract demand limit at Bus 1 by {req_kw:,.1f} kW "
                f"to eliminate peak load shedding during high commercial/industrial consumption."
            ),
        })

    return recs


def generate_scenario_recommendations(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates complete gap analysis and prioritized actions for a single scenario."""
    gap = analyze_load_gap(scenario_data)
    opt = scenario_data.get("abc", scenario_data.get("pso", {}))
    vector = opt.get("vector", [1.0, 1.0, 1.0, 1.0, 100.0, 2000.0])

    actions: List[Dict[str, Any]] = []
    actions.extend(recommend_pv(gap["peak_gap_kw"], vector))
    actions.extend(recommend_battery(scenario_data, gap))
    actions.extend(recommend_grid(scenario_data, gap))

    # Priority ranking: Sort ascending by Phi (most cost-effective first)
    actions.sort(key=lambda a: a.get("cost_effectiveness_phi", float("inf")))

    return {
        "scenario_name": scenario_data.get("scenario_name", "Unknown Scenario"),
        "gap_analysis": gap,
        "recommendations": actions,
    }


def generate_full_report(
    results_dataset: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], str]:
    """
    Generates structured JSON recommendation dictionary and comprehensive ASCII executive text report.

    Args:
        results_dataset: List of 10 scenario result dictionaries.

    Returns:
        Tuple of (json_structured_dict, human_readable_report_text).
    """
    report_dict: Dict[str, Any] = {}
    total_capex_all = 0.0
    total_unmet_all = 0.0

    lines: List[str] = [
        "=" * 92,
        "          ECOGRIDAI AUTONOMOUS CAPACITY RECOMMENDATION & INVESTMENT REPORT          ",
        "                20-Year Amortized Financial Sizing & Resilience Analysis            ",
        "=" * 92,
        f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Scenarios Evaluated: {len(results_dataset)}",
        f"Benchmark Rates: Solar PV: Rs.50k/kW | Wind: Rs.60k/kW | Battery: Rs.15k/kWh | Grid: Rs.5k/kW",
        f"Amortization Horizon: 20 Years (7,300 Days)",
        "-" * 92,
        "",
    ]

    for sc in results_dataset:
        sc_name = sc.get("scenario_name", "Scenario")
        rec = generate_scenario_recommendations(sc)
        report_dict[sc_name] = rec

        gap = rec["gap_analysis"]
        acts = rec["recommendations"]

        total_unmet_all += gap["unmet_kwh"]

        lines.append(f"SCENARIO: {sc_name.upper()}")
        lines.append(f"  Load Satisfaction: {gap['load_satisfaction']:.2f}% | Unmet: {gap['unmet_kwh']:,.1f} kWh/day | Peak Gap: {gap['peak_gap_kw']:,.1f} kW")
        lines.append(f"  Critical Period:   {gap['critical_hours']}")

        if acts:
            lines.append("  Prioritized Interventions:")
            for idx, a in enumerate(acts, 1):
                total_capex_all += a["capital_cost"]
                lines.append(
                    f"    [{idx}] {a['priority']:<11} | {a['action']:<36} | Cap: {a['additional_capacity']:<16} "
                    f"| CapEx: Rs.{a['capital_cost']:>10,.0f} | 20-Yr Daily: Rs.{a['daily_amortized_cost']:>7.2f}/day"
                )
        else:
            lines.append("  Status: Optimal operation achieved. Zero asset capacity expansion required.")

        lines.append("-" * 92)

    lines.append("")
    lines.append("=" * 92)
    lines.append("                         EXECUTIVE INVESTMENT SUMMARY                               ")
    lines.append("=" * 92)
    lines.append(f"Total Cumulative Daily Energy Deficit across Suite: {total_unmet_all:,.1f} kWh/day")
    lines.append(f"Total Recommended Capital Expenditure (CapEx):     Rs.{total_capex_all:,.0f}")
    lines.append(f"Total 20-Year Amortized Daily Operating Cost:       Rs.{calculate_daily_amortized_cost(total_capex_all):,.2f} / day")
    lines.append("=" * 92)

    report_text = "\n".join(lines)
    return report_dict, report_text


def save_recommendations(
    rec_dict: Dict[str, Any],
    report_text: str,
    output_dir: Optional[Union[str, Path]] = None,
) -> Tuple[Path, Path]:
    """
    Persists recommendation outputs to recommendations.json and recommendations.txt.

    Returns:
        Tuple of (json_path, txt_path).
    """
    target_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = (target_dir / "recommendations.json").resolve()
    txt_path = (target_dir / "recommendations.txt").resolve()

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rec_dict, f, indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f" [Recommendations] JSON saved to: {json_path}")
    print(f" [Recommendations] Text report saved to: {txt_path}")

    return json_path, txt_path
