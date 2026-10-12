"""
real_data_loader.py - Real CSV Data Loader (Data1.csv & Data2.csv)

Role: Loads real hourly microgrid datasets from Data1.csv (measured kW & bus ratings)
and Data2.csv (per-unit normalized profiles), providing structured profiles for optimization.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Union
import numpy as np
import pandas as pd

CONFIG: Dict[str, Any] = {
    "default_data1": "Data1.csv",
    "default_data2": "Data2.csv",
    "fallback_search_dirs": [".", "..", "../Resource_optimizer", "Resource_optimizer"],
}


def find_file(filename: Union[str, Path]) -> Path:
    """Locates target CSV file across candidate search paths."""
    target = Path(filename)
    if target.is_file():
        return target.resolve()

    name = target.name
    current_dir = Path(__file__).parent

    for sdir in CONFIG["fallback_search_dirs"]:
        cand = (current_dir / sdir / name).resolve()
        if cand.is_file():
            return cand

    # Default fallback to filename
    return target


def load_real_data(
    data1_path: Union[str, Path] = "Data1.csv",
    data2_path: Union[str, Path] = "Data2.csv",
) -> Dict[str, Any]:
    """
    Reads Data1.csv and Data2.csv and returns structured dictionary with
    primary measured kW profiles (Data1), secondary per-unit/scaled profiles (Data2),
    bus ratings, and system capacity metrics.
    """
    f1 = find_file(data1_path)
    f2 = find_file(data2_path)

    # 1. Parse Data1.csv (Skip double-header rows 0 and 1)
    cols = [
        "Hour", "Total_Load_kW", "Commercial_kW", "Industry_kW",
        "Residential_kW", "PV_kW", "Wind_kW",
        "_empty", "Bus_Label", "Bus_Location", "Bus_Rating"
    ]

    df1 = pd.read_csv(f1, header=None, skiprows=2)
    # Assign column names up to number of columns present
    df1.columns = cols[: len(df1.columns)]

    df1["Total_Load_kW"] = pd.to_numeric(df1["Total_Load_kW"], errors="coerce")
    df1["PV_kW"] = pd.to_numeric(df1["PV_kW"], errors="coerce")
    df1["Wind_kW"] = pd.to_numeric(df1["Wind_kW"], errors="coerce")

    hourly_load = df1["Total_Load_kW"].dropna().values[:24].astype(np.float64)
    hourly_pv = df1["PV_kW"].dropna().values[:24].astype(np.float64)
    hourly_wind = df1["Wind_kW"].dropna().values[:24].astype(np.float64)

    # Extract bus rating table from columns 8-10
    bus_df = df1[["Bus_Label", "Bus_Location", "Bus_Rating"]].dropna().copy()
    bus_ratings = []
    pv_buses = []
    wind_buses = []

    for _, row in bus_df.iterrows():
        lbl = str(row["Bus_Label"]).strip()
        bus_num = int(float(str(row["Bus_Location"]).strip()))
        rating_str = str(row["Bus_Rating"]).lower().replace("kw", "").strip()
        rating_kw = float(rating_str)

        bus_ratings.append({"label": lbl, "bus": bus_num, "rating_kw": rating_kw})

        if "pv" in lbl.lower():
            pv_buses.append(bus_num)
        elif "wind" in lbl.lower():
            wind_buses.append(bus_num)

    total_pv_capacity = float(sum(b["rating_kw"] for b in bus_ratings if "pv" in b["label"].lower()))
    total_wind_capacity = float(sum(b["rating_kw"] for b in bus_ratings if "wind" in b["label"].lower()))
    peak_load = float(np.max(hourly_load))

    # Fallbacks if bus ratings missing
    if total_pv_capacity == 0:
        total_pv_capacity = 2009.1
        pv_buses = [13, 30]
    if total_wind_capacity == 0:
        total_wind_capacity = 2097.97
        wind_buses = [6]

    # Print Data1 Summary
    print(f"[Data Loader] Data1: {len(hourly_load)} hours loaded")
    print(f"[Data Loader] Peak Load: {peak_load:.1f} kW")
    print(f"[Data Loader] Total PV Capacity: {total_pv_capacity:.2f} kW")
    print(f"[Data Loader] Total Wind Capacity: {total_wind_capacity:.2f} kW")

    bus_str_list = [f"{b['label']}@Bus{b['bus']}={b['rating_kw']}kW" for b in bus_ratings]
    print(f"[Data Loader] Bus Ratings: {', '.join(bus_str_list)}")

    # 2. Parse Data2.csv (Normalized per-unit values)
    df2 = pd.read_csv(f2)
    df2.columns = [str(c).strip() for c in df2.columns]

    # Find matching columns flexibly
    load_col = [c for c in df2.columns if "load" in c.lower() or "demand" in c.lower()][0]
    pv_col = [c for c in df2.columns if "pv" in c.lower()][0]
    wind_col = [c for c in df2.columns if "wind" in c.lower()][0]

    hourly_load_pu = pd.to_numeric(df2[load_col], errors="coerce").fillna(0.0).values[:24].astype(np.float64)
    hourly_pv_pu = pd.to_numeric(df2[pv_col], errors="coerce").fillna(0.0).values[:24].astype(np.float64)
    hourly_wind_pu = pd.to_numeric(df2[wind_col], errors="coerce").fillna(0.0).values[:24].astype(np.float64)

    # Scale Data2 per-unit profiles to kW
    hourly_load_d2 = hourly_load_pu * peak_load
    hourly_pv_d2 = hourly_pv_pu * total_pv_capacity
    hourly_wind_d2 = hourly_wind_pu * total_wind_capacity

    print("[Data Loader] Data2: normalized profiles loaded and scaled")

    return {
        "hourly_load": hourly_load,
        "hourly_pv": hourly_pv,
        "hourly_wind": hourly_wind,
        "hourly_load_pu": hourly_load_pu,
        "hourly_pv_pu": hourly_pv_pu,
        "hourly_wind_pu": hourly_wind_pu,
        "hourly_load_d2": hourly_load_d2,
        "hourly_pv_d2": hourly_pv_d2,
        "hourly_wind_d2": hourly_wind_d2,
        "bus_ratings": bus_ratings,
        "total_pv_capacity": total_pv_capacity,
        "total_wind_capacity": total_wind_capacity,
        "peak_load": peak_load,
        "pv_buses": pv_buses,
        "wind_buses": wind_buses,
    }


if __name__ == "__main__":
    data = load_real_data("Data1.csv", "Data2.csv")

    print("\n--- FIRST 5 ROWS OF EACH PROFILE ARRAY ---")
    print(f"Data1 Hourly Load (kW) : {data['hourly_load'][:5]}")
    print(f"Data1 Hourly PV (kW)   : {data['hourly_pv'][:5]}")
    print(f"Data1 Hourly Wind (kW) : {data['hourly_wind'][:5]}")
    print("-" * 50)
    print(f"Data2 Load Per-Unit    : {data['hourly_load_pu'][:5]}")
    print(f"Data2 PV Per-Unit      : {data['hourly_pv_pu'][:5]}")
    print(f"Data2 Wind Per-Unit    : {data['hourly_wind_pu'][:5]}")
    print("-" * 50)
    print(f"Data2 Scaled Load (kW) : {data['hourly_load_d2'][:5]}")
    print(f"Data2 Scaled PV (kW)   : {data['hourly_pv_d2'][:5]}")
    print(f"Data2 Scaled Wind (kW) : {data['hourly_wind_d2'][:5]}")
