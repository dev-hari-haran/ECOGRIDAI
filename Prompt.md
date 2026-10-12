# EcoGridAI — Agent Architectural Rules

## Project Structure
- Resource_optimizer/ (Root)   ← Consolidated Real 33-Bus Microgrid Data Pipeline (Data1.csv & Data2.csv)
- _synthetic_archive/          ← Archived legacy synthetic prototype files


## Coding Rules
- Python 3.10+
- Type hints on all functions
- Docstrings on all functions
- No hardcoded paths — use pathlib.Path
- Config values in CONFIG dict at top of each file
- Random seeds: ABC=42, PSO=43 always

## Never Modify These Files
- Resource_optimizer/abc_optimization.py
- Resource_optimizer/pso_optimization.py
- Resource_optimizer/battery_soc.py
- Resource_optimizer/constraints.py
- Resource_optimizer/planning_vector.py
- Resource_optimizer/dispatch_simulation.py
- Resource_optimizer/objective_function.py

## Data Files
- Data1.csv → actual hourly kW measurements
- Data2.csv → normalized per-unit profiles (0.0 to 1.0)
- Bus ratings: PV@Bus13=851.5kW, PV@Bus30=1157.6kW, Wind@Bus6=2097.97kW
- Peak load: 3715.0 kW at hour 19

## Current Results Location
- results_real.json         → real pipeline 10-scenario baseline results
- results_real_entropy.json → real pipeline 10-scenario entropy results
- results.json              → consolidated mirror of results_real.json

## Task Execution Rules
- Complete ONE checklist item fully before moving to next
- Append to progress.txt after EACH completed step
- Never skip validation steps
- Run python file after creating it to verify no errors
- If a file already exists, read it first before modifying

## Architecture Decisions (Final)
- Fitness function accepts weights as parameter (not hardcoded)
- ABC and PSO receive different entropy-computed weights
- Dashboard reads from results_real.json and results_real_entropy.json
- Recommendation engine reads from results_real_entropy.json
- All outputs saved to Plot_real/ folder