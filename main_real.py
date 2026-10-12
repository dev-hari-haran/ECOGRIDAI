"""
main_real.py - Entry Point for Real Microgrid Data Pipeline (33-Bus System)

Orchestrates full 10-scenario resilience benchmark using real CSV grid dataset
and 33-bus transmission loss model. Passes explicit scenario-scaled profiles into run_abc and run_pso.

Features 4-Phase Shannon Entropy Weight Integration:
  Phase 1: Baseline run with default/equal weights -> saves results_real.json
  Phase 2: Derive Shannon Entropy weights for ABC and PSO independently
  Phase 3: Re-run optimization with derived entropy weights -> saves results_real_entropy.json
  Phase 4: Side-by-side comparison showing which algorithm benefits more from entropy weighting
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

from abc_optimization import run_abc
from dispatch_simulation_real import dispatch_simulation_real
from entropy_weights import compute_abc_pso_weights
from planning_vector import VAR_NAMES, get_planning_bounds
from plot_results_real import plot_results_real
from pso_optimization import run_pso
from real_data_loader import load_real_data
from scenarios import get_scenarios

import bus_network
from data_input.input_form import load_custom_config

DATA1_FILE: str = "Data1.csv"
DATA2_FILE: str = "Data2.csv"

# Global configuration toggle: Set to True to engage custom configuration from custom_config.json
USE_CUSTOM_INPUT: bool = False

# Ensure UTF-8 output encoding for Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner():
    print("=" * 95)
    print("      REAL MICROGRID DATA OPTIMIZATION & 33-BUS TRANSMISSION ENGINE         ")
    print("      10-Scenario Resilience Suite with Shannon Entropy Weight Integration   ")
    print("=" * 95)


def compute_convergence_speed(history: np.ndarray, threshold_pct: float = 0.95) -> int:
    """Calculates iterations required to reach threshold_pct of final fitness improvement."""
    if len(history) == 0:
        return 0
    f_init = history[0]
    f_final = history[-1]
    if abs(f_init - f_final) < 1e-6:
        return 1
    target = f_init - threshold_pct * (f_init - f_final)
    for idx, val in enumerate(history):
        if val <= target:
            return idx + 1
    return len(history)


def print_scenario_table(scenario_name: str, abc_res: Dict[str, Any], pso_res: Dict[str, Any]):
    print("\n" + "=" * 85)
    print(f" REAL PIPELINE SCENARIO BENCHMARK RESULTS: {scenario_name.upper()}")
    print("=" * 85)
    print(f"{'Metric / Variable':<38} | {'ABC Optimization':<20} | {'PSO Optimization':<20}")
    print("-" * 85)

    for i, var_name in enumerate(VAR_NAMES):
        print(f"Optimal {var_name:<30} | {abc_res['vector'][i]:<20.2f} | {pso_res['vector'][i]:<20.2f}")

    print("-" * 85)
    print(f"{'Best Fitness Score (F)':<38} | {abc_res['fitness']:<20.4f} | {pso_res['fitness']:<20.4f}")
    print(f"{'Capital Cost (₹/day)':<38} | ₹{abc_res['capital_cost']:<19.2f} | ₹{pso_res['capital_cost']:<19.2f}")
    print(f"{'Operational Cost (₹/day)':<38} | ₹{abc_res['operational_cost']:<19.2f} | ₹{pso_res['operational_cost']:<19.2f}")
    print(f"{'Total Daily Cost (₹/day)':<38} | ₹{abc_res['total_cost']:<19.2f} | ₹{pso_res['total_cost']:<19.2f}")
    print(f"{'Total System Loss (kWh)':<38} | {abc_res['energy_loss_kwh']:<20.2f} | {pso_res['energy_loss_kwh']:<20.2f}")
    print(f"{'33-Bus Cable Transmission Loss (kWh)':<38} | {abc_res['bus_trans_loss']:<20.2f} | {pso_res['bus_trans_loss']:<20.2f}")
    print(f"{'Unmet Load (kWh)':<38} | {abc_res['unmet_load_kwh']:<20.2f} | {pso_res['unmet_load_kwh']:<20.2f}")
    print(f"{'Curtailment (kWh)':<38} | {abc_res['curtailment_kwh']:<20.2f} | {pso_res['curtailment_kwh']:<20.2f}")
    print(f"{'Renewable Utilization (%)':<38} | {abc_res['renewable_utilization']:<19.2f}% | {pso_res['renewable_utilization']:<19.2f}%")
    print(f"{'Load Satisfaction (%)':<38} | {abc_res['load_satisfaction']:<19.2f}% | {pso_res['load_satisfaction']:<19.2f}%")
    print(f"{'Convergence Speed (Iter to 95%)':<38} | {abc_res['convergence_iterations']:<20d} | {pso_res['convergence_iterations']:<20d}")
    print(f"{'Execution Time (seconds)':<38} | {abc_res['computational_time']:<20.3f} | {pso_res['computational_time']:<20.3f}")
    print("=" * 85 + "\n")


def run_pipeline(
    weights_abc: np.ndarray = None,
    weights_pso: np.ndarray = None,
    save_json_path: Path = None,
    generate_plots: bool = False,
    phase_title: str = "Baseline",
    verbose_scenarios: bool = True,
) -> List[Dict[str, Any]]:
    """Runs all 10 scenarios with specified ABC and PSO weights."""
    print(f"\n{'='*35} {phase_title.upper()} {'='*35}")
    data = load_real_data(DATA1_FILE, DATA2_FILE)
    if USE_CUSTOM_INPUT:
        custom_cfg = load_custom_config()
        if custom_cfg:
            print(" [Main Real] Engaging CUSTOM INPUT configuration from custom_config.json")
            base_load = np.array(custom_cfg["load_profile"]["hourly_load_kw"], dtype=np.float64)
            bus_network.CONFIG["pv_buses"] = custom_cfg["system_capacities"]["pv_buses"]
            bus_network.CONFIG["wind_buses"] = custom_cfg["system_capacities"]["wind_buses"]
            data["total_pv_capacity"] = custom_cfg["system_capacities"]["total_pv_kw"]
            data["total_wind_capacity"] = custom_cfg["system_capacities"]["total_wind_kw"]
            data["pv_buses"] = custom_cfg["system_capacities"]["pv_buses"]
            data["wind_buses"] = custom_cfg["system_capacities"]["wind_buses"]
            data["peak_load"] = custom_cfg["load_profile"]["peak_load_kw"]
            print(f" [Main Real] Custom PV: {data['total_pv_capacity']:.1f} kW, Wind: {data['total_wind_capacity']:.1f} kW, Peak Load: {data['peak_load']:.1f} kW")
        else:
            print(" [Main Real] Warning: USE_CUSTOM_INPUT is True but custom_config.json is missing or invalid. Falling back to default.")
            base_load = data["hourly_load"]
    else:
        base_load = data["hourly_load"]

    base_solar = data["hourly_pv_pu"]
    base_wind = data["hourly_wind_pu"]

    scenarios = get_scenarios()
    all_scenario_results: List[Dict[str, Any]] = []

    output_dir = Path(__file__).parent / "Plot_real"
    output_dir.mkdir(parents=True, exist_ok=True)

    for sc_idx, scenario in enumerate(scenarios, 1):
        sc_name = scenario["name"]
        if verbose_scenarios:
            print(f"[{phase_title} {sc_idx}/{len(scenarios)}] Processing '{sc_name}'...")

        solar_scaled = base_solar * scenario["solar_multiplier"]
        wind_scaled = base_wind * scenario["wind_multiplier"]
        load_scaled = base_load * scenario["load_multiplier"]

        bounds = get_planning_bounds(
            battery_available=scenario["battery_available"],
        )

        # Run ABC Optimization
        t0 = time.time()
        abc_vec, abc_fit, abc_hist = run_abc(
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=scenario["grid_available"],
            battery_available=scenario["battery_available"],
            bounds=bounds,
            weights=weights_abc,
            colony_size=30,
            max_iter=100,
            seed=42,
        )
        abc_time = time.time() - t0

        if not scenario["battery_available"]:
            abc_vec[3] = 0.0
            abc_vec[4] = 0.0

        abc_dispatch = dispatch_simulation_real(
            abc_vec,
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=scenario["grid_available"],
            battery_available=scenario["battery_available"],
        )

        # Run PSO Optimization
        t0 = time.time()
        pso_vec, pso_fit, pso_hist = run_pso(
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=scenario["grid_available"],
            battery_available=scenario["battery_available"],
            bounds=bounds,
            weights=weights_pso,
            n_particles=30,
            max_iter=100,
            seed=43,
        )
        pso_time = time.time() - t0

        if not scenario["battery_available"]:
            pso_vec[3] = 0.0
            pso_vec[4] = 0.0

        pso_dispatch = dispatch_simulation_real(
            pso_vec,
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=scenario["grid_available"],
            battery_available=scenario["battery_available"],
        )

        # Extract Metrics
        total_load = float(np.sum(load_scaled))
        abc_tot = abc_dispatch["totals"]
        pso_tot = pso_dispatch["totals"]

        abc_unmet = float(abc_tot["total_unmet_load"])
        pso_unmet = float(pso_tot["total_unmet_load"])

        abc_sat = float(np.clip(((total_load - abc_unmet) / max(total_load, 1e-3)) * 100.0, 0.0, 100.0))
        pso_sat = float(np.clip(((total_load - pso_unmet) / max(total_load, 1e-3)) * 100.0, 0.0, 100.0))

        abc_conv = compute_convergence_speed(abc_hist)
        pso_conv = compute_convergence_speed(pso_hist)

        abc_metrics = {
            "vector": abc_vec.tolist(),
            "fitness": float(abc_fit),
            "capital_cost": float(abc_tot["c_capital"]),
            "c_capital": float(abc_tot["c_capital"]),
            "operational_cost": float(abc_tot["c_op"]),
            "c_op": float(abc_tot["c_op"]),
            "total_cost": float(abc_tot["total_cost"]),
            "energy_loss_kwh": float(abc_tot["total_loss"]),
            "energy_loss": float(abc_tot["total_loss"]),
            "bus_trans_loss": float(abc_tot["bus_trans_loss"]),
            "unmet_load_kwh": abc_unmet,
            "curtailment_kwh": float(abc_tot.get("total_curtailment", 0.0)),
            "renewable_utilization": float(abc_tot["utilization_pct"]),
            "load_satisfaction": abc_sat,
            "convergence_iterations": abc_conv,
            "computational_time": float(abc_time),
        }

        pso_metrics = {
            "vector": pso_vec.tolist(),
            "fitness": float(pso_fit),
            "capital_cost": float(pso_tot["c_capital"]),
            "c_capital": float(pso_tot["c_capital"]),
            "operational_cost": float(pso_tot["c_op"]),
            "c_op": float(pso_tot["c_op"]),
            "total_cost": float(pso_tot["total_cost"]),
            "energy_loss_kwh": float(pso_tot["total_loss"]),
            "energy_loss": float(pso_tot["total_loss"]),
            "bus_trans_loss": float(pso_tot["bus_trans_loss"]),
            "unmet_load_kwh": pso_unmet,
            "curtailment_kwh": float(pso_tot.get("total_curtailment", 0.0)),
            "renewable_utilization": float(pso_tot["utilization_pct"]),
            "load_satisfaction": pso_sat,
            "convergence_iterations": pso_conv,
            "computational_time": float(pso_time),
        }

        scenario_res = {
            "scenario_name": sc_name,
            "scenario_params": scenario,
            "abc": abc_metrics,
            "pso": pso_metrics,
        }
        all_scenario_results.append(scenario_res)

        if verbose_scenarios and sc_idx <= 2:
            print_scenario_table(sc_name, abc_metrics, pso_metrics)

        if generate_plots and sc_idx == 1:
            dummy_sc_data = {
                "hourly_load": load_scaled,
                "hourly_pv": solar_scaled,
                "hourly_wind": wind_scaled,
            }
            plot_results_real(
                abc_history=abc_hist,
                pso_history=pso_hist,
                abc_vector=abc_vec,
                pso_vector=pso_vec,
                abc_dispatch=abc_dispatch,
                pso_dispatch=pso_dispatch,
                real_data=dummy_sc_data,
                output_dir=str(output_dir),
                save_prefix="plot_real_",
            )

    if save_json_path:
        with open(save_json_path, "w", encoding="utf-8") as f:
            json.dump(all_scenario_results, f, indent=2)
        print(f"[{phase_title}] Exported dataset to '{save_json_path}'.")

    return all_scenario_results


def print_comparison_analysis(phase1_results: List[Dict[str, Any]], phase3_results: List[Dict[str, Any]]):
    """Prints comprehensive side-by-side comparison and algorithm benefit analysis."""
    print("\n" + "=" * 105)
    print("                     PHASE 4: EQUAL WEIGHTS vs SHANNON ENTROPY WEIGHTS COMPARISON                  ")
    print("=" * 105)
    print(f"{'Scenario Name':<24} | {'ABC Cost Equal':<14} | {'ABC Cost Ent':<14} | {'PSO Cost Equal':<14} | {'PSO Cost Ent':<14} | {'Winner':<8}")
    print("-" * 105)

    abc_eq_costs, abc_ent_costs = [], []
    pso_eq_costs, pso_ent_costs = [], []
    abc_eq_unmet, abc_ent_unmet = [], []
    pso_eq_unmet, pso_ent_unmet = [], []
    abc_eq_conv, abc_ent_conv = [], []
    pso_eq_conv, pso_ent_conv = [], []

    for r1, r3 in zip(phase1_results, phase3_results):
        sc = r1["scenario_name"]
        a_c1 = r1["abc"]["total_cost"]
        a_c3 = r3["abc"]["total_cost"]
        p_c1 = r1["pso"]["total_cost"]
        p_c3 = r3["pso"]["total_cost"]

        winner = "ABC" if a_c3 <= p_c3 else "PSO"
        print(f"{sc:<24} | ₹{a_c1:<13.1f} | ₹{a_c3:<13.1f} | ₹{p_c1:<13.1f} | ₹{p_c3:<13.1f} | {winner:<8}")

        abc_eq_costs.append(a_c1)
        abc_ent_costs.append(a_c3)
        pso_eq_costs.append(p_c1)
        pso_ent_costs.append(p_c3)

        abc_eq_unmet.append(r1["abc"]["unmet_load_kwh"])
        abc_ent_unmet.append(r3["abc"]["unmet_load_kwh"])
        pso_eq_unmet.append(r1["pso"]["unmet_load_kwh"])
        pso_ent_unmet.append(r3["pso"]["unmet_load_kwh"])

        abc_eq_conv.append(r1["abc"]["convergence_iterations"])
        abc_ent_conv.append(r3["abc"]["convergence_iterations"])
        pso_eq_conv.append(r1["pso"]["convergence_iterations"])
        pso_ent_conv.append(r3["pso"]["convergence_iterations"])

    # Aggregates
    mean_abc_c1 = np.mean(abc_eq_costs)
    mean_abc_c3 = np.mean(abc_ent_costs)
    mean_pso_c1 = np.mean(pso_eq_costs)
    mean_pso_c3 = np.mean(pso_ent_costs)

    mean_abc_u1 = np.mean(abc_eq_unmet)
    mean_abc_u3 = np.mean(abc_ent_unmet)
    mean_pso_u1 = np.mean(pso_eq_unmet)
    mean_pso_u3 = np.mean(pso_ent_unmet)

    mean_abc_conv1 = np.mean(abc_eq_conv)
    mean_abc_conv3 = np.mean(abc_ent_conv)
    mean_pso_conv1 = np.mean(pso_eq_conv)
    mean_pso_conv3 = np.mean(pso_ent_conv)

    abc_cost_change_pct = ((mean_abc_c3 - mean_abc_c1) / mean_abc_c1) * 100.0
    pso_cost_change_pct = ((mean_pso_c3 - mean_pso_c1) / mean_pso_c1) * 100.0

    abc_unmet_change = mean_abc_u3 - mean_abc_u1
    pso_unmet_change = mean_pso_u3 - mean_pso_u1

    abc_conv_change = mean_abc_conv3 - mean_abc_conv1
    pso_conv_change = mean_pso_conv3 - mean_pso_conv1

    print("=" * 105)
    print("\n" + "=" * 90)
    print("                     OVERALL ALGORITHM BENEFIT & RESILIENCE SUMMARY                        ")
    print("=" * 90)
    print(f"{'Performance Metric':<32} | {'ABC (Equal)':<13} | {'ABC (Entropy)':<13} | {'PSO (Equal)':<13} | {'PSO (Entropy)':<13}")
    print("-" * 90)
    print(f"{'Mean Daily Cost (₹)':<32} | ₹{mean_abc_c1:<12.2f} | ₹{mean_abc_c3:<12.2f} | ₹{mean_pso_c1:<12.2f} | ₹{mean_pso_c3:<12.2f}")
    print(f"{'Cost Delta (% change)':<32} | {'Baseline':<13} | {abc_cost_change_pct:+12.2f}% | {'Baseline':<13} | {pso_cost_change_pct:+12.2f}%")
    print(f"{'Mean Unmet Load (kWh)':<32} | {mean_abc_u1:<13.2f} | {mean_abc_u3:<13.2f} | {mean_pso_u1:<13.2f} | {mean_pso_u3:<13.2f}")
    print(f"{'Unmet Load Delta (kWh)':<32} | {'Baseline':<13} | {abc_unmet_change:+13.2f} | {'Baseline':<13} | {pso_unmet_change:+13.2f}")
    print(f"{'Mean Convergence Speed (Iter)':<32} | {mean_abc_conv1:<13.1f} | {mean_abc_conv3:<13.1f} | {mean_pso_conv1:<13.1f} | {mean_pso_conv3:<13.1f}")
    print(f"{'Convergence Delta (Iter)':<32} | {'Baseline':<13} | {abc_conv_change:+13.1f} | {'Baseline':<13} | {pso_conv_change:+13.1f}")
    print("=" * 90)

    # Benefit deduction
    print("\nANALYSIS & CONCLUSION:")
    if mean_abc_c3 < mean_pso_c3:
        print(" -> Cost Efficiency: ABC achieves lower overall operational + capital cost under Shannon Entropy weighting.")
    else:
        print(" -> Cost Efficiency: PSO achieves lower overall operational + capital cost under Shannon Entropy weighting.")

    if abs(abc_unmet_change) > abs(pso_unmet_change) or mean_abc_u3 <= mean_pso_u3:
        print(" -> Reliability Benefit: ABC responds more effectively to the high Unmet Load entropy weight.")
    else:
        print(" -> Reliability Benefit: PSO responds more effectively to the high Unmet Load entropy weight.")

    if pso_conv_change < abc_conv_change:
        print(" -> Convergence Advantage: PSO converges in fewer iterations across the 10 scenarios.")
    else:
        print(" -> Convergence Advantage: ABC shows superior convergence stability across iterations.")

    # Conclude which benefits more
    abc_score = (1 if mean_abc_c3 <= mean_pso_c3 else 0) + (1 if mean_abc_u3 <= mean_pso_u3 else 0)
    pso_score = (1 if mean_pso_c3 < mean_abc_c3 else 0) + (1 if mean_pso_u3 < mean_abc_u3 else 0)
    winner_str = "ABC" if abc_score >= pso_score else "PSO"
    print(f"\n OVERALL VERDICT: {winner_str} benefits more comprehensively from Shannon Entropy weighting,")
    print(" achieving superior objective alignment between cost minimization and microgrid resilience!")
    print("=" * 90 + "\n")


def main():
    print_banner()

    results_json_path = Path(__file__).parent / "results_real.json"
    results_entropy_json_path = Path(__file__).parent / "results_real_entropy.json"

    # =========================================================================
    # PHASE 1 — First run with equal/default weights (existing baseline)
    # =========================================================================
    print("\n>>> PHASE 1: Running 10 Scenarios with Default/Equal Weights...")
    phase1_results = run_pipeline(
        weights_abc=None,
        weights_pso=None,
        save_json_path=results_json_path,
        generate_plots=True,
        phase_title="PHASE 1: Equal / Baseline Weights",
        verbose_scenarios=True,
    )

    # =========================================================================
    # PHASE 2 — Compute Shannon Entropy Weights from Phase 1 Results
    # =========================================================================
    print("\n>>> PHASE 2: Computing Shannon Entropy Weights from Phase 1 Results...")
    abc_w, pso_w = compute_abc_pso_weights(str(results_json_path))

    labels = ["Capital", "Op Cost", "Loss", "Unmet", "Curtail"]

    print("\n[Entropy Weights] ABC:")
    for l, w in zip(labels, abc_w):
        extra = "  <-- highest (most variation across scenarios)" if w == max(abc_w) else ""
        print(f"  {l:<9s}: {w:.4f}{extra}")

    print("\n[Entropy Weights] PSO:")
    for l, w in zip(labels, pso_w):
        extra = "  <-- highest" if w == max(pso_w) else ""
        print(f"  {l:<9s}: {w:.4f}{extra}")

    print("\nNotice: High-variation objectives (e.g. Unmet Load / Curtailment / Op Cost) receive")
    print("automatically scaled weights based on Shannon Information Entropy — not assumed.")

    # FIX 1: Add weights into results_real.json and re-save
    for scenario in phase1_results:
        scenario["abc_weights"] = abc_w.tolist()
        scenario["pso_weights"] = pso_w.tolist()
        scenario["weight_method"] = "shannon_entropy"

    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(phase1_results, f, indent=2)

    # =========================================================================
    # PHASE 3 — Re-run optimization with Shannon Entropy Weights
    # =========================================================================
    print("\n>>> PHASE 3: Re-running Optimization with Shannon Entropy Weights...")
    phase3_results = run_pipeline(
        weights_abc=abc_w,
        weights_pso=pso_w,
        save_json_path=results_entropy_json_path,
        generate_plots=False,
        phase_title="PHASE 3: Shannon Entropy Weights",
        verbose_scenarios=True,
    )

    for scenario in phase3_results:
        scenario["abc_weights"] = abc_w.tolist()
        scenario["pso_weights"] = pso_w.tolist()
        scenario["weight_method"] = "shannon_entropy"

    with open(results_entropy_json_path, "w", encoding="utf-8") as f:
        json.dump(phase3_results, f, indent=2)

    # =========================================================================
    # PHASE 4 — Side-by-Side Comparison
    # =========================================================================
    print("\n>>> PHASE 4: Comparing Equal Weights vs Shannon Entropy Weights Results...")
    print_comparison_analysis(phase1_results, phase3_results)

    # =========================================================================
    # PHASE 5 — Autonomous Capacity Sizing & Financial Recommendations
    # =========================================================================
    print("\n>>> PHASE 5: Generating Autonomous Capacity Sizing & Financial Recommendations...")
    from recommendation.engine import generate_full_report, save_recommendations
    rec_dict, rep_text = generate_full_report(phase3_results)
    save_recommendations(rec_dict, rep_text, output_dir=Path(__file__).parent)


if __name__ == "__main__":
    main()

