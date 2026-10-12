"""
pso_optimization.py - Particle Swarm Optimization Algorithm (Real Pipeline)

Role: Search for optimal microgrid planning vector using Particle Swarm Optimization with passed profile arrays.
Supports custom multi-objective weights (e.g., Shannon Entropy weights).
"""

from typing import Any, Dict, Tuple
import numpy as np

from objective_function import compute_fitness
from planning_vector import clip_and_cast_vector, get_planning_bounds, sample_random_vector


def run_pso(
    solar_profile: np.ndarray,
    wind_profile: np.ndarray,
    load_profile: np.ndarray,
    grid_available: bool = True,
    battery_available: bool = True,
    bounds: dict = None,
    weights: np.ndarray = None,
    n_particles: int = 30,
    max_iter: int = 100,
    w_max: float = 0.9,
    w_min: float = 0.4,
    c1: float = 2.0,
    c2: float = 2.0,
    seed: int = 43,
) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    Executes Particle Swarm Optimization (PSO) using explicit scenario profile arrays.
    """
    rng = np.random.default_rng(seed)

    if bounds is None:
        bounds = get_planning_bounds(battery_available=battery_available)

    lb = bounds["lb"].copy()
    ub = bounds["ub"].copy()

    dim = bounds["dim"]
    v_max = 0.2 * (ub - lb)
    num_particles = n_particles

    particles = np.zeros((num_particles, dim), dtype=np.float64)
    velocities = np.zeros((num_particles, dim), dtype=np.float64)
    fitness = np.zeros(num_particles, dtype=np.float64)

    pbest_positions = np.zeros((num_particles, dim), dtype=np.float64)
    pbest_fitness = np.full(num_particles, np.inf, dtype=np.float64)

    # 1. Initialization
    for i in range(num_particles):
        particles[i] = rng.uniform(lb, ub)
        particles[i] = clip_and_cast_vector(particles[i], battery_available=battery_available)

        velocities[i] = rng.uniform(-v_max, v_max)

        fit_i = compute_fitness(
            particles[i],
            solar_profile,
            wind_profile,
            load_profile,
            grid_available=grid_available,
            battery_available=battery_available,
            weights=weights,
        )
        fitness[i] = fit_i
        pbest_positions[i] = particles[i].copy()
        pbest_fitness[i] = fit_i

    gbest_idx = np.argmin(pbest_fitness)
    gbest_position = pbest_positions[gbest_idx].copy()
    gbest_fitness = float(pbest_fitness[gbest_idx])

    fitness_history = np.zeros(max_iter, dtype=np.float64)

    # 2. Iteration Loop
    for it in range(max_iter):
        w = w_max - it * (w_max - w_min) / max_iter

        for i in range(num_particles):
            r1 = rng.uniform(0.0, 1.0, size=dim)
            r2 = rng.uniform(0.0, 1.0, size=dim)

            cognitive = c1 * r1 * (pbest_positions[i] - particles[i])
            social = c2 * r2 * (gbest_position - particles[i])
            velocities[i] = w * velocities[i] + cognitive + social
            velocities[i] = np.clip(velocities[i], -v_max, v_max)

            particles[i] = particles[i] + velocities[i]
            particles[i] = clip_and_cast_vector(particles[i], battery_available=battery_available)

            fit_current = compute_fitness(
                particles[i],
                solar_profile,
                wind_profile,
                load_profile,
                grid_available=grid_available,
                battery_available=battery_available,
                weights=weights,
            )
            fitness[i] = fit_current

            if fit_current < pbest_fitness[i]:
                pbest_fitness[i] = fit_current
                pbest_positions[i] = particles[i].copy()

                if fit_current < gbest_fitness:
                    gbest_fitness = float(fit_current)
                    gbest_position = particles[i].copy()

        fitness_history[it] = gbest_fitness

    return gbest_position, gbest_fitness, fitness_history


pso_optimization = run_pso


if __name__ == "__main__":
    dummy_s = np.full(24, 500.0)
    dummy_w = np.full(24, 800.0)
    dummy_l = np.full(24, 1200.0)
    vec, fit, hist = run_pso(dummy_s, dummy_w, dummy_l, max_iter=5, seed=43)
    print("--- RUN PSO TEST ---")
    print(f"Best Fitness: {fit:.4f}")
