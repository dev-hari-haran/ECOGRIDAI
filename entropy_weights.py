import json
from pathlib import Path
from typing import Tuple
import numpy as np


def shannon_entropy_weights(decision_matrix: np.ndarray) -> np.ndarray:
    """
    Computes objective weights using Shannon Entropy Method.

    Args:
        decision_matrix: shape (n_scenarios, n_objectives)
        Each row = one scenario
        Each col = one objective (capital, op, loss, unmet, curtail)

    Returns:
        weights: shape (n_objectives,) summing to 1.0
    """
    n, m = decision_matrix.shape

    # Step 1: Normalize each column (sum normalization)
    col_sums = decision_matrix.sum(axis=0)
    norm = decision_matrix / (col_sums + 1e-9)

    # Step 2: Compute entropy for each objective
    # E_j = -1/ln(n) * sum(p_ij * ln(p_ij))
    ln_n = np.log(n)
    E = np.zeros(m)
    for j in range(m):
        p = norm[:, j]
        p = np.clip(p, 1e-9, 1.0)
        E[j] = -np.sum(p * np.log(p)) / ln_n

    # Step 3: Divergence (information content)
    d = 1.0 - E

    # Step 4: Final weights
    weights = d / d.sum()

    return weights


def compute_abc_pso_weights(results_json_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reads results.json, extracts ABC and PSO matrices separately,
    computes entropy weights for each algorithm independently.

    Returns:
        abc_weights: np.array shape (5,)
        pso_weights: np.array shape (5,)
    """
    json_path = Path(results_json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    abc_rows = []
    pso_rows = []

    for scenario in results:
        abc_entry = scenario["abc"]
        pso_entry = scenario["pso"]

        # Extract ABC metrics with fallbacks for legacy key compatibility
        c_cap_abc = abc_entry.get("capital_cost", abc_entry.get("c_capital", 0.0))
        c_op_abc = abc_entry.get("operational_cost", abc_entry.get("c_op", 0.0))
        loss_abc = abc_entry.get("energy_loss_kwh", abc_entry.get("energy_loss", abc_entry.get("total_loss", 0.0)))
        unmet_abc = abc_entry.get("unmet_load_kwh", abc_entry.get("total_unmet_load", abc_entry.get("unmet_load", 0.0)))
        curtail_abc = abc_entry.get("curtailment_kwh", abc_entry.get("total_curtailment", abc_entry.get("curtailment", 0.0)))

        # Fallback for unmet load if zero and load_satisfaction < 100%
        if unmet_abc == 0.0 and "load_satisfaction" in abc_entry:
            sat = abc_entry["load_satisfaction"]
            if sat < 99.99:
                load_mult = scenario.get("scenario_params", {}).get("load_multiplier", 1.0)
                base_load = 47820.0
                unmet_abc = base_load * load_mult * (1.0 - sat / 100.0)

        abc_rows.append([c_cap_abc, c_op_abc, loss_abc, unmet_abc, curtail_abc])

        # Extract PSO metrics with fallbacks
        c_cap_pso = pso_entry.get("capital_cost", pso_entry.get("c_capital", 0.0))
        c_op_pso = pso_entry.get("operational_cost", pso_entry.get("c_op", 0.0))
        loss_pso = pso_entry.get("energy_loss_kwh", pso_entry.get("energy_loss", pso_entry.get("total_loss", 0.0)))
        unmet_pso = pso_entry.get("unmet_load_kwh", pso_entry.get("total_unmet_load", pso_entry.get("unmet_load", 0.0)))
        curtail_pso = pso_entry.get("curtailment_kwh", pso_entry.get("total_curtailment", pso_entry.get("curtailment", 0.0)))

        if unmet_pso == 0.0 and "load_satisfaction" in pso_entry:
            sat = pso_entry["load_satisfaction"]
            if sat < 99.99:
                load_mult = scenario.get("scenario_params", {}).get("load_multiplier", 1.0)
                base_load = 47820.0
                unmet_pso = base_load * load_mult * (1.0 - sat / 100.0)

        pso_rows.append([c_cap_pso, c_op_pso, loss_pso, unmet_pso, curtail_pso])

    abc_matrix = np.array(abc_rows, dtype=np.float64)
    pso_matrix = np.array(pso_rows, dtype=np.float64)

    abc_weights = shannon_entropy_weights(abc_matrix)
    pso_weights = shannon_entropy_weights(pso_matrix)

    return abc_weights, pso_weights


if __name__ == "__main__":
    # Test with dummy data
    matrix = np.array([
        [14425, 10418, 111.5,    0,    0],
        [18337, 13461, 144.9,    0,    0],
        [14440, 10361, 111.5,    0,    0],
        [14425, 14133, 111.0,  215,    0],
        [32799, 15046, 111.1,    0,    0],
        [10207, 10328, 111.5,    0, 2126],
        [17150, 19106, 133.8,    0,    0],
        [29368, 18237, 110.7,    0,    0],
        [14309, 15914, 111.5,    0,    0],
        [32047, 200631, 132.7, 8543,    0],
    ])
    w = shannon_entropy_weights(matrix)
    labels = ["Capital", "Op Cost", "Loss", "Unmet", "Curtail"]
    print("Entropy Weights:")
    for l, wi in zip(labels, w):
        print(f"  {l:12s}: {wi:.4f}")
    print(f"  Sum: {w.sum():.4f}")
