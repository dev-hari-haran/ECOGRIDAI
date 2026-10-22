"""
update_report.py - Updates EcoGridAI_Project_Report.docx with:
1. Technical accuracy corrections (cable loss factors, normalization constants, architecture).
2. Fills in missing descriptions under all headings.
3. Inserts all 10 high-resolution publication-quality PNG figures with captions.
4. Populates List of Figures and List of Tables.
5. Documents the 4-page Full-Stack Web Application (IEEE 33-bus interactive channel, optimization runner, compare & modify with implement & run, weights & fitness function in a box).
"""

import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 1. Create a safe backup
BACKUP_PATH = "EcoGridAI_Project_Report_backup.docx"
TARGET_PATH = "EcoGridAI_Project_Report.docx"
shutil.copyfile(TARGET_PATH, BACKUP_PATH)
print(f"Created backup at {BACKUP_PATH}")

doc = docx.Document(TARGET_PATH)

def insert_paragraph_after(p, text="", style="Normal"):
    new_p = doc.add_paragraph(text, style=style)
    p._p.addnext(new_p._p)
    return new_p

def insert_figure_after(p, image_path, caption_text, width_inches=5.8):
    if not os.path.exists(image_path):
        print(f"WARNING: Image not found: {image_path}")
        return p
    
    # Image paragraph
    img_p = doc.add_paragraph()
    p._p.addnext(img_p._p)
    img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_run = img_p.add_run()
    img_run.add_picture(image_path, width=Inches(width_inches))
    
    # Caption paragraph
    cap_p = doc.add_paragraph()
    img_p._p.addnext(cap_p._p)
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap_p.add_run(caption_text)
    cap_run.font.name = "Calibri"
    cap_run.font.size = Pt(9.5)
    cap_run.font.bold = True
    cap_run.font.italic = True
    cap_run.font.color.rgb = RGBColor(51, 65, 85) # slate-700
    
    # Spacing after caption
    cap_p.paragraph_format.space_after = Pt(12)
    cap_p.paragraph_format.space_before = Pt(4)
    
    return cap_p

# ----------------------------------------------------------------------
# Pass 1: Text Corrections
# ----------------------------------------------------------------------
for p in doc.paragraphs:
    # Correction 1: Bus 6 cable loss factor error in Section 2.2
    if "Bus 6 Wind has highest cable loss due to distance" in p.text:
        p.text = (
            "• Cable Loss Factor: Computed using the shortest-path distance (number of hops) from Bus 1 using BFS, "
            "calculated as loss_factor = min(1.15, 1.00 + 0.01 × distance). The generator cable loss factors are: "
            "Bus 1 (Substation): 1.00 (0% cable loss, 0 hops); Bus 6 (Wind): 1.05 (5% cable loss, 5 hops); "
            "Bus 30 (PV 2): 1.10 (10% cable loss, 10 hops); and Bus 13 (PV 1): 1.12 (12% cable loss, 12 hops). "
            "Bus 13 exhibits the highest distance loss factor among generation buses due to its electrical distance along the main feeder."
        )
        print("Corrected Bus 6 / Bus 13 loss factor statement in Section 2.2.")

    # Correction 2: Normalization constants in Section 3.2
    if "Normalization constants: Capital = ₹150,000/day" in p.text:
        p.text = (
            "Normalization constants from objective_function.py are defined to bring all conflicting objectives to a "
            "comparable non-dimensional scale: Capital Expenditure (N_cap) = ₹80,000/day; Operational Cost (N_op) = ₹400,000/day; "
            "Cable Transmission Loss (N_loss) = 5,000 kWh/day; Unmet Load Deficit (N_unmet) = 10,000 kWh/day; and "
            "Renewable Curtailment (N_curtail) = 10,000 kWh/day. Additionally, a generation oversizing penalty is enforced "
            "whenever total daily renewable generation exceeds 120% of total daily load demand "
            "(oversize_ratio = max(0, total_gen / total_load - 1.2), oversize_penalty = oversize_ratio × 0.5) to discourage "
            "financially irresponsible asset overbuilding."
        )
        print("Corrected normalization constants and added oversizing penalty in Section 3.2.")

