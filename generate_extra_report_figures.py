import os
import json
import numpy as np
import matplotlib.pyplot as plt

os.makedirs('report_figures', exist_ok=True)

plt.rcParams.update({
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#CBD5E1',
    'axes.labelcolor': '#1E293B',
    'xtick.color': '#334155',
    'ytick.color': '#334155',
    'grid.color': '#E2E8F0',
    'grid.linestyle': '--',
    'grid.alpha': 0.7,
    'text.color': '#0F172A',
    'legend.facecolor': '#FFFFFF',
    'legend.edgecolor': '#CBD5E1',
    'font.sans-serif': ['Times New Roman', 'DejaVu Sans', 'Arial'],
})

# Fig 11: Shannon Entropy Objective Weights
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
objs = ['Capital Cost\n(w1)', 'OpEx Cost\n(w2)', 'Cable Losses\n(w3)', 'Unmet Load\n(w4)', 'Curtailment\n(w5)']
abc_w = [0.038, 0.054, 0.073, 0.473, 0.362]
pso_w = [0.035, 0.051, 0.071, 0.481, 0.362]
x = np.arange(len(objs))
w = 0.35
r1 = ax.bar(x - w/2, [v*100 for v in abc_w], width=w, label='ABC Entropy Weights (%)', color='#16A34A', edgecolor='#0F172A')
r2 = ax.bar(x + w/2, [v*100 for v in pso_w], width=w, label='PSO Entropy Weights (%)', color='#0288D1', edgecolor='#0F172A')
ax.set_title('Shannon Information Entropy Dynamic Objective Weights Distribution', fontsize=13, fontweight='bold', pad=12)
ax.set_ylabel('Objective Weight Allocation (%)', fontsize=11, fontweight='semibold')
ax.set_xticks(x)
ax.set_xticklabels(objs, fontsize=9.5, fontweight='semibold')
ax.set_ylim(0, 56)
ax.grid(True, axis='y')
ax.legend(loc='upper right')
for r in r1:
    h = r.get_height()
    ax.annotate(f'{h:.1f}%', (r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=8.5, fontweight='bold')
for r in r2:
    h = r.get_height()
    ax.annotate(f'{h:.1f}%', (r.get_x() + r.get_width()/2, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=8.5, fontweight='bold')
plt.tight_layout()
fig.savefig('report_figures/fig11_shannon_entropy_weights.png', dpi=300)
plt.close(fig)

# Fig 12: Load Duration Curve
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
with open('Data1.csv', 'r') as f:
    raw_lines = [l.strip().split(',') for l in f.readlines()]
    lines = [r for r in raw_lines if len(r) > 1 and r[0].strip().isdigit()][:24]
hourly_loads = np.array([float(row[1]) for row in lines])
sorted_loads = np.sort(hourly_loads)[::-1]
h_range = np.arange(1, 25)
ax.plot(h_range, sorted_loads, color='#DC2626', linewidth=2.8, marker='o', label='Measured Load Duration Curve (LDC)')
ax.fill_between(h_range, sorted_loads, color='#DC2626', alpha=0.12, label='Daily Energy Requirement (68,500 kWh)')
ax.axhline(y=3715.0, color='#0F172A', linestyle='--', label='Peak Demand Shortfall Level (3,715 kW @ Hour 19)')
ax.axhline(y=1938.0, color='#64748B', linestyle=':', label='Baseload Minimum (1,938 kW)')
ax.set_title('24-Hour Load Duration Curve (IEEE 33-Bus System)', fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel('Cumulative Duration Hours (Ranked by Demand)', fontsize=11)
ax.set_ylabel('Active Load Power (kW)', fontsize=11)
ax.set_xticks(h_range)
ax.grid(True)
ax.legend(loc='upper right')
plt.tight_layout()
fig.savefig('report_figures/fig12_load_duration_curve.png', dpi=300)
plt.close(fig)

# Fig 13: Cable Loss Multiplier vs Distance Hops
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
buses = np.arange(1, 34)
hops = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 
                 2, 3, 4, 5, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
loss_factors = np.minimum(1.15, 1.0 + 0.01 * hops)
ax.stem(buses, (loss_factors - 1.0)*100, linefmt='b-', markerfmt='bo', basefmt='r-')
ax.scatter([1, 6, 13, 30], [(loss_factors[i-1]-1.0)*100 for i in [1, 6, 13, 30]], color='#F59E0B', s=160, zorder=5, label='Generator Buses (1, 6, 13, 30)')
ax.set_title('IEEE 33-Bus Cable Transmission Distance Loss Multiplier (BFS Hop Metric)', fontsize=13, fontweight='bold', pad=12)
ax.set_xlabel('Bus Index Number (1 to 33)', fontsize=11)
ax.set_ylabel('Transmission Loss Penalty (% above baseline)', fontsize=11)
ax.set_xticks(np.arange(1, 34, 2))
ax.grid(True)
ax.legend(loc='upper left')
plt.tight_layout()
fig.savefig('report_figures/fig13_loss_vs_distance_hops.png', dpi=300)
plt.close(fig)

# Fig 14: Cost-Effectiveness Index
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
actions = ['Substation Upgrade\n(Grid Expansion)', 'Modular BESS\n(LFP Storage)', 'Solar PV Farm\n(Bus 18 Expansion)']
phi = [5000.0, 48484.9, 50000.0]
colors = ['#16A34A', '#F59E0B', '#F97316']
r = ax.bar(actions, phi, width=0.45, color=colors, edgecolor='#0F172A', alpha=0.9)
ax.axhline(y=50000, color='#DC2626', linestyle='--', label='Economic Threshold (Phi = ₹50,000/kW)')
ax.set_title('Autonomous Capacity Recommendation Cost-Effectiveness Index (Phi = CapEx / kW Served)', fontsize=13, fontweight='bold', pad=12)
ax.set_ylabel('Index Value Phi (₹ / kW Served)', fontsize=11)
ax.set_ylim(0, 60000)
ax.grid(True, axis='y')
ax.legend(loc='upper left')
for rect in r:
    h = rect.get_height()
    ax.annotate(f'₹{h:,.0f} / kW', (rect.get_x() + rect.get_width()/2, h), xytext=(0, 3), textcoords='offset points', ha='center', fontsize=9, fontweight='bold')
plt.tight_layout()
fig.savefig('report_figures/fig14_recommendation_cost_effectiveness.png', dpi=300)
plt.close(fig)

# Fig 15: 10-Scenario Load Satisfaction
fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
with open('results_real_entropy.json', 'r') as f:
    sc_data = json.load(f)
sc_names = [sc['scenario_name'].replace(' Surplus', '') for sc in sc_data]
abc_sat = [sc['abc']['load_satisfaction'] for sc in sc_data]
pso_sat = [sc['pso']['load_satisfaction'] for sc in sc_data]
x = np.arange(len(sc_names))
w = 0.38
ax.bar(x - w/2, abc_sat, width=w, label='ABC Load Satisfaction (%)', color='#16A34A', alpha=0.88, edgecolor='#0F172A')
ax.bar(x + w/2, pso_sat, width=w, label='PSO Load Satisfaction (%)', color='#0288D1', alpha=0.88, edgecolor='#0F172A')
ax.set_title('10-Scenario Benchmark: Demand Satisfaction Rate Comparison (ABC vs. PSO)', fontsize=13, fontweight='bold', pad=12)
ax.set_ylabel('Load Satisfaction Rate (%)', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(sc_names, rotation=35, ha='right', fontsize=9, fontweight='semibold')
ax.set_ylim(0, 115)
ax.axhline(y=100, color='#16A34A', linestyle=':', label='100% Demand Satisfaction Target')
ax.grid(True, axis='y')
ax.legend(loc='upper right')
plt.tight_layout()
fig.savefig('report_figures/fig15_scenario_load_satisfaction.png', dpi=300)
plt.close(fig)

print('Generated all 5 extra report figures successfully.')
