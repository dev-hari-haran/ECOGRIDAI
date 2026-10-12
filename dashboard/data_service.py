"""
data_service.py - Data Access & Extraction Layer for EcoGridAI Dashboard

Role: Loads and normalizes benchmark results from JSON files across synthetic
and real 33-bus microgrid optimization pipelines, handling both Baseline (Equal Weights)
and Shannon Entropy-weighted datasets.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONFIG: Dict[str, Any] = {
    "real_baseline_path": Path("results_real.json"),
    "real_entropy_path": Path("results_real_entropy.json"),
    "fallback_search_dirs": [Path("."), Path("..")],
}


def _resolve_file_path(target: Path) -> Path:
    """Resolves target JSON file path across current working directory and fallback directories."""
    if target.is_file():
        return target.resolve()

    current_dir = Path(__file__).parent.parent
    candidate = (current_dir / target).resolve()
    if candidate.is_file():
        return candidate

    for sdir in CONFIG["fallback_search_dirs"]:
        cand = (current_dir / sdir / target.name).resolve()
        if cand.is_file():
            return cand

    return target


def load_results(pipeline: str = "real", mode: str = "entropy") -> List[Dict[str, Any]]:
    """
    Loads benchmark dataset based on pipeline and weighting mode.

    Args:
        pipeline: 'real' (33-Bus dataset) or 'synthetic' (Synthetic profile dataset)
        mode: 'entropy' (Shannon Entropy weights) or 'baseline' (Equal weights)

    Returns:
        List of scenario result dictionaries (length 10).
    """
    pipeline_lower = pipeline.lower()
    mode_lower = mode.lower()
    file_path = CONFIG["real_entropy_path"] if "entr" in mode_lower else CONFIG["real_baseline_path"]

    resolved_path = _resolve_file_path(file_path)

    if not resolved_path.is_file():
        # Fallback to alternate file if selected one is absent
        alt_path = _resolve_file_path(CONFIG["real_entropy_path"])
        if alt_path.is_file():
            resolved_path = alt_path
        else:
            raise FileNotFoundError(f"Benchmark results file not found at '{resolved_path}' or candidate locations.")

    with open(resolved_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def get_scenario_names(results: List[Dict[str, Any]]) -> List[str]:
    """Extracts ordered list of scenario names from results."""
    return [s.get("scenario_name", f"Scenario {i+1}") for i, s in enumerate(results)]


def get_scenario_data(results: List[Dict[str, Any]], scenario_name: str) -> Dict[str, Any]:
    """Retrieves full scenario result dictionary by scenario name."""
    for s in results:
        if s.get("scenario_name") == scenario_name:
            return s
    return results[0] if results else {}


def extract_comparison_metrics(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extracts structured comparison metrics for a scenario comparing ABC and PSO.
    Returns list of dicts: [{metric, abc, pso, unit, winner, format_spec}]
    """
    abc = scenario.get("abc", {})
    pso = scenario.get("pso", {})

    metrics = [
        {
            "metric": "Best Fitness Score",
            "abc": float(abc.get("fitness", 0.0)),
            "pso": float(pso.get("fitness", 0.0)),
            "unit": "",
            "better": "lower",
            "fmt": "{:.4f}",
        },
        {
            "metric": "Total Daily Cost",
            "abc": float(abc.get("total_cost", 0.0)),
            "pso": float(pso.get("total_cost", 0.0)),
            "unit": "₹/day",
            "better": "lower",
            "fmt": "₹{:,.2f}",
        },
        {
            "metric": "Capital Cost",
            "abc": float(abc.get("capital_cost", abc.get("c_capital", 0.0))),
            "pso": float(pso.get("capital_cost", pso.get("c_capital", 0.0))),
            "unit": "₹/day",
            "better": "lower",
            "fmt": "₹{:,.2f}",
        },
        {
            "metric": "Operational Cost",
            "abc": float(abc.get("operational_cost", abc.get("c_op", 0.0))),
            "pso": float(pso.get("operational_cost", pso.get("c_op", 0.0))),
            "unit": "₹/day",
            "better": "lower",
            "fmt": "₹{:,.2f}",
        },
        {
            "metric": "Total System Energy Loss",
            "abc": float(abc.get("energy_loss_kwh", abc.get("energy_loss", 0.0))),
            "pso": float(pso.get("energy_loss_kwh", pso.get("energy_loss", 0.0))),
            "unit": "kWh",
            "better": "lower",
            "fmt": "{:,.2f} kWh",
        },
        {
            "metric": "Load Satisfaction Rate",
            "abc": float(abc.get("load_satisfaction", 100.0)),
            "pso": float(pso.get("load_satisfaction", 100.0)),
            "unit": "%",
            "better": "higher",
            "fmt": "{:.2f}%",
        },
        {
            "metric": "Renewable Utilization",
            "abc": float(abc.get("renewable_utilization", 0.0)),
            "pso": float(pso.get("renewable_utilization", 0.0)),
            "unit": "%",
            "better": "higher",
            "fmt": "{:.2f}%",
        },
        {
            "metric": "Unmet Load",
            "abc": float(abc.get("unmet_load_kwh", 0.0)),
            "pso": float(pso.get("unmet_load_kwh", 0.0)),
            "unit": "kWh",
            "better": "lower",
            "fmt": "{:,.2f} kWh",
        },
        {
            "metric": "Curtailment",
            "abc": float(abc.get("curtailment_kwh", 0.0)),
            "pso": float(pso.get("curtailment_kwh", 0.0)),
            "unit": "kWh",
            "better": "lower",
            "fmt": "{:,.2f} kWh",
        },
        {
            "metric": "Convergence Speed",
            "abc": int(abc.get("convergence_iterations", 0)),
            "pso": int(pso.get("convergence_iterations", 0)),
            "unit": "iterations",
            "better": "lower",
            "fmt": "{:d} iter",
        },
        {
            "metric": "Execution Runtime",
            "abc": float(abc.get("computational_time", 0.0)),
            "pso": float(pso.get("computational_time", 0.0)),
            "unit": "s",
            "better": "lower",
            "fmt": "{:.3f} s",
        },
    ]

    for item in metrics:
        v_abc = item["abc"]
        v_pso = item["pso"]
        if item["better"] == "lower":
            item["winner"] = "ABC" if v_abc < v_pso else ("PSO" if v_pso < v_abc else "Tie")
        else:
            item["winner"] = "ABC" if v_abc > v_pso else ("PSO" if v_pso > v_abc else "Tie")

    return metrics


if __name__ == "__main__":
    # Self-test
    res = load_results(pipeline="real", mode="entropy")
    names = get_scenario_names(res)
    print(f"Loaded {len(res)} scenarios. First: '{names[0]}'")
    first_sc = get_scenario_data(res, names[0])
    metrics = extract_comparison_metrics(first_sc)
    for m in metrics[:5]:
        print(f"  {m['metric']:<28} | ABC: {m['abc']} | PSO: {m['pso']} | Winner: {m['winner']}")