# ----------------------------------------------------------------------
# Pass 2: Populate List of Figures & List of Tables
# ----------------------------------------------------------------------
list_of_figures_entries = [
    "Figure 1: IEEE 33-Bus Radial Distribution Network Topology & Generator Bus Mapping",
    "Figure 2: 24-Hour Real Microgrid Energy Dispatch Profile under Measured Diurnal Load Demand (Normal Operation)",
    "Figure 3: Bus-Wise Renewable Generation Contribution across 24 Hours (Bus 13 PV 1, Bus 30 PV 2, Bus 6 Wind)",
    "Figure 4: 33-Bus Transmission Cable Losses across 24 Hours for Distributed Generation Buses",
    "Figure 5: Real Measured Diurnal Load Demand (Data1.csv) vs. Synthetic Benchmark Profile Comparison",
    "Figure 6: Metaheuristic Optimization Convergence History Curves (ABC vs. PSO) with 95% Iteration Threshold Markers",
    "Figure 7: 24-Hour Battery Energy Storage System (BESS) SOC Trajectory Curve within Safe Operating Boundaries [20%, 95%]",
    "Figure 8: Capital Expenditure (CapEx) vs. Operational Cost (OpEx) Breakdown for ABC and PSO under Normal Operation",
    "Figure 9: 10-Scenario Global Benchmark Suite Daily Total Cost Comparison (ABC vs. PSO across Stress Scenarios)",
    "Figure 10: Post-Implementation 24-Hour Energy Dispatch Profile Achieving 100% Demand Satisfaction and Zero Deficit",
]

list_of_tables_entries = [
    "Table 1: Six Continuous Decision Variables and Operational Search Bounds",
    "Table 2: Shannon Entropy Multi-Objective Weight Distribution vs. Static Weights",
    "Table 3: System Architecture and Source Code Module Structure",
    "Table 4: Ten Microgrid Operational Stress Scenario Parameter Definitions",
    "Table 5: Baseline Pipeline Optimization Benchmark Results across 10 Scenarios",
    "Table 6: Real IEEE 33-Bus Data Pipeline Performance Results across 10 Scenarios",
    "Table 7: Autonomous Capacity Recommendation Engine Interventions and Financials",
    "Table 8: EcoGridAI Full-Stack Web Application and Dashboard Feature Matrix",
]

for p in doc.paragraphs:
    if p.text.strip() == "List of Figures":
        curr_p = p
        for entry in list_of_figures_entries:
            curr_p = insert_paragraph_after(curr_p, f"• {entry}", style="Normal")
        print("Populated List of Figures.")
    
    if p.text.strip() == "List of Tables":
        curr_p = p
        for entry in list_of_tables_entries:
            curr_p = insert_paragraph_after(curr_p, f"• {entry}", style="Normal")
        print("Populated List of Tables.")

# ----------------------------------------------------------------------
# Pass 3: Insert Figures and Contextual Descriptions
# ----------------------------------------------------------------------

# Figure 1: In Section 2.2 after cable loss factor description
for p in doc.paragraphs:
    if "Bus 13 exhibits the highest distance loss factor among generation buses" in p.text:
        insert_figure_after(
            p,
            "Plot_real/plot_real_33_bus_network_diagram.png",
            "Figure 1: IEEE 33-Bus Radial Distribution Network Topology & Generator Bus Mapping (Bus 1 Substation, Bus 6 Wind, Bus 13 PV 1, Bus 30 PV 2)."
        )
        print("Inserted Figure 1 into Section 2.2.")
        break

# Figure 5: In Section 4.2 after Data2.csv description
for p in doc.paragraphs:
    if "Data2.csv contains normalized per-unit profiles" in p.text:
        desc_p = insert_paragraph_after(
            p,
            "Figure 5 compares the measured 24-hour diurnal load curve from Data1.csv against the synthetic reference curve. "
            "The measured real dataset displays pronounced evening residential and commercial peak demand reaching 3,715 kW at hour 19."
        )
        insert_figure_after(
            desc_p,
            "Plot_real/plot_real_real_vs_synthetic_load.png",
            "Figure 5: Real Measured Diurnal Load Demand (Data1.csv) vs. Synthetic Benchmark Profile Comparison."
        )
        print("Inserted Figure 5 into Section 4.2.")
        break

# Fill in 4.1 Module Overview missing text
for p in doc.paragraphs:
    if p.text.strip() == "EcoGridAI consists of two independent pipelines:":
        p.text = (
            "EcoGridAI implements a production-grade modular architecture consolidated at the repository root. "
            "It integrates a Python optimization engine (IEEE 33-bus network topology, real data loader, ABC and PSO swarm algorithms, "
            "Shannon Entropy weight derivation, and autonomous recommendation engine) with a high-performance FastAPI backend (api/app.py) "
            "and a responsive React/Vite web application (web/src). Table 2 summarizes the core module architecture."
        )
        print("Filled in Section 4.1 Module Overview text.")
        break

# Fill in 4.3 Ten Scenario Definitions missing text
for p in doc.paragraphs:
    if p.text.strip() == "4.3 Ten Scenario Definitions":
        insert_paragraph_after(
            p,
            "To evaluate algorithmic resilience under diverse operational stresses, EcoGridAI defines 10 distinct operational scenarios. "
            "These scenarios systematically vary solar irradiance multipliers, wind velocity factors, diurnal load demand scaling, "
            "and utility grid/battery availability flags. Table 3 outlines the full 10-scenario parameter matrix."
        )
        print("Filled in Section 4.3 Scenario Definitions text.")
        break

# Fill in 5.1 Baseline Pipeline Results missing text
for p in doc.paragraphs:
    if p.text.strip() == "5.1 Baseline Pipeline Results (Synthetic Data)":
        insert_paragraph_after(
            p,
            "Table 4 presents the benchmark results for the synthetic reference pipeline. Across all synthetic scenarios, "
            "both ABC and PSO successfully identify feasible dispatch vectors achieving 100% load satisfaction with minimal constraint violations."
        )
        print("Filled in Section 5.1 Baseline Pipeline Results text.")
        break

# Fill in 5.2 Real Data Pipeline Results missing text and insert Figures 2, 3, 4, 7
for p in doc.paragraphs:
    if p.text.strip() == "5.2 Real Data Pipeline Results (IEEE 33-Bus)":
        p_intro = insert_paragraph_after(
            p,
            "The real data pipeline executes optimizations using actual measured data from Data1.csv and Data2.csv on the IEEE 33-bus network. "
            "Table 5 summarizes the performance metrics across all 10 real scenarios under Shannon Entropy multi-objective weighting."
        )
        print("Filled in Section 5.2 Real Data Pipeline Results intro.")
        break

