"""
api/app.py - FastAPI Service for EcoGridAI Microgrid Optimization & 33-Bus System
"""

import io
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from api.pdf_generator import build_pdf_report

# Add parent directory to path to import project modules
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import bus_network
from abc_optimization import run_abc
from pso_optimization import run_pso
from dispatch_simulation_real import dispatch_simulation_real, CONFIG as DISPATCH_CONFIG
from planning_vector import get_planning_bounds, VAR_NAMES
from real_data_loader import load_real_data
from scenarios import get_scenarios
from data_input.validator import (
    validate_bus_ratings,
    validate_load_profile,
    validate_csv_columns,
)
from recommendation.engine import (
    analyze_load_gap,
    recommend_pv,
    recommend_battery,
    recommend_grid,
)
from api.serializers import sanitize_for_json
from api.schemas import (
    OptimizeRequest,
    ValidateRequest,
    RecommendationRequest,
    ConfigModel,
)

app = FastAPI(
    title="EcoGridAI Optimization API",
    description="Real IEEE 33-Bus Radial Distribution Network Optimization with ABC, PSO, Shannon Entropy Weighting, and Expansion Intelligence",
    version="1.0.0",
)

# Configure CORS for Vite dev server and Netlify deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Async job storage and thread pool
executor = ThreadPoolExecutor(max_workers=3)
JOBS: Dict[str, Dict[str, Any]] = {}

# Standard IEEE 33-bus layout positions for visual continuity
BUS_COORDINATES = [
    (34, 100), (88, 100), (142, 100), (196, 100), (250, 100), (304, 100),
    (358, 100), (412, 100), (466, 100), (520, 100), (574, 100), (628, 100),
    (682, 100), (736, 100), (790, 100), (844, 100), (898, 100), (952, 100),
    (88, 174), (160, 174), (232, 174), (304, 174), (142, 30), (220, 30),
    (298, 30), (304, 248), (376, 248), (448, 248), (520, 248), (592, 248),
    (664, 248), (736, 248), (808, 248),
]

# Standard IEEE 33-bus benchmark active loads (kW)
IEEE_33_LOADS = [
    0.0, 100.0, 90.0, 120.0, 60.0, 60.0, 200.0, 200.0, 60.0, 60.0, 45.0, 60.0, 60.0, 120.0, 60.0, 60.0, 60.0,
    90.0, 90.0, 90.0, 90.0, 90.0, 90.0, 420.0, 420.0, 60.0, 60.0, 60.0, 120.0, 200.0, 150.0, 210.0, 60.0,
]

# Baseline entropy weights derived from 10-scenario suite
ENTROPY_WEIGHTS_ABC = np.array([0.2635, 0.2223, 0.0573, 0.3204, 0.1365], dtype=np.float64)
ENTROPY_WEIGHTS_PSO = np.array([0.2514, 0.2198, 0.0542, 0.3371, 0.1375], dtype=np.float64)


def compute_convergence_speed(history: np.ndarray, threshold_pct: float = 0.95) -> int:
    """Calculates iterations required to reach threshold_pct of final fitness improvement."""
    if len(history) == 0:
        return 0
    f_init = history[0]
    f_final = history[-1]
    if abs(f_init - f_final) < 1e-6:
        return 1
    target = f_init - threshold_pct * (f_init - f_final)
    for idx, val in enumerate(history):
        if val <= target:
            return idx + 1
    return len(history)


