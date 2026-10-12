"""
plot_results_real.py - Real Data & 33-Bus Network Visualization Suite

Role: Generates high-resolution visualization charts comparing ABC and PSO results on real grid dataset,
including 33-bus distribution system topology, bus-wise generation, and transmission loss profiles.

Plots Generated:
1. ABC Convergence Curve
2. PSO Convergence Curve
3. ABC vs PSO Convergence (Direct Comparison)
4. 24-Hour Stacked Dispatch Area Chart
5. Battery SOC Profile Curve
6. Optimal Planning Vector Comparison Bar Chart
7. Cost Breakdown Chart
8. Renewable Energy Utilization vs Curtailment Chart
9. 2x2 Summary Dashboard Grid Figure
10. Bus-Wise Generation Contribution Bar Chart (Bus 6, Bus 13, Bus 30)
11. Transmission Cable Loss per Bus across 24 Hours (Line Chart)
12. Real vs Synthetic Load Demand Comparison Chart
13. 33-Bus Network Topology Diagram with PV & Wind Bus Highlights
14. 10-Scenario Benchmark Suite Plots
"""

import os
from pathlib import Path
from typing import Any, Dict, List
import matplotlib.pyplot as plt
import numpy as np

from bus_network import IEEE_33_BUS_EDGES
from planning_vector import VAR_NAMES

# Styling Config
PLT_STYLE = {
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#CBD5E1",
    "axes.labelcolor": "#1E293B",
    "xtick.color": "#334155",
    "ytick.color": "#334155",
    "grid.color": "#E2E8F0",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "text.color": "#0F172A",
    "legend.facecolor": "#FFFFFF",
    "legend.edgecolor": "#CBD5E1",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
}

COLOR_ABC = "#16A34A"        # Green
COLOR_PSO = "#0288D1"        # Sky Blue
COLOR_SOLAR = "#F59E0B"      # Gold
COLOR_WIND = "#0288D1"       # Deep Cyan
COLOR_BAT_DIS = "#9333EA"    # Purple
COLOR_GRID = "#F97316"       # Orange
COLOR_LOAD = "#DC2626"       # Red

COLOR_BUS13 = "#F59E0B"      # Solar PV 1
COLOR_BUS30 = "#D97706"      # Solar PV 2
COLOR_BUS6 = "#0288D1"       # Wind


def set_plot_style():
    plt.rcParams.update(PLT_STYLE)


