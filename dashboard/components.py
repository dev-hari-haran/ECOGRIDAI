"""
components.py - Visual Components, KPI Cards & Plotly Visualizers for EcoGridAI Dashboard

Role: Generates modern dark-themed interactive Plotly figures, comparison metric cards,
and responsive UI widgets for the Streamlit presentation layer.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CONFIG: Dict[str, Any] = {
    "color_abc": "#E5FE98",       # Secondary — Lime Citrus (ABC accent)
    "color_pso": "#7DD3FC",       # Sky Blue 300 (PSO accent)
    "color_solar": "#F59E0B",     # Gold Amber
    "color_wind": "#34D399",      # Emerald
    "color_bat_dis": "#C084FC",   # Violet 400
    "color_grid": "#FB923C",      # Orange 400
    "color_load": "#F87171",      # Red 400
    "color_bg_dark": "#2D3E2C",   # Primary — Deep Forest Green
    "color_card_dark": "#3A5038", # Primary Light — Fern Green
    "color_gridline": "#4A6348",  # Primary Mid — Moss Green
    "color_text": "#E5FE98",      # Secondary — Lime Citrus
    "color_text_muted": "#A8C4A6",# Muted sage green
}


def apply_dark_layout(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """Applies unified dark theme styling to Plotly figures."""
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.05,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 16, "color": CONFIG["color_text"], "family": "Segoe UI, Inter, sans-serif"},
        },
        paper_bgcolor=CONFIG["color_card_dark"],
        plot_bgcolor=CONFIG["color_card_dark"],
        font={"color": CONFIG["color_text_muted"], "family": "Segoe UI, Inter, sans-serif"},
        height=height,
        margin={"l": 45, "r": 35, "t": 60, "b": 45},
        legend={
            "bgcolor": "rgba(45, 62, 44, 0.85)",
            "bordercolor": CONFIG["color_gridline"],
            "borderwidth": 1,
            "font": {"color": CONFIG["color_text"], "size": 11},
        },
        xaxis={
            "gridcolor": CONFIG["color_gridline"],
            "linecolor": CONFIG["color_gridline"],
            "zerolinecolor": CONFIG["color_gridline"],
        },
        yaxis={
            "gridcolor": CONFIG["color_gridline"],
            "linecolor": CONFIG["color_gridline"],
            "zerolinecolor": CONFIG["color_gridline"],
        },
        hoverlabel={
            "bgcolor": CONFIG["color_bg_dark"],
            "font_size": 12,
            "font_family": "Segoe UI, sans-serif",
        },
    )
    return fig


def build_scenario_benchmark_chart(all_scenarios: List[Dict[str, Any]], metric_key: str = "fitness") -> go.Figure:
    """
    Builds a grouped bar chart comparing ABC vs PSO across all 10 scenarios.
    """
    sc_names = [s.get("scenario_name", f"Sc {i+1}") for i, s in enumerate(all_scenarios)]

    if metric_key == "total_cost":
        title = "10-Scenario Benchmark — Total Daily Cost Comparison (₹/day)"
        y_label = "Daily Cost (₹)"
        abc_vals = [s["abc"].get("total_cost", 0.0) for s in all_scenarios]
        pso_vals = [s["pso"].get("total_cost", 0.0) for s in all_scenarios]
        hover_template = "%{x}<br><b>Cost:</b> ₹%{y:,.2f}<extra></extra>"
    elif metric_key == "load_satisfaction":
        title = "10-Scenario Benchmark — Load Satisfaction Rate (%)"
        y_label = "Satisfaction Rate (%)"
        abc_vals = [s["abc"].get("load_satisfaction", 100.0) for s in all_scenarios]
        pso_vals = [s["pso"].get("load_satisfaction", 100.0) for s in all_scenarios]
        hover_template = "%{x}<br><b>Load Sat:</b> %{y:.2f}%<extra></extra>"
    else:
        title = "10-Scenario Benchmark — Fitness Score Comparison (ABC vs PSO)"
        y_label = "Fitness Score (F) — Lower is Better"
        abc_vals = [s["abc"].get("fitness", 0.0) for s in all_scenarios]
        pso_vals = [s["pso"].get("fitness", 0.0) for s in all_scenarios]
        hover_template = "%{x}<br><b>Fitness:</b> %{y:,.4f}<extra></extra>"

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=sc_names,
            y=abc_vals,
            name="ABC Optimization",
            marker_color=CONFIG["color_abc"],
            hovertemplate=hover_template,
        )
    )

    fig.add_trace(
        go.Bar(
            x=sc_names,
            y=pso_vals,
            name="PSO Optimization",
            marker_color=CONFIG["color_pso"],
            hovertemplate=hover_template,
        )
    )

    fig.update_layout(
        barmode="group",
        yaxis_title=y_label,
        xaxis_tickangle=-25,
    )

    return apply_dark_layout(fig, title=title, height=430)


def build_dispatch_profile_chart(dispatch_data: Dict[str, Any], title_suffix: str = "ABC") -> go.Figure:
    """
    Builds a stacked area chart showing 24-hour generation contribution vs load demand.
    """
    hourly = dispatch_data.get("hourly", {})
    hours = list(range(1, 25))

    solar = hourly.get("solar_used", np.zeros(24))
    wind = hourly.get("wind_used", np.zeros(24))
    bat_dis = hourly.get("bat_dis", np.zeros(24))
    grid = hourly.get("grid_import", np.zeros(24))
    load = hourly.get("load", np.zeros(24))
    unmet = hourly.get("unmet_load", np.zeros(24))

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=solar,
            mode="lines",
            line={"width": 0.5, "color": CONFIG["color_solar"]},
            stackgroup="generation",
            name="Solar PV",
            fillcolor="rgba(245, 158, 11, 0.75)",
            hovertemplate="Hour %{x}: %{y:.1f} kW<extra>Solar PV</extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=wind,
            mode="lines",
            line={"width": 0.5, "color": CONFIG["color_wind"]},
            stackgroup="generation",
            name="Wind Turbines",
            fillcolor="rgba(6, 182, 212, 0.75)",
            hovertemplate="Hour %{x}: %{y:.1f} kW<extra>Wind</extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=bat_dis,
            mode="lines",
            line={"width": 0.5, "color": CONFIG["color_bat_dis"]},
            stackgroup="generation",
            name="Battery Discharge",
            fillcolor="rgba(139, 92, 246, 0.75)",
            hovertemplate="Hour %{x}: %{y:.1f} kW<extra>Battery Discharge</extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=grid,
            mode="lines",
            line={"width": 0.5, "color": CONFIG["color_grid"]},
            stackgroup="generation",
            name="Grid Import",
            fillcolor="rgba(249, 115, 22, 0.75)",
            hovertemplate="Hour %{x}: %{y:.1f} kW<extra>Grid Import</extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=load,
            mode="lines+markers",
            line={"width": 2.5, "color": CONFIG["color_load"], "dash": "dash"},
            marker={"size": 4, "color": CONFIG["color_load"]},
            name="Load Demand",
            hovertemplate="Hour %{x}: %{y:.1f} kW<extra>Load Demand</extra>",
        )
    )

    if float(np.sum(unmet)) > 0:
        fig.add_trace(
            go.Bar(
                x=hours,
                y=unmet,
                name="Unmet Load Deficit",
                marker_color="rgba(239, 68, 68, 0.4)",
                hovertemplate="Hour %{x} Deficit: %{y:.1f} kW<extra></extra>",
            )
        )

    fig.update_layout(
        xaxis={"title": "Hour of Day (1 to 24)", "tickmode": "linear", "tick0": 1, "dtick": 1},
        yaxis={"title": "Power Flow (kW)"},
    )

    return apply_dark_layout(fig, title=f"24-Hour Energy Dispatch Profile ({title_suffix})", height=420)


def build_convergence_curves_chart(abc_hist: np.ndarray, pso_hist: np.ndarray) -> go.Figure:
    """
    Builds iteration-by-iteration convergence curves comparing ABC vs PSO.
    """
    iters = list(range(1, len(abc_hist) + 1))

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=iters,
            y=abc_hist,
            mode="lines",
            line={"width": 2.5, "color": CONFIG["color_abc"]},
            name="ABC Optimization",
            hovertemplate="Iteration %{x}: %{y:.4f}<extra>ABC</extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=iters,
            y=pso_hist,
            mode="lines",
            line={"width": 2.5, "color": CONFIG["color_pso"]},
            name="PSO Optimization",
            hovertemplate="Iteration %{x}: %{y:.4f}<extra>PSO</extra>",
        )
    )

    fig.update_layout(
        xaxis={"title": "Iteration (1 to 100)"},
        yaxis={"title": "Best Fitness (F)"},
    )

    return apply_dark_layout(fig, title="Metaheuristic Convergence Curves (ABC vs PSO)", height=380)


def build_cost_breakdown_chart(scenario: Dict[str, Any]) -> go.Figure:
    """
    Builds stacked bar chart comparing Capital and Operational daily cost in ₹.
    """
    abc = scenario.get("abc", {})
    pso = scenario.get("pso", {})

    abc_cap = abc.get("capital_cost", abc.get("c_capital", 0.0))
    abc_op = abc.get("operational_cost", abc.get("c_op", 0.0))

    pso_cap = pso.get("capital_cost", pso.get("c_capital", 0.0))
    pso_op = pso.get("operational_cost", pso.get("c_op", 0.0))

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=["ABC", "PSO"],
            y=[abc_cap, pso_cap],
            name="Capital Cost",
            marker_color="#7DD3FC",  # Sky Blue 300
            hovertemplate="%{x}<br>Capital: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=["ABC", "PSO"],
            y=[abc_op, pso_op],
            name="Operational Cost",
            marker_color="#E5FE98",  # Secondary Lime
            hovertemplate="%{x}<br>Operational: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="stack",
        yaxis={"title": "Cost (₹ / day)"},
    )

    return apply_dark_layout(fig, title="Daily Cost Breakdown: Capital vs Operational", height=380)


def build_battery_soc_chart(soc_history: np.ndarray) -> go.Figure:
    """
    Plots the 24-hour Battery State of Charge (SOC) profile curve with technical limits.
    """
    hours = list(range(1, len(soc_history) + 1))
    soc_pct = soc_history * 100.0 if np.max(soc_history) <= 1.0 else soc_history

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=soc_pct,
            mode="lines+markers",
            line={"width": 2.5, "color": CONFIG["color_bat_dis"]},
            marker={"size": 6, "color": CONFIG["color_bat_dis"]},
            name="Battery SOC (%)",
            hovertemplate="Hour %{x}: %{y:.1f}%<extra>SOC</extra>",
        )
    )

    fig.add_hline(y=95.0, line_dash="dot", line_color="#EF4444", annotation_text="SOC Max (95%)", annotation_position="top right")
    fig.add_hline(y=20.0, line_dash="dot", line_color="#EF4444", annotation_text="SOC Min (20%)", annotation_position="bottom right")

    fig.update_layout(
        xaxis={"title": "Hour of Day (1 to 24)", "tickmode": "linear", "tick0": 1, "dtick": 1},
        yaxis={"title": "State of Charge (%)", "range": [0, 105]},
    )

    return apply_dark_layout(fig, title="24-Hour Battery SOC Profile Curve", height=380)