# Insert Figures 2, 3, 4, 7 after Table 5
# Find the paragraph right after Table 5 (which is 5.3 Key Findings)
for p in doc.paragraphs:
    if p.text.strip() == "5.3 Key Findings":
        # Insert descriptions and figures right before 5.3
        p_prev = p._element.getprevious()
        # Create a paragraph before 5.3
        p_fig2_desc = doc.add_paragraph(
            "Figure 2 illustrates the 24-hour energy dispatch profile under normal operating conditions. "
            "Solar PV generation covers daytime load from hours 8 to 16, Wind generation contributes baseline power, "
            "and battery storage discharges during early evening hours. The red dashed line denotes the real measured load curve."
        )
        p._p.addprevious(p_fig2_desc._p)
        
        cap2 = insert_figure_after(
            p_fig2_desc,
            "Plot_real/plot_real_dispatch_profile.png",
            "Figure 2: 24-Hour Real Microgrid Energy Dispatch Profile under Measured Diurnal Load Demand (Normal Operation)."
        )
        
        p_fig3_desc = insert_paragraph_after(
            cap2,
            "Figure 3 details the bus-wise generation contribution across the 24-hour cycle. Generation is tracked at "
            "Bus 13 (PV 1: 851.5 kW), Bus 30 (PV 2: 1,157.6 kW), and Bus 6 (Wind Turbine: 2,097.97 kW)."
        )
        cap3 = insert_figure_after(
            p_fig3_desc,
            "Plot_real/plot_real_bus_generation_contribution.png",
            "Figure 3: Bus-Wise Renewable Generation Contribution across 24 Hours (Bus 13 PV 1, Bus 30 PV 2, Bus 6 Wind)."
        )
        
        p_fig4_desc = insert_paragraph_after(
            cap3,
            "Figure 4 charts the 33-bus transmission cable losses across 24 hours. Cable loss varies proportionately with branch power flow "
            "and electrical distance. Bus 13 exhibits a 12% cable loss factor, Bus 30 has a 10% factor, and Bus 6 incurs a 5% factor."
        )
        cap4 = insert_figure_after(
            p_fig4_desc,
            "Plot_real/plot_real_bus_transmission_losses.png",
            "Figure 4: 33-Bus Transmission Cable Losses across 24 Hours for Distributed Generation Buses."
        )
        
        p_fig7_desc = insert_paragraph_after(
            cap4,
            "Figure 7 displays the 24-hour State of Charge (SOC %) trajectory of the Battery Energy Storage System (BESS). "
            "The battery charges from surplus solar generation during peak midday hours and discharges to support evening peak load, "
            "strictly bounded between the 20% minimum depth-of-discharge and 95% maximum charge limits."
        )
        cap7 = insert_figure_after(
            p_fig7_desc,
            "report_figures/fig7_battery_soc_trajectory.png",
            "Figure 7: 24-Hour Battery Energy Storage System (BESS) SOC Trajectory Curve within Safe Operating Boundaries [20%, 95%]."
        )
        print("Inserted Figures 2, 3, 4, 7 into Section 5.2.")
        break

# Insert Figures 6, 8, 9 into Section 5.3 (Key Findings & Algorithm Comparison)
for p in doc.paragraphs:
    if "Night Peak correctly sets pv_bus13_frac = 0.0" in p.text:
        p_fig6_desc = insert_paragraph_after(
            p,
            "Figure 6 illustrates the convergence history of ABC and PSO over 40 iterations. "
            "PSO rapidly approaches its optimal fitness in 3 to 6 iterations (achieving the 95% optimality threshold by iteration 4), "
            "whereas ABC exhibits steady, exploratory convergence reaching the threshold at iteration 9 to 20."
        )
        cap6 = insert_figure_after(
            p_fig6_desc,
            "report_figures/fig6_convergence_curves.png",
            "Figure 6: Metaheuristic Optimization Convergence History Curves (ABC vs. PSO) with 95% Iteration Threshold Markers."
        )
        
        p_fig8_desc = insert_paragraph_after(
            cap6,
            "Figure 8 compares the 20-year amortized daily Capital Expenditure (CapEx) against the daily Operational Cost (OpEx) for both algorithms. "
            "Both algorithms arrive at nearly identical economic balances (₹57,512/day CapEx vs ₹273,499/day OpEx)."
        )
        cap8 = insert_figure_after(
            p_fig8_desc,
            "report_figures/fig8_cost_breakdown.png",
            "Figure 8: Capital Expenditure (CapEx) vs. Operational Cost (OpEx) Breakdown for ABC and PSO under Normal Operation."
        )
        
        p_fig9_desc = insert_paragraph_after(
            cap8,
            "Figure 9 benchmarks ABC and PSO daily total costs across all 10 operational stress scenarios. "
            "The comparison highlights consistent algorithmic parity across stress conditions while identifying Extreme Stress and Low Renewable "
            "as high-cost regimes requiring grid purchases."
        )
        cap9 = insert_figure_after(
            p_fig9_desc,
            "report_figures/fig9_global_benchmark_suite.png",
            "Figure 9: 10-Scenario Global Benchmark Suite Daily Total Cost Comparison (ABC vs. PSO across Stress Scenarios)."
        )
        print("Inserted Figures 6, 8, 9 into Section 5.3.")
        break