def plot_results_real(
    abc_history: np.ndarray,
    pso_history: np.ndarray,
    abc_vector: np.ndarray,
    pso_vector: np.ndarray,
    abc_dispatch: Dict[str, Any],
    pso_dispatch: Dict[str, Any],
    real_data: Dict[str, Any] = None,
    output_dir: str = "Plot_real",
    save_prefix: str = "plot_real_",
) -> List[str]:
    """Generates all single-run real data visualizations in output_dir."""
    set_plot_style()
    os.makedirs(output_dir, exist_ok=True)
    saved_files = []
    hours = np.arange(1, 25)

    best_dispatch = pso_dispatch if pso_dispatch["totals"]["total_cost"] <= abc_dispatch["totals"]["total_cost"] else abc_dispatch
    h = best_dispatch["hourly"]

    # 1. Dispatch Profile Stacked Area
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.stackplot(
        hours,
        h["solar_used"],
        h["wind_used"],
        h["bat_dis"],
        h["grid_import"],
        labels=["Solar Used", "Wind Used", "Battery Discharge", "Grid Import"],
        colors=[COLOR_SOLAR, COLOR_WIND, COLOR_BAT_DIS, COLOR_GRID],
        alpha=0.85,
    )
    ax.plot(hours, h["load"], color=COLOR_LOAD, linewidth=3.0, linestyle="--", label="Real Load Curve")
    ax.set_title("24-Hour Real Microgrid Energy Dispatch Profile", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Hour of Day (t)", fontsize=11)
    ax.set_ylabel("Power Output (kW)", fontsize=11)
    ax.set_xticks(hours)
    ax.grid(True)
    ax.legend(loc="upper left")
    plt.tight_layout()
    f1 = os.path.join(output_dir, f"{save_prefix}dispatch_profile.png")
    plt.savefig(f1, dpi=300)
    plt.close()
    saved_files.append(f1)

    # 2. Bus-Wise Generation Contribution Bar Chart
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x_h = np.arange(1, 25)
    w = 0.25
    ax.bar(x_h - w, h["gen_bus13"], width=w, label="Bus 13 (PV 1: 851.5 kW)", color=COLOR_BUS13, alpha=0.85)
    ax.bar(x_h, h["gen_bus30"], width=w, label="Bus 30 (PV 2: 1157.6 kW)", color=COLOR_BUS30, alpha=0.85)
    ax.bar(x_h + w, h["gen_bus6"], width=w, label="Bus 6 (Wind: 2097.97 kW)", color=COLOR_BUS6, alpha=0.85)
    ax.set_title("Bus-Wise Generation Contribution Across 24 Hours", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Hour of Day (t)", fontsize=11)
    ax.set_ylabel("Power Generation (kW)", fontsize=11)
    ax.set_xticks(x_h)
    ax.grid(True, axis="y")
    ax.legend(loc="upper right")
    plt.tight_layout()
    f2 = os.path.join(output_dir, f"{save_prefix}bus_generation_contribution.png")
    plt.savefig(f2, dpi=300)
    plt.close()
    saved_files.append(f2)

    # 3. Transmission Loss per Bus across 24 Hours (Line Chart)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(hours, h["loss_bus13"], color=COLOR_BUS13, linewidth=2.5, marker="o", label="Bus 13 Cable Loss (12% factor)")
    ax.plot(hours, h["loss_bus30"], color=COLOR_BUS30, linewidth=2.5, marker="s", label="Bus 30 Cable Loss (11% factor)")
    ax.plot(hours, h["loss_bus6"], color=COLOR_BUS6, linewidth=2.5, marker="^", label="Bus 6 Cable Loss (5% factor)")
    ax.set_title("33-Bus Transmission Cable Losses Across 24 Hours", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Hour of Day (t)", fontsize=11)
    ax.set_ylabel("Transmission Loss (kW)", fontsize=11)
    ax.set_xticks(hours)
    ax.grid(True)
    ax.legend(loc="upper left")
    plt.tight_layout()
    f3 = os.path.join(output_dir, f"{save_prefix}bus_transmission_losses.png")
    plt.savefig(f3, dpi=300)
    plt.close()
    saved_files.append(f3)

    # 4. Real vs Synthetic Load Comparison Chart
    if real_data is not None:
        fig, ax = plt.subplots(figsize=(9, 5))
        synth_load = np.array([
            1450.0, 970.0, 808.0, 646.0, 646.0, 646.0,
            808.0, 1130.0, 1292.0, 1615.0, 1938.0, 2196.0,
            2422.0, 2745.0, 3068.0, 3230.0, 3391.0, 3585.0,
            3715.0, 3456.0, 3230.0, 2745.0, 2422.0, 1938.0
        ], dtype=np.float64)

        ax.plot(hours, real_data["hourly_load"], color="#0F172A", linewidth=2.5, marker="o", label="Real Loaded Dataset Curve")
        ax.plot(hours, synth_load, color="#94A3B8", linewidth=2.0, linestyle="--", marker="x", label="Synthetic Reference Curve")
        ax.set_title("Real vs Synthetic Load Profile Comparison", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Hour of Day (t)", fontsize=11)
        ax.set_ylabel("Load Demand (kW)", fontsize=11)
        ax.set_xticks(hours)
        ax.grid(True)
        ax.legend(loc="upper left")
        plt.tight_layout()
        f4 = os.path.join(output_dir, f"{save_prefix}real_vs_synthetic_load.png")
        plt.savefig(f4, dpi=300)
        plt.close()
        saved_files.append(f4)

    # 5. 33-Bus Network Diagram Node Graph
    fig, ax = plt.subplots(figsize=(12, 7))

    # Node positions layout for 33-bus radial network
    pos = {
        1: (0, 0), 2: (1, 0), 3: (2, 0), 4: (3, 0), 5: (4, 0), 6: (5, 0), 7: (6, 0), 8: (7, 0), 9: (8, 0), 10: (9, 0), 11: (10, 0), 12: (11, 0), 13: (12, 0), 14: (13, 0), 15: (14, 0), 16: (15, 0), 17: (16, 0), 18: (17, 0),
        19: (1, 1), 20: (2, 1), 21: (3, 1), 22: (4, 1),
        23: (4, -1), 24: (5, -1), 25: (6, -1),
        26: (5, 1.5), 27: (6, 1.5), 28: (7, 1.5), 29: (8, 1.5), 30: (9, 1.5), 31: (10, 1.5), 32: (11, 1.5), 33: (12, 1.5)
    }

    # Draw edges
    for u, v in IEEE_33_BUS_EDGES:
        x_vals = [pos[u][0], pos[v][0]]
        y_vals = [pos[u][1], pos[v][1]]
        ax.plot(x_vals, y_vals, color="#94A3B8", linewidth=1.5, zorder=1)

    # Draw nodes
    for bus_id, (x_c, y_c) in pos.items():
        if bus_id == 1:
            color = "#DC2626"  # Root / Substation Red
            size = 400
            label_text = "Bus 1\n(Substation)"
        elif bus_id in [13, 30]:
            color = COLOR_SOLAR  # PV Amber
            size = 350
            label_text = f"Bus {bus_id}\n(PV)"
        elif bus_id == 6:
            color = COLOR_WIND  # Wind Blue
            size = 350
            label_text = "Bus 6\n(Wind)"
        else:
            color = "#64748B"  # Load Bus Slate
            size = 180
            label_text = f"{bus_id}"

        ax.scatter(x_c, y_c, s=size, color=color, zorder=2, edgecolors="#0F172A", linewidth=1.2)
        ax.text(x_c, y_c - 0.28, label_text, ha="center", va="top", fontsize=8, fontweight="bold")

    ax.set_title("33-Bus Radial Distribution Network Topology & Generator Bus Mapping", fontsize=14, fontweight="bold", pad=15)
    ax.axis("off")
    plt.tight_layout()
    f5 = os.path.join(output_dir, f"{save_prefix}33_bus_network_diagram.png")
    plt.savefig(f5, dpi=300)
    plt.close()
    saved_files.append(f5)

    return saved_files
