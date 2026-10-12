"""
abc_optimization.py - Artificial Bee Colony Optimization Algorithm (Real Pipeline)

Role: Search for optimal microgrid planning vector using bee colony metaheuristic with passed profile arrays.
Supports custom multi-objective weights (e.g., Shannon Entropy weights).
"""

from typing import Any, Dict, Tuple
import numpy as np

from objective_function import compute_fitness
from planning_vector import clip_and_cast_vector, get_planning_bounds, sample_random_vector


def run_abc(
    solar_profile: np.ndarray,
    wind_profile: np.ndarray,
    load_profile: np.ndarray,
    grid_available: bool = True,
    battery_available: bool = True,
    bounds: dict = None,
    weights: np.ndarray = None,
    colony_size: int = 30,
    max_iter: int = 100,
    limit: int = None,
    seed: int = 42,
) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    Executes Artificial Bee Colony (ABC) optimization using explicit scenario profile arrays.
    """
    if limit is None:
        limit = 20

    rng = np.random.default_rng(seed)

    if bounds is None:
        bounds = get_planning_bounds(battery_available=battery_available)

    lb = bounds["lb"].copy()
    ub = bounds["ub"].copy()

    dim = bounds["dim"]
    pop_size = colony_size

    population = np.zeros((pop_size, dim), dtype=np.float64)
    fitness = np.zeros(pop_size, dtype=np.float64)
    trial = np.zeros(pop_size, dtype=np.int32)

    # 1. Initialization
    for i in range(pop_size):
        population[i] = rng.uniform(lb, ub)
        population[i] = clip_and_cast_vector(population[i], battery_available=battery_available)

        fitness[i] = compute_fitness(
            population[i],
            solar_profile,
            wind_profile,
            load_profile,
            grid_available=grid_available,
            battery_available=battery_available,
            weights=weights,
        )

    best_idx = np.argmin(fitness)
    best_vector = population[best_idx].copy()
    best_fitness = float(fitness[best_idx])

    fitness_history = np.zeros(max_iter, dtype=np.float64)

    for it in range(max_iter):
        # 2. Employed Bee Phase
        for i in range(pop_size):
            k_candidates = [idx for idx in range(pop_size) if idx != i]
            k = rng.choice(k_candidates)
            j = rng.integers(0, dim)

            phi = rng.uniform(-1.0, 1.0)
            x_new = population[i].copy()
            x_new[j] = population[i][j] + phi * (population[i][j] - population[k][j])
            x_new = clip_and_cast_vector(x_new, battery_available=battery_available)

            f_new = compute_fitness(
                x_new,
                solar_profile,
                wind_profile,
                load_profile,
                grid_available=grid_available,
                battery_available=battery_available,
                weights=weights,
            )

            if f_new < fitness[i]:
                population[i] = x_new
                fitness[i] = f_new
                trial[i] = 0
            else:
                trial[i] += 1

        # 3. Onlooker Bee Phase
        fit_val = np.where(fitness >= 0, 1.0 / (1.0 + fitness), 1.0 + np.abs(fitness))
        prob = fit_val / np.sum(fit_val)

        for _ in range(pop_size):
            i = rng.choice(pop_size, p=prob)
            k_candidates = [idx for idx in range(pop_size) if idx != i]
            k = rng.choice(k_candidates)
            j = rng.integers(0, dim)

            phi = rng.uniform(-1.0, 1.0)
            x_new = population[i].copy()
            x_new[j] = population[i][j] + phi * (population[i][j] - population[k][j])
            x_new = clip_and_cast_vector(x_new, battery_available=battery_available)

            f_new = compute_fitness(
                x_new,
                solar_profile,
                wind_profile,
                load_profile,
                grid_available=grid_available,
                battery_available=battery_available,
                weights=weights,
            )

            if f_new < fitness[i]:
                population[i] = x_new
                fitness[i] = f_new
                trial[i] = 0
            else:
                trial[i] += 1

        # 4. Scout Bee Phase
        max_trial_idx = np.argmax(trial)
        if trial[max_trial_idx] > limit:
            population[max_trial_idx] = rng.uniform(lb, ub)
            population[max_trial_idx] = clip_and_cast_vector(population[max_trial_idx], battery_available=battery_available)

            fitness[max_trial_idx] = compute_fitness(
                population[max_trial_idx],
                solar_profile,
                wind_profile,
                load_profile,
                grid_available=grid_available,
                battery_available=battery_available,
                weights=weights,
            )
            trial[max_trial_idx] = 0

        current_best_idx = np.argmin(fitness)
        if fitness[current_best_idx] < best_fitness:
            best_fitness = float(fitness[current_best_idx])
            best_vector = population[current_best_idx].copy()

        fitness_history[it] = best_fitness

    return best_vector, best_fitness, fitness_history


abc_optimization = run_abc


if __name__ == "__main__":
    dummy_s = np.full(24, 500.0)
    dummy_w = np.full(24, 800.0)
    dummy_l = np.full(24, 1200.0)
    vec, fit, hist = run_abc(dummy_s, dummy_w, dummy_l, max_iter=5, seed=42)
    print("--- RUN ABC TEST ---")
    print(f"Best Fitness: {fit:.4f}")