# Insert Figure 10 and descriptions in Section 5.4 Capacity Recommendation Engine
for p in doc.paragraphs:
    if "Based on real pipeline analysis, the recommendation engine identifies and ranks capacity interventions:" in p.text:
        p.text = (
            "The Capacity Recommendation Engine analyzes the unmet energy deficit, peak capacity deficit, and scenario severity "
            "to automatically synthesize ranked expansion interventions. Each recommendation specifies candidate bus placement, "
            "additional capacity sizing (kW / kWh), estimated 20-year capital expenditure (CapEx), daily amortized cost, and cost-effectiveness index (Phi). "
            "Table 6 summarizes the prioritized expansion portfolio."
        )
        print("Updated Section 5.4 Recommendation Engine text.")
        break

# Insert Figure 10 after Table 6 (before Chapter 6)
for p in doc.paragraphs:
    if p.text.strip() == "Chapter 6: Dashboard & Visualization":
        p_rec_eval = doc.add_paragraph(
            "Through the Web Application's 'Implement & run' capability, users can immediately apply a recommended capacity expansion "
            "(such as adding a Supplementary PV Farm on low-loss Candidate Bus 18 or expanding BESS storage). "
            "Figure 10 depicts the post-implementation 24-hour dispatch profile, demonstrating that the commissioned assets "
            "completely eliminate the evening deficit, achieving 100.0% total demand satisfaction across all 24 hours."
        )
        p._p.addprevious(p_rec_eval._p)
        
        insert_figure_after(
            p_rec_eval,
            "report_figures/fig10_post_implementation_dispatch.png",
            "Figure 10: Post-Implementation 24-Hour Energy Dispatch Profile Achieving 100% Demand Satisfaction and Zero Deficit."
        )
        print("Inserted Figure 10 into Section 5.4.")
        break

# Update Chapter 6: Dashboard & Visualization
for p in doc.paragraphs:
    if "The EcoGridAI dashboard is built using Web and Plotly." in p.text:
        p.text = (
            "EcoGridAI provides a dual-interface visualization suite comprising a production React/Vite Full-Stack Web Application "
            "and an interactive Plotly/Streamlit data dashboard. The modern Web Application (built with React 19, TypeScript, Tailwind CSS, "
            "and a FastAPI Python backend) is organized into four dedicated operational pages:"
        )
        p1 = insert_paragraph_after(
            p,
            "• Page 1 — System Overview: Interactive IEEE 33-bus radial network diagram with smooth bus channel interaction, "
            "animated electricity flow pulses along active lines, live impedance display (R, X), bus and branch add/delete toolbar, "
            "and cable loss factor inspection."
        )
        p2 = insert_paragraph_after(
            p1,
            "• Page 2 — Data & Optimization: Live scenario configuration (10 operating scenarios), measured dataset selector (Data1.csv, Data2.csv), "
            "custom CSV load profile validator with client/server schema checks, and system asset sizing sliders."
        )
        p3 = insert_paragraph_after(
            p2,
            "• Page 3 — Compare & Modify: Side-by-side ABC vs PSO head-to-head performance benchmark, 24-hour stacked dispatch area chart, "
            "convergence history curves, battery SOC trajectory, capital vs operational cost breakdown, bus-wise generation contribution, "
            "33-bus transmission cable loss curves, 10-scenario global benchmark suite, and Autonomous Capacity Expansion with one-click 'Implement & run' "
            "and instant post-implementation comparison graphs."
        )
        p4 = insert_paragraph_after(
            p3,
            "• Page 4 — Weights & Fitness Simulation: Interactive real-time Shannon Entropy step-by-step derivation simulator across all 10 scenarios "
            "(P_ij → E_j → d_j → W_j) and the interactive 'Fitness Function in a Box' mathematical formula simulator with live sliders for CapEx, OpEx, "
            "losses, deficit, and curtailment, providing instant scalar fitness evaluation."
        )
        print("Updated Chapter 6 Dashboard & Visualization text.")
        break

# Save updated document
doc.save(TARGET_PATH)
print(f"Successfully updated and saved {TARGET_PATH}!")