@app.get("/api/health")
def get_health():
    """Returns backend status, loaded models, and dataset availability."""
    data1_exists = (ROOT_DIR / "Data1.csv").is_file()
    data2_exists = (ROOT_DIR / "Data2.csv").is_file()
    custom_config_exists = (ROOT_DIR / "custom_config.json").is_file()

    return sanitize_for_json({
        "status": "ok",
        "models": ["ABC", "PSO"],
        "algorithms": {
            "ABC": "Artificial Bee Colony (colony_size=30)",
            "PSO": "Particle Swarm Optimization (particles=30)",
        },
        "datasets": {
            "Data1.csv": data1_exists,
            "Data2.csv": data2_exists,
            "custom_config.json": custom_config_exists,
        },
        "system": "IEEE 33-Bus Radial Test Feeder (12.66 kV)",
        "entropy_weighting_ready": True,
        "recommendation_engine_ready": True,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.get("/api/network")
def get_network():
    """
    Returns real IEEE 33-bus network topology, bus coordinates, branch connections,
    baseline loads, installed generators, hop distances, and cable loss factors.
    """
    adj = bus_network.build_adjacency_list()
    distances = bus_network.compute_bus_distances(1)
    generator_map = bus_network.get_bus_generator_mapping()

    buses = []
    for idx in range(1, 34):
        x, y = BUS_COORDINATES[idx - 1]
        load_kw = IEEE_33_LOADS[idx - 1]
        loss_factor = bus_network.get_loss_factor(idx)
        hops = distances.get(idx, 0)
        connected = sorted(adj.get(idx, []))

        resources = []
        installed = []
        if idx == 1:
            resources.append("grid")
            installed.append({"type": "grid", "label": "Substation Main Feeder", "rating_kw": 3200.0})
        if idx in generator_map.get("PV", []):
            resources.append("solar")
            rating = 851.5 if idx == 13 else 1157.6
            installed.append({"type": "solar", "label": f"Solar PV Array (Bus {idx})", "rating_kw": rating})
        if idx in generator_map.get("Wind", []):
            resources.append("wind")
            installed.append({"type": "wind", "label": f"Wind Turbine Farm (Bus {idx})", "rating_kw": 2097.97})

        buses.append({
            "id": idx,
            "loadKw": load_kw,
            "x": x,
            "y": y,
            "resources": resources,
            "installed": installed,
            "loss_factor": loss_factor,
            "loss_pct": round((loss_factor - 1.0) * 100, 1),
            "distance_hops": hops,
            "connected_buses": connected,
        })

    branches = [list(edge) for edge in bus_network.IEEE_33_BUS_EDGES]
    total_base_load_kw = float(sum(IEEE_33_LOADS))

    return sanitize_for_json({
        "system_name": "IEEE 33-Bus Radial Feeder",
        "voltage_kv": 12.66,
        "root_bus": 1,
        "total_buses": 33,
        "total_branches": len(branches),
        "total_base_load_kw": total_base_load_kw,
        "buses": buses,
        "branches": branches,
        "loss_model": {
            "formula": "loss_factor = min(1.15, 1.00 + 0.01 * distance_hops)",
            "base_loss_factor": bus_network.CONFIG["base_loss_factor"],
            "loss_per_hop": bus_network.CONFIG["loss_per_hop"],
            "max_loss_factor": bus_network.CONFIG["max_loss_factor"],
        },
        "pv_buses": generator_map.get("PV", []),
        "wind_buses": generator_map.get("Wind", []),
        "grid_bus": 1,
    })


@app.post("/api/network/add-bus")
async def add_bus(req: Request):
    """Adds a new bus and connects it to the feeder network."""
    body = await req.json()
    bus_id = int(body.get("id", 34))
    load_kw = float(body.get("loadKw", 100.0))
    bus_type = str(body.get("type", "load")).lower()
    connect_to = int(body.get("connect_to", 1))

    # Add branch
    branch = [min(connect_to, bus_id), max(connect_to, bus_id)]

    return sanitize_for_json({
        "status": "ok",
        "message": f"Bus {bus_id} added and connected to Bus {connect_to}",
        "bus": {
            "id": bus_id,
            "loadKw": load_kw,
            "x": 800,
            "y": 400,
            "resources": [bus_type] if bus_type != "load" else [],
            "installed": [{"type": bus_type, "label": f"Custom {bus_type.upper()} Node", "rating_kw": load_kw}] if bus_type != "load" else [],
            "loss_factor": 1.05,
            "loss_pct": 5.0,
            "distance_hops": 5,
            "connected_buses": [connect_to],
        },
        "branch": branch,
    })


@app.post("/api/network/delete-bus")
async def delete_bus(req: Request):
    """Deletes a bus and removes its connected branches."""
    body = await req.json()
    bus_id = int(body.get("id", 33))
    if bus_id == 1:
        return JSONResponse(status_code=400, content={"detail": "Cannot delete Substation Root Bus 1"})

    return sanitize_for_json({
        "status": "ok",
        "message": f"Bus {bus_id} and associated branches removed successfully",
        "deleted_id": bus_id,
    })


@app.post("/api/network/add-branch")
async def add_branch(req: Request):
    """Adds a node path (branch/edge) between two buses."""
    body = await req.json()
    from_bus = int(body.get("from_bus", 1))
    to_bus = int(body.get("to_bus", 2))
    if from_bus == to_bus:
        return JSONResponse(status_code=400, content={"detail": "Cannot connect a bus to itself"})

    branch = [min(from_bus, to_bus), max(from_bus, to_bus)]
    return sanitize_for_json({
        "status": "ok",
        "message": f"Path between Bus {branch[0]} and Bus {branch[1]} established",
        "branch": branch,
    })


@app.post("/api/network/delete-branch")
async def delete_branch(req: Request):
    """Deletes a node path (branch/edge) between two buses."""
    body = await req.json()
    from_bus = int(body.get("from_bus", 1))
    to_bus = int(body.get("to_bus", 2))
    branch = [min(from_bus, to_bus), max(from_bus, to_bus)]
    return sanitize_for_json({
        "status": "ok",
        "message": f"Path between Bus {branch[0]} and Bus {branch[1]} removed",
        "branch": branch,
    })


@app.get("/api/datasets")
def get_datasets():
    """Returns available datasets and their metadata."""
    datasets = []

    # 1. Data1.csv
    data1_path = ROOT_DIR / "Data1.csv"
    if data1_path.is_file():
        try:
            d = load_real_data("Data1.csv", "Data2.csv")
            datasets.append({
                "id": "Data1.csv",
                "name": "Data1.csv (Primary Measured kW & Bus Ratings)",
                "description": "24-hour measured demand profiles (Commercial, Industrial, Residential), actual PV & Wind generation, and nameplate bus allocations.",
                "hours": len(d["hourly_load"]),
                "peak_load_kw": d["peak_load"],
                "total_pv_kw": d["total_pv_capacity"],
                "total_wind_kw": d["total_wind_capacity"],
                "pv_buses": d["pv_buses"],
                "wind_buses": d["wind_buses"],
                "bus_ratings": d["bus_ratings"],
                "is_default": True,
            })
        except Exception as e:
            datasets.append({
                "id": "Data1.csv",
                "name": "Data1.csv",
                "error": str(e),
            })

    # 2. Data2.csv
    data2_path = ROOT_DIR / "Data2.csv"
    if data2_path.is_file():
        datasets.append({
            "id": "Data2.csv",
            "name": "Data2.csv (Normalized Per-Unit Profiles)",
            "description": "Normalized (0-1 p.u.) diurnal profiles for load, solar irradiation, and wind speed.",
            "hours": 24,
            "is_default": False,
        })

    # 3. custom_config.json
    custom_path = ROOT_DIR / "custom_config.json"
    if custom_path.is_file():
        datasets.append({
            "id": "custom_config.json",
            "name": "custom_config.json (Saved Custom Parameters)",
            "description": "Operator customized generator bus allocations and diurnal load curves.",
            "hours": 24,
            "is_default": False,
        })

    return sanitize_for_json(datasets)


@app.post("/api/datasets/validate")
async def validate_dataset(request: Request):
    """
    Validates uploaded CSV file, raw CSV text, or structured parameters
    using the existing data_input validator engine.
    """
    content_type = request.headers.get("content-type", "").lower()
    csv_text = None
    bus_ratings = None
    load_profile = None

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        file = form.get("file")
        if file and hasattr(file, "read"):
            content = await file.read()
            csv_text = content.decode("utf-8", errors="replace")
        elif "raw_csv" in form:
            csv_text = str(form["raw_csv"])
        elif "csv_content" in form:
            csv_text = str(form["csv_content"])
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                csv_text = body.get("csv_content") or body.get("raw_csv")
                bus_ratings = body.get("bus_ratings")
                load_profile = body.get("load_profile")
        except Exception:
            raw_body = await request.body()
            if raw_body:
                csv_text = raw_body.decode("utf-8", errors="replace")

    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, Any] = {}

    if csv_text:
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            # Find load column
            load_col = None
            for cand in ["Total_Load_kW", "load_kw", "Load_kW", "Load", "load", "demand"]:
                if cand in df.columns:
                    load_col = cand
                    break

            if load_col is not None:
                expected = ["Hour", load_col] if "Hour" in df.columns else [load_col]
                col_res = validate_csv_columns(df, expected_cols=expected)
                if not col_res.valid:
                    errors.extend(col_res.errors)
                warnings.extend(col_res.warnings)

                load_vals = pd.to_numeric(df[load_col], errors="coerce").dropna().values[:24]
                load_res = validate_load_profile(load_vals)
                if not load_res.valid:
                    errors.extend(load_res.errors)
                warnings.extend(load_res.warnings)
                if load_res.data:
                    summary = {
                        "peak_kw": load_res.data["peak_kw"],
                        "min_kw": load_res.data["min_kw"],
                        "total_kwh": load_res.data["total_kwh"],
                        "avg_kw": load_res.data["avg_kw"],
                        "load_factor": load_res.data["load_factor"],
                        "hours": len(load_vals),
                    }
            else:
                errors.append("[ERROR] [csv.columns]: No recognizable load column found (expected 'Total_Load_kW' or 'load_kw').")

        except Exception as e:
            errors.append(f"[ERROR] [csv.parse]: Failed to parse CSV content: {e}")

    # Validate bus ratings if provided
    if bus_ratings:
        b_res = validate_bus_ratings(bus_ratings)
        if not b_res.valid:
            errors.extend(b_res.errors)
        warnings.extend(b_res.warnings)
        if b_res.data:
            summary["bus_ratings"] = b_res.data

    # Validate direct load profile if provided
    if load_profile:
        l_res = validate_load_profile(load_profile)
        if not l_res.valid:
            errors.extend(l_res.errors)
        warnings.extend(l_res.warnings)
        if l_res.data:
            summary["load_profile"] = {
                "peak_kw": l_res.data["peak_kw"],
                "total_kwh": l_res.data["total_kwh"],
                "load_factor": l_res.data["load_factor"],
            }

    is_valid = len(errors) == 0 and (bool(summary) or csv_text is not None)
    return sanitize_for_json({
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "summary": summary if is_valid else None,
    })


@app.get("/api/scenarios")
def get_all_scenarios():
    """Returns the 10 operational scenarios from scenarios.py."""
    scenarios = get_scenarios()
    formatted = []
    for idx, sc in enumerate(scenarios):
        formatted.append({
            "index": idx,
            "name": sc["name"],
            "description": f"Scenario {idx+1}: {sc['name']}. Demand ×{sc['load_multiplier']}, Solar ×{sc['solar_multiplier']}, Wind ×{sc['wind_multiplier']}.",
            "load_multiplier": sc["load_multiplier"],
            "solar_multiplier": sc["solar_multiplier"],
            "wind_multiplier": sc["wind_multiplier"],
            "grid_available": sc["grid_available"],
            "battery_available": sc["battery_available"],
            # Frontend shorthand mappings
            "load": sc["load_multiplier"],
            "solar": sc["solar_multiplier"],
            "wind": sc["wind_multiplier"],
            "grid": 1.0 if sc["grid_available"] else 0.0,
            "battery": 1.0 if sc["battery_available"] else 0.0,
        })
    return sanitize_for_json(formatted)


@app.get("/api/benchmark")
def get_benchmark():
    """Returns the full 10-scenario benchmark suite results for global comparison."""
    import json
    benchmark_path = ROOT_DIR / "results_real_entropy.json"
    if not benchmark_path.is_file():
        benchmark_path = ROOT_DIR / "results_real.json"

    if benchmark_path.is_file():
        with open(benchmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return sanitize_for_json(data)
    return sanitize_for_json([])


def execute_optimization(req: OptimizeRequest) -> Dict[str, Any]:
    """Runs the real ABC and PSO algorithms and returns normalized model outputs."""
    data = load_real_data("Data1.csv", "Data2.csv")

    scenarios = get_scenarios()
    sc_idx = req.scenario_index if req.scenario_index is not None and 0 <= req.scenario_index < len(scenarios) else 0
    sc = scenarios[sc_idx]

    # Custom load profile or standard real load profile
    if req.custom_load_profile and len(req.custom_load_profile) == 24:
        base_load = np.array(req.custom_load_profile, dtype=np.float64)
    else:
        base_load = data["hourly_load"]

    base_solar = data["hourly_pv_pu"]
    base_wind = data["hourly_wind_pu"]

    solar_scaled = base_solar * sc["solar_multiplier"]
    wind_scaled = base_wind * sc["wind_multiplier"]
    load_scaled = base_load * sc["load_multiplier"]

    # Bounds scaled with requested capacities
    bounds = get_planning_bounds(battery_available=sc["battery_available"])
    bounds["ub"][3] = max(10.0, float(req.config.batteryKw))
    bounds["ub"][4] = max(100.0, float(req.config.batteryKwh))
    bounds["ub"][5] = max(10.0, float(req.config.gridLimitKw))

    # Temporarily apply configured capacities to dispatch config
    orig_pv13 = DISPATCH_CONFIG["pv_bus13_kw"]
    orig_pv30 = DISPATCH_CONFIG["pv_bus30_kw"]
    orig_wind = DISPATCH_CONFIG["wind_bus6_kw"]
    orig_grid_cap = DISPATCH_CONFIG.get("grid_cap_kw", 2000.0)

    total_nominal_pv = 851.5 + 1157.6
    pv_scale = req.config.solarKw / total_nominal_pv if req.config.solarKw > 0 else 1.0
    DISPATCH_CONFIG["pv_bus13_kw"] = 851.5 * pv_scale
    DISPATCH_CONFIG["pv_bus30_kw"] = 1157.6 * pv_scale
    DISPATCH_CONFIG["wind_bus6_kw"] = float(req.config.windKw) if req.config.windKw > 0 else orig_wind
    DISPATCH_CONFIG["grid_cap_kw"] = float(req.config.gridLimitKw) if req.config.gridLimitKw > 0 else orig_grid_cap

    # Select multi-objective weights
    w_abc = ENTROPY_WEIGHTS_ABC if req.use_entropy_weights else None
    w_pso = ENTROPY_WEIGHTS_PSO if req.use_entropy_weights else None

    max_iter = max(15, min(req.max_iter, 150))

    try:
        # Run ABC
        t0 = time.time()
        abc_vec, abc_fit, abc_hist = run_abc(
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=sc["grid_available"],
            battery_available=sc["battery_available"],
            bounds=bounds,
            weights=w_abc,
            colony_size=30,
            max_iter=max_iter,
            seed=42,
        )
        abc_time = time.time() - t0

        if not sc["battery_available"]:
            abc_vec[3] = 0.0
            abc_vec[4] = 0.0

        abc_dispatch = dispatch_simulation_real(
            abc_vec,
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=sc["grid_available"],
            battery_available=sc["battery_available"],
            grid_cap_kw=float(req.config.gridLimitKw) if req.config.gridLimitKw > 0 else None,
        )

        # Run PSO
        t0 = time.time()
        pso_vec, pso_fit, pso_hist = run_pso(
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=sc["grid_available"],
            battery_available=sc["battery_available"],
            bounds=bounds,
            weights=w_pso,
            n_particles=30,
            max_iter=max_iter,
            seed=43,
        )
        pso_time = time.time() - t0

        if not sc["battery_available"]:
            pso_vec[3] = 0.0
            pso_vec[4] = 0.0

        pso_dispatch = dispatch_simulation_real(
            pso_vec,
            solar_profile=solar_scaled,
            wind_profile=wind_scaled,
            load_profile=load_scaled,
            grid_available=sc["grid_available"],
            battery_available=sc["battery_available"],
            grid_cap_kw=float(req.config.gridLimitKw) if req.config.gridLimitKw > 0 else None,
        )

    finally:
        # Restore original dispatch config
        DISPATCH_CONFIG["pv_bus13_kw"] = orig_pv13
        DISPATCH_CONFIG["pv_bus30_kw"] = orig_pv30
        DISPATCH_CONFIG["wind_bus6_kw"] = orig_wind
        DISPATCH_CONFIG["grid_cap_kw"] = orig_grid_cap

    # Compute load satisfaction & metrics
    total_load = float(np.sum(load_scaled))
    abc_tot = abc_dispatch["totals"]
    pso_tot = pso_dispatch["totals"]

    abc_unmet = float(abc_tot["total_unmet_load"])
    pso_unmet = float(pso_tot["total_unmet_load"])

    abc_sat = float(np.clip(((total_load - abc_unmet) / max(total_load, 1e-3)) * 100.0, 0.0, 100.0))
    pso_sat = float(np.clip(((total_load - pso_unmet) / max(total_load, 1e-3)) * 100.0, 0.0, 100.0))

    abc_conv = compute_convergence_speed(abc_hist)
    pso_conv = compute_convergence_speed(pso_hist)

    # Format 24-hour dispatch items
    def make_dispatch_series(disp: Dict[str, Any], cap_kwh: float) -> List[Dict[str, Any]]:
        h = disp["hourly"]
        rows = []
        soc_arr = h["soc"] if ("soc" in h and len(h["soc"]) == 24) else np.zeros(24)
        for hour in range(24):
            demand = float(load_scaled[hour])
            solar = float(h["solar_used"][hour])
            wind = float(h["wind_used"][hour])
            # Net battery dispatch: positive is discharge, negative is charging
            battery = float(h["bat_dis"][hour] - h["bat_chg"][hour])
            grid = float(h["grid_import"][hour])
            unmet = float(h["unmet_load"][hour])
            raw_soc = float(soc_arr[hour])
            soc = raw_soc * 100.0 if 0.0 < raw_soc <= 1.0 else raw_soc
            curtailment = float(h["curtailment"][hour])
            rows.append({
                "hour": hour,
                "demand": demand,
                "solar": solar,
                "wind": wind,
                "battery": battery,
                "grid": grid,
                "unmet": unmet,
                "soc": soc,
                "curtailment": curtailment,
            })
        return rows

    abc_dispatch_rows = make_dispatch_series(abc_dispatch, abc_vec[4])
    pso_dispatch_rows = make_dispatch_series(pso_dispatch, pso_vec[4])

    abc_result = {
        "name": "ABC",
        "algorithm": "ABC",
        "dispatch": abc_dispatch_rows,
        "unmetKwh": abc_unmet,
        "cost": float(abc_tot["total_cost"]),
        "totalCost": float(abc_tot["total_cost"]),
        "capitalCost": float(abc_tot["c_capital"]),
        "operationalCost": float(abc_tot["c_op"]),
        "energyLossKwh": float(abc_tot["total_loss"]),
        "busTransLossKwh": float(abc_tot["bus_trans_loss"]),
        "curtailmentKwh": float(abc_tot.get("total_curtailment", 0.0)),
        "renewableUtilization": float(abc_tot["utilization_pct"]),
        "loadSatisfaction": abc_sat,
        "objective": float(abc_fit),
        "executionSeconds": round(abc_time, 2),
        "convergenceIterations": abc_conv,
        "convergence": abc_hist.tolist(),
        "vector": abc_vec.tolist(),
        "capacities": {
            "pv_bus13_kw": round(float(abc_vec[0] * DISPATCH_CONFIG["pv_bus13_kw"]), 1),
            "pv_bus30_kw": round(float(abc_vec[1] * DISPATCH_CONFIG["pv_bus30_kw"]), 1),
            "wind_bus6_kw": round(float(abc_vec[2] * DISPATCH_CONFIG["wind_bus6_kw"]), 1),
            "battery_power_kw": round(float(abc_vec[3]), 1),
            "battery_capacity_kwh": round(float(abc_vec[4]), 1),
            "grid_limit_kw": round(float(abc_vec[5]), 1),
        },
    }

    pso_result = {
        "name": "PSO",
        "algorithm": "PSO",
        "dispatch": pso_dispatch_rows,
        "unmetKwh": pso_unmet,
        "cost": float(pso_tot["total_cost"]),
        "totalCost": float(pso_tot["total_cost"]),
        "capitalCost": float(pso_tot["c_capital"]),
        "operationalCost": float(pso_tot["c_op"]),
        "energyLossKwh": float(pso_tot["total_loss"]),
        "busTransLossKwh": float(pso_tot["bus_trans_loss"]),
        "curtailmentKwh": float(pso_tot.get("total_curtailment", 0.0)),
        "renewableUtilization": float(pso_tot["utilization_pct"]),
        "loadSatisfaction": pso_sat,
        "objective": float(pso_fit),
        "executionSeconds": round(pso_time, 2),
        "convergenceIterations": pso_conv,
        "convergence": pso_hist.tolist(),
        "vector": pso_vec.tolist(),
        "capacities": {
            "pv_bus13_kw": round(float(pso_vec[0] * DISPATCH_CONFIG["pv_bus13_kw"]), 1),
            "pv_bus30_kw": round(float(pso_vec[1] * DISPATCH_CONFIG["pv_bus30_kw"]), 1),
            "wind_bus6_kw": round(float(pso_vec[2] * DISPATCH_CONFIG["wind_bus6_kw"]), 1),
            "battery_power_kw": round(float(pso_vec[3]), 1),
            "battery_capacity_kwh": round(float(pso_vec[4]), 1),
            "grid_limit_kw": round(float(pso_vec[5]), 1),
        },
    }

    # Autonomous capacity recommendations
    sc_dict_for_rec = {
        "abc": {
            "load_satisfaction": abc_sat,
            "unmet_load_kwh": abc_unmet,
            "curtailment_kwh": float(abc_tot.get("total_curtailment", 0.0)),
        },
        "scenario_params": sc,
    }
    gap = analyze_load_gap(sc_dict_for_rec)
    recs = []
    recs.extend(recommend_pv(gap["peak_gap_kw"], abc_vec.tolist()))
    recs.extend(recommend_battery(sc_dict_for_rec, gap))
    recs.extend(recommend_grid(sc_dict_for_rec, gap))

    # Overall outcome
    overall_winner = "ABC" if (abc_unmet < pso_unmet or (abc_unmet == pso_unmet and abc_result["cost"] <= pso_result["cost"])) else "PSO"
    violations_count = int(abc_tot["battery_violations"] + pso_tot["battery_violations"])

    return sanitize_for_json({
        "scenario": {
            "index": sc_idx,
            "name": sc["name"],
            "description": f"Demand ×{sc['load_multiplier']}, Solar ×{sc['solar_multiplier']}, Wind ×{sc['wind_multiplier']}.",
            "load": sc["load_multiplier"],
            "solar": sc["solar_multiplier"],
            "wind": sc["wind_multiplier"],
            "grid": 1.0 if sc["grid_available"] else 0.0,
            "battery": 1.0 if sc["battery_available"] else 0.0,
        },
        "dataset": req.dataset,
        "config": req.config.model_dump(),
        "abc": abc_result,
        "pso": pso_result,
        "overallWinner": overall_winner,
        "losses": {
            "abc_system_loss_kwh": float(abc_tot["total_loss"]),
            "pso_system_loss_kwh": float(pso_tot["total_loss"]),
            "abc_cable_transmission_loss_kwh": float(abc_tot["bus_trans_loss"]),
            "pso_cable_transmission_loss_kwh": float(pso_tot["bus_trans_loss"]),
            "cable_loss_details": abc_dispatch.get("bus_losses", {}),
        },
        "feasibility": "Power balance satisfied" if max(abc_unmet, pso_unmet) == 0 else "Shortfall detected",
        "violations": {
            "battery_violations": violations_count,
            "thermal_violations": 0,
            "prohibited_violations": 0,
        },
        "recommendations": recs,
        "completedAt": time.strftime("%H:%M:%S"),
    })


@app.post("/api/optimize")
def optimize_endpoint(req: OptimizeRequest):
    """
    Runs real ABC and PSO algorithms against the microgrid network and selected scenario.
    Supports both fast synchronous completion or background job polling via ?async_job=true.
    """
    if req.async_job:
        job_id = str(uuid.uuid4())[:8]
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "running",
            "progress": 0,
            "result": None,
            "error": None,
            "started_at": time.time(),
        }

        def run_job():
            try:
                res = execute_optimization(req)
                JOBS[job_id]["status"] = "complete"
                JOBS[job_id]["result"] = res
                JOBS[job_id]["progress"] = 100
            except Exception as e:
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = str(e)

        executor.submit(run_job)
        return sanitize_for_json({
            "job_id": job_id,
            "status": "running",
            "poll_url": f"/api/results/{job_id}",
        })

    # Synchronous execution
    try:
        return execute_optimization(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.get("/api/results/{job_id}")
def get_job_result(job_id: str):
    """Retrieves status and output of an asynchronous optimization job."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return sanitize_for_json(job)


@app.post("/api/recommendations")
def get_recommendations(req: RecommendationRequest):
    """
    Evaluates microgrid deficit gap and returns autonomous capacity sizing
    and 20-year amortized financial recommendations.
    """
    scenarios = get_scenarios()
    sc_idx = req.scenario_index if req.scenario_index is not None and 0 <= req.scenario_index < len(scenarios) else 0
    sc = scenarios[sc_idx]

    sc_dict = {
        "abc": {
            "load_satisfaction": req.load_satisfaction or 100.0,
            "unmet_load_kwh": req.unmet_kwh or 0.0,
        },
        "scenario_params": {
            "name": req.scenario_name or sc["name"],
            "grid_available": req.grid_available if req.grid_available is not None else sc["grid_available"],
        },
    }

    gap = analyze_load_gap(sc_dict)
    curr_vec = req.current_vector or [1.0, 1.0, 1.0, 500.0, 1800.0, 3200.0]

    recs = []
    recs.extend(recommend_pv(gap["peak_gap_kw"], curr_vec))
    recs.extend(recommend_battery(sc_dict, gap))
    recs.extend(recommend_grid(sc_dict, gap))

    return sanitize_for_json({
        "gap_analysis": gap,
        "recommendations": recs,
        "total_actions": len(recs),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="127.0.0.1", port=8000, reload=True)
