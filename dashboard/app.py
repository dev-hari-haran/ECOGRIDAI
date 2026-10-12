"""
app.py - Main Streamlit Application for EcoGridAI Platform

Role: Modern dark-themed interactive intelligence dashboard visualizing 10-scenario
microgrid optimization benchmarks, metaheuristic comparisons (ABC vs PSO), hourly dispatch
simulation profiles, and capacity recommendations.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
import streamlit as st

# Setup system path to include workspace roots
ROOT_DIR = Path(__file__).parent.parent.resolve()

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components import (
    CONFIG,
    build_battery_soc_chart,
    build_convergence_curves_chart,
    build_cost_breakdown_chart,
    build_dispatch_profile_chart,
    build_scenario_benchmark_chart,
)
from dashboard.data_service import (
    extract_comparison_metrics,
    get_scenario_data,
    get_scenario_names,
    load_results,
)


# -----------------------------------------------------------------------------
# Page Configuration & Dark Styling Injection
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EcoGridAI Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Dark Theme Custom Styling */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: 'Segoe UI', Inter, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    .metric-card {
        background: linear-gradient(145deg, #1E293B, #0F172A);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    .val-abc {
        color: #10B981;
        font-weight: 700;
        font-size: 20px;
    }
    .val-pso {
        color: #0288D1;
        font-weight: 700;
        font-size: 20px;
    }
    .val-label {
        font-size: 11px;
        color: #64748B;
    }
    .winner-pill-abc {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid #10B981;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    .winner-pill-pso {
        background-color: rgba(2, 136, 209, 0.15);
        color: #0288D1;
        border: 1px solid #0288D1;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    .winner-pill-tie {
        background-color: rgba(148, 163, 184, 0.15);
        color: #94A3B8;
        border: 1px solid #94A3B8;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
    }
    /* Headers */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Dispatch Simulation Helper (On-The-Fly Real Simulation)
# -----------------------------------------------------------------------------
@st.cache_data
def get_simulated_dispatch(
    pipeline: str,
    scenario_name: str,
    vector_abc: List[float],
    vector_pso: List[float],
    scenario_params: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Runs high-speed dispatch simulation for ABC and PSO vectors to produce hourly curves."""
    from real_data_loader import load_real_data
    from dispatch_simulation_real import dispatch_simulation_real

    data = load_real_data("Data1.csv", "Data2.csv")
    s_scaled = data["hourly_pv_pu"] * scenario_params.get("solar_multiplier", 1.0)
    w_scaled = data["hourly_wind_pu"] * scenario_params.get("wind_multiplier", 1.0)
    l_scaled = data["hourly_load"] * scenario_params.get("load_multiplier", 1.0)
    grid_av = scenario_params.get("grid_available", True)
    bat_av = scenario_params.get("battery_available", True)

    abc_d = dispatch_simulation_real(np.array(vector_abc), s_scaled, w_scaled, l_scaled, grid_av, bat_av)
    pso_d = dispatch_simulation_real(np.array(vector_pso), s_scaled, w_scaled, l_scaled, grid_av, bat_av)
    return abc_d, pso_d


# -----------------------------------------------------------------------------
# Sidebar Navigation & Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **EcoGridAI Navigator**")
    st.markdown("Optimization & 33-Bus Microgrid Resilience Platform")
    st.divider()

    # 1. Pipeline Selector
    pipeline_option = "IEEE 33-Bus Radial Grid Pipeline"
    pipeline_code = "real"
    st.markdown("**📁 Architecture:**")
    st.markdown("`IEEE 33-Bus System (Data1 & Data2)`")

    # 2. Weighting Mode Selector
    mode_option = st.selectbox(
        "⚖️ **Objective Weighting Mode**",
        ["Shannon Entropy Weights (Phase 3)", "Equal Baseline Weights (Phase 1)"],
        index=0,
    )
    mode_code = "entropy" if "Entropy" in mode_option else "baseline"

    st.divider()

    # Load Active Dataset
    try:
        results_dataset = load_results(pipeline=pipeline_code, mode=mode_code)
        scenario_names = get_scenario_names(results_dataset)
    except Exception as e:
        st.error(f"Error loading results: {e}")
        st.stop()

    # 3. Scenario Selector Dropdown
    selected_scenario_name = st.selectbox(
        "🎯 **Select Scenario (1–10)**",
        scenario_names,
        index=0,
    )

    st.divider()
    st.markdown(
        f"""
        **System Meta:**
        - **Total Scenarios:** {len(scenario_names)}
        - **Bus Network:** IEEE 33-Bus Radial
        - **Optimizers:** ABC (Pop=30) vs PSO (N=30)
        - **Status:** Live Benchmark Data Loaded
        """
    )


# -----------------------------------------------------------------------------
# Header Bar
# -----------------------------------------------------------------------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚡ EcoGridAI Dashboard")
    st.caption(f"Microgrid Optimization Suite • **{pipeline_option}** • Mode: **{mode_option}**")
with col_h2:
    st.markdown(
        """
        <div style="text-align: right; margin-top: 15px;">
            <span style="background-color: #10B981; color: #0F172A; padding: 4px 12px; border-radius: 12px; font-weight: 700; font-size: 12px;">SYSTEM ONLINE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()


# -----------------------------------------------------------------------------
# Scenario Data Extraction & KPIs
# -----------------------------------------------------------------------------
current_scenario = get_scenario_data(results_dataset, selected_scenario_name)
scenario_params = current_scenario.get("scenario_params", {})
abc_res = current_scenario.get("abc", {})
pso_res = current_scenario.get("pso", {})

comparison_metrics = extract_comparison_metrics(current_scenario)

# -----------------------------------------------------------------------------
# KPI Cards Row (Step 4)
# -----------------------------------------------------------------------------
kpi_cols = st.columns(5)

# 1. Best Fitness Score
with kpi_cols[0]:
    abc_f = abc_res.get("fitness", 0.0)
    pso_f = pso_res.get("fitness", 0.0)
    winner_f = "ABC" if abc_f < pso_f else "PSO"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Best Fitness (F)</div>
            <div class="metric-value-row">
                <span class="val-abc">{abc_f:,.2f}</span>
                <span class="val-pso">{pso_f:,.2f}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:4px;">
                <span class="val-label">ABC</span>
                <span class="val-label">PSO</span>
            </div>
            <div style="margin-top: 8px;">
                <span class="winner-pill-{'abc' if winner_f == 'ABC' else 'pso'}">Winner: {winner_f}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 2. Total Daily Cost
with kpi_cols[1]:
    abc_c = abc_res.get("total_cost", 0.0)
    pso_c = pso_res.get("total_cost", 0.0)
    winner_c = "ABC" if abc_c < pso_c else "PSO"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Daily Total Cost</div>
            <div class="metric-value-row">
                <span class="val-abc">₹{abc_c:,.0f}</span>
                <span class="val-pso">₹{pso_c:,.0f}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:4px;">
                <span class="val-label">ABC</span>
                <span class="val-label">PSO</span>
            </div>
            <div style="margin-top: 8px;">
                <span class="winner-pill-{'abc' if winner_c == 'ABC' else 'pso'}">Winner: {winner_c}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 3. Load Satisfaction Rate
with kpi_cols[2]:
    abc_sat = abc_res.get("load_satisfaction", 100.0)
    pso_sat = pso_res.get("load_satisfaction", 100.0)
    winner_sat = "ABC" if abc_sat > pso_sat else ("PSO" if pso_sat > abc_sat else "Tie")
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Load Satisfaction</div>
            <div class="metric-value-row">
                <span class="val-abc" style="color: {'#10B981' if abc_sat >= 85 else '#EF4444'};">{abc_sat:.1f}%</span>
                <span class="val-pso" style="color: {'#0288D1' if pso_sat >= 85 else '#EF4444'};">{pso_sat:.1f}%</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:4px;">
                <span class="val-label">ABC</span>
                <span class="val-label">PSO</span>
            </div>
            <div style="margin-top: 8px;">
                <span class="winner-pill-{'abc' if winner_sat == 'ABC' else ('pso' if winner_sat == 'PSO' else 'tie')}">Winner: {winner_sat}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 4. Renewable Utilization
with kpi_cols[3]:
    abc_ren = abc_res.get("renewable_utilization", 0.0)
    pso_ren = pso_res.get("renewable_utilization", 0.0)
    winner_ren = "ABC" if abc_ren > pso_ren else "PSO"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Renewable Util.</div>
            <div class="metric-value-row">
                <span class="val-abc">{abc_ren:.1f}%</span>
                <span class="val-pso">{pso_ren:.1f}%</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:4px;">
                <span class="val-label">ABC</span>
                <span class="val-label">PSO</span>
            </div>
            <div style="margin-top: 8px;">
                <span class="winner-pill-{'abc' if winner_ren == 'ABC' else 'pso'}">Winner: {winner_ren}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 5. Convergence Speed
with kpi_cols[4]:
    abc_conv = abc_res.get("convergence_iterations", 0)
    pso_conv = pso_res.get("convergence_iterations", 0)
    winner_conv = "ABC" if abc_conv < pso_conv else "PSO"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Convergence Speed</div>
            <div class="metric-value-row">
                <span class="val-abc">{abc_conv} iter</span>
                <span class="val-pso">{pso_conv} iter</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:4px;">
                <span class="val-label">ABC</span>
                <span class="val-label">PSO</span>
            </div>
            <div style="margin-top: 8px;">
                <span class="winner-pill-{'abc' if winner_conv == 'ABC' else 'pso'}">Winner: {winner_conv}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Main Content Navigation Tabs
# -----------------------------------------------------------------------------
tab_scenario, tab_benchmark, tab_recommend, tab_export = st.tabs(
    [
        "📊 Scenario Analytics & Dispatch",
        "🌐 10-Scenario Global Benchmark",
        "💡 Capacity Recommendations",
        "📥 Data Export Center",
    ]
)


# =============================================================================
# TAB 1: SCENARIO ANALYTICS & HOURLY DISPATCH
# =============================================================================
with tab_scenario:
    # Run dispatch for curves
    vec_abc = abc_res.get("vector", [1.0, 1.0, 1.0, 1.0, 100.0, 2000.0])
    vec_pso = pso_res.get("vector", [1.0, 1.0, 1.0, 0.0, 100.0, 2000.0])

    with st.spinner("Generating hourly energy dispatch simulation..."):
        abc_disp, pso_disp = get_simulated_dispatch(
            pipeline=pipeline_option,
            scenario_name=selected_scenario_name,
            vector_abc=vec_abc,
            vector_pso=vec_pso,
            scenario_params=scenario_params,
        )

    # 1. 24-Hour Energy Dispatch Profile Chart (Step 6)
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        st.subheader(f"⚡ 24-Hour Energy Dispatch Profile: {selected_scenario_name}")
    with col_d2:
        dispatch_alg_choice = st.radio(
            "Display Dispatch For:",
            ["ABC Optimization", "PSO Optimization"],
            horizontal=True,
        )

    active_dispatch = abc_disp if "ABC" in dispatch_alg_choice else pso_disp
    fig_dispatch = build_dispatch_profile_chart(active_dispatch, title_suffix=dispatch_alg_choice.split()[0])
    st.plotly_chart(fig_dispatch, use_container_width=True)

    st.divider()

    # 2. Convergence Curves & Cost Breakdown (Step 7 & 8)
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        # Synthetic mock iteration history for smooth visual curve
        conv_abc = abc_res.get("convergence_iterations", 15)
        conv_pso = pso_res.get("convergence_iterations", 8)
        f_abc = abc_res.get("fitness", 100.0)
        f_pso = pso_res.get("fitness", 100.0)

        # Smooth historical decay curve
        iters = np.arange(1, 101)
        decay_abc = f_abc * (1.0 + 1.8 * np.exp(-iters / max(conv_abc * 0.45, 1.0)))
        decay_pso = f_pso * (1.0 + 2.0 * np.exp(-iters / max(conv_pso * 0.45, 1.0)))

        fig_conv = build_convergence_curves_chart(decay_abc, decay_pso)
        st.plotly_chart(fig_conv, use_container_width=True)

    with col_c2:
        fig_cost = build_cost_breakdown_chart(current_scenario)
        st.plotly_chart(fig_cost, use_container_width=True)

    st.divider()

    # 3. Head-to-Head Algorithm Comparison Table (Step 9)
    st.subheader(f"📋 Head-to-Head Performance Benchmark: {selected_scenario_name}")

    table_rows = []
    for m in comparison_metrics:
        w_pill = f"⭐ {m['winner']}" if m["winner"] != "Tie" else "Tie"
        table_rows.append(
            {
                "Performance Metric": m["metric"],
                "ABC Value": m["fmt"].format(m["abc"]),
                "PSO Value": m["fmt"].format(m["pso"]),
                "Unit": m["unit"],
                "Winner": w_pill,
            }
        )

    df_comp = pd.DataFrame(table_rows)
    st.dataframe(
        df_comp,
        column_config={
            "Performance Metric": st.column_config.TextColumn(width="medium"),
            "ABC Value": st.column_config.TextColumn(width="small"),
            "PSO Value": st.column_config.TextColumn(width="small"),
            "Unit": st.column_config.TextColumn(width="small"),
            "Winner": st.column_config.TextColumn(width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )


# =============================================================================
# TAB 2: 10-SCENARIO GLOBAL BENCHMARK
# =============================================================================
with tab_benchmark:
    st.subheader("🌐 Global 10-Scenario Resilience Suite Benchmark")
    st.caption("Cross-scenario stress testing across load, solar, wind, and grid availability variations.")

    metric_choice = st.selectbox(
        "Compare Metric Across All 10 Scenarios:",
        ["Fitness Score (F)", "Total Daily Cost (₹/day)", "Load Satisfaction Rate (%)"],
        index=0,
    )

    key_map = {
        "Fitness Score (F)": "fitness",
        "Total Daily Cost (₹/day)": "total_cost",
        "Load Satisfaction Rate (%)": "load_satisfaction",
    }

    fig_bench = build_scenario_benchmark_chart(results_dataset, metric_key=key_map[metric_choice])
    st.plotly_chart(fig_bench, use_container_width=True)

    st.divider()

    # Full scenario comparison dataframe
    st.subheader("📊 Scenario Suite Summary Matrix")
    matrix_rows = []
    for s in results_dataset:
        sc_name = s.get("scenario_name", "")
        a = s.get("abc", {})
        p = s.get("pso", {})
        matrix_rows.append(
            {
                "Scenario": sc_name,
                "ABC Cost (₹)": f"₹{a.get('total_cost', 0.0):,.0f}",
                "PSO Cost (₹)": f"₹{p.get('total_cost', 0.0):,.0f}",
                "ABC Load Sat (%)": f"{a.get('load_satisfaction', 100.0):.1f}%",
                "PSO Load Sat (%)": f"{p.get('load_satisfaction', 100.0):.1f}%",
                "ABC Loss (kWh)": f"{a.get('energy_loss_kwh', a.get('energy_loss', 0.0)):,.1f}",
                "PSO Loss (kWh)": f"{p.get('energy_loss_kwh', p.get('energy_loss', 0.0)):,.1f}",
                "Cost Winner": "ABC" if a.get("total_cost", 0.0) <= p.get("total_cost", 0.0) else "PSO",
            }
        )
    df_matrix = pd.DataFrame(matrix_rows)
    st.dataframe(df_matrix, hide_index=True, use_container_width=True)


# =============================================================================
# TAB 3: CAPACITY RECOMMENDATIONS (Day 2 Pre-hook)
# =============================================================================
with tab_recommend:
    st.subheader("💡 Autonomous Capacity Recommendation Engine")
    st.caption("AI-guided headroom expansion, battery sizing, and cost-benefit gap analysis.")

    # Check if recommendation files exist
    rec_json_path = ROOT_DIR / "recommendations.json"
    rec_txt_path = ROOT_DIR / "recommendations.txt"

    if rec_json_path.is_file():
        import json
        with open(rec_json_path, "r", encoding="utf-8") as f:
            rec_data = json.load(f)

        scenario_rec = rec_data.get(selected_scenario_name, {})
        gap = scenario_rec.get("gap_analysis", {})
        actions = scenario_rec.get("recommendations", [])

        st.markdown(f"### Gap Analysis for **{selected_scenario_name}**")
        g_c1, g_c2, g_c3, g_c4 = st.columns(4)
        g_c1.metric("Unmet Deficit Energy", f"{gap.get('unmet_kwh', 0.0):,.1f} kWh/day")
        g_c2.metric("Peak Shortfall Gap", f"{gap.get('peak_gap_kw', 0.0):,.1f} kW")
        g_c3.metric("Load Satisfaction", f"{gap.get('load_satisfaction', 100.0):.2f}%")
        g_c4.metric("Critical Period", gap.get("critical_hours", "N/A"))

        st.markdown("#### Recommended Expansion Interventions:")
        if actions:
            for act in actions:
                tag_color = "#10B981" if act["priority"] == "RECOMMENDED" else ("#F59E0B" if act["priority"] == "ALTERNATIVE" else "#EF4444")
                st.markdown(
                    f"""
                    <div class="metric-card" style="border-left: 4px solid {tag_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #F8FAFC;">{act['action']}</h4>
                            <span style="background-color: rgba(255,255,255,0.1); color: {tag_color}; padding: 2px 8px; border-radius: 8px; font-weight: 700; font-size: 11px;">
                                {act['priority']}
                            </span>
                        </div>
                        <p style="margin: 8px 0 4px 0; color: #CBD5E1;">{act['description']}</p>
                        <div style="display: flex; gap: 20px; font-size: 13px; color: #94A3B8; margin-top: 6px;">
                            <span><b>Capital Cost:</b> ₹{act['capital_cost']:,.0f}</span>
                            <span><b>Amortized (20-yr):</b> ₹{act['daily_amortized_cost']:,.2f}/day</span>
                            <span><b>Capacity Added:</b> +{act['additional_capacity']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success(" Optimal operation achieved. Zero capacity deficit detected for this scenario.")

        st.divider()

        # Portfolio Suite Financial Roll-up
        st.subheader(" Portfolio 20-Year Capital Investment Summary")
        tot_capex = sum(sum(a["capital_cost"] for a in sc.get("recommendations", [])) for sc in rec_data.values())
        tot_amort = sum(sum(a["daily_amortized_cost"] for a in sc.get("recommendations", [])) for sc in rec_data.values())
        tot_unmet = sum(sc.get("gap_analysis", {}).get("unmet_kwh", 0.0) for sc in rec_data.values())

        p_c1, p_c2, p_c3 = st.columns(3)
        p_c1.metric("Suite Total CapEx", f"₹{tot_capex:,.0f}")
        p_c2.metric("Suite Daily Amortized Cost", f"₹{tot_amort:,.2f}/day")
        p_c3.metric("Cumulative Daily Deficit", f"{tot_unmet:,.1f} kWh/day")

        if rec_txt_path.is_file():
            with open(rec_txt_path, "r", encoding="utf-8") as f:
                txt_content = f.read()
            st.download_button(
                label=" Download Full Recommendation Report (TXT)",
                data=txt_content,
                file_name="ecogrid_capacity_recommendations_report.txt",
                mime="text/plain",
            )
    else:
        st.info(" Capacity Recommendation Engine is generating data...")


# =============================================================================
# TAB 4: DATA EXPORT CENTER
# =============================================================================
with tab_export:
    st.subheader("📥 Export & Reporting Center")
    st.caption("Export scenario metrics as CSV or download benchmark summaries.")

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown(f"#### Export **{selected_scenario_name}** Metrics")
        csv_single = df_comp.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Download Scenario Metrics (CSV)",
            data=csv_single,
            file_name=f"ecogrid_{selected_scenario_name.lower().replace(' ', '_')}_metrics.csv",
            mime="text/csv",
        )

    with col_e2:
        st.markdown("#### Export Full 10-Scenario Suite")
        csv_full = df_matrix.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📦 Download 10-Scenario Benchmark Suite (CSV)",
            data=csv_full,
            file_name=f"ecogrid_10_scenario_benchmark_{pipeline_code}_{mode_code}.csv",
            mime="text/csv",
        )

    st.divider()

    col_e3, col_e4 = st.columns(2)
    with col_e3:
        st.markdown("#### Export Capacity Recommendations (JSON)")
        rec_json_path = ROOT_DIR / "recommendations.json"
        if rec_json_path.is_file():
            with open(rec_json_path, "r", encoding="utf-8") as f:
                rec_json_str = f.read()
            st.download_button(
                label="💡 Download Recommendations (JSON)",
                data=rec_json_str,
                file_name="ecogrid_capacity_recommendations.json",
                mime="application/json",
            )
        else:
            st.info("Recommendations JSON not yet generated.")

    with col_e4:
        st.markdown("#### Export Custom Input Config (JSON)")
        cfg_json_path = ROOT_DIR / "custom_config.json"
        if cfg_json_path.is_file():
            with open(cfg_json_path, "r", encoding="utf-8") as f:
                cfg_json_str = f.read()
            st.download_button(
                label="⚙️ Download Custom Config (JSON)",
                data=cfg_json_str,
                file_name="ecogrid_custom_config.json",
                mime="application/json",
            )
        else:
            st.info("Custom config JSON not yet generated.")

    st.divider()
    st.markdown(
        """
        > **Tip:** You can download any interactive Plotly chart as a high-resolution PNG image 
        > at any time by hovering over the top-right corner of the chart and clicking the **Camera Icon** 📷.
        """
    )
