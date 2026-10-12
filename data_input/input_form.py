"""
input_form.py - Custom Parameter Acquisition, Synthesis & Persistence for EcoGridAI

Role: Provides functions to collect, synthesize, preview, and persist custom generator bus
ratings and 24-hour load profiles into custom_config.json.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from .validator import (
    validate_bus_ratings,
    validate_load_profile,
    validate_csv_columns,
    ValidationResult,
)

CONFIG: Dict[str, Any] = {
    "default_config_path": Path(__file__).parent.parent / "custom_config.json",
    # Typical 24-hour normalized diurnal load curve (pu shape with morning/evening peaks)
    "default_diurnal_shape": np.array([
        0.58, 0.54, 0.52, 0.50, 0.53, 0.62,
        0.75, 0.88, 0.94, 0.98, 1.00, 0.96,
        0.92, 0.90, 0.92, 0.95, 0.98, 0.97,
        0.93, 0.88, 0.82, 0.76, 0.68, 0.62
    ], dtype=np.float64),
}


def synthesize_diurnal_load_profile(
    peak_kw: float,
    base_shape: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Synthesizes a 24-hour diurnal load curve scaled to a specified peak kW.

    Args:
        peak_kw: Peak load demand in kW (e.g. 3715.0 kW).
        base_shape: Optional normalized shape array of length 24.

    Returns:
        np.ndarray of length 24 in kW.
    """
    if base_shape is None:
        shape = CONFIG["default_diurnal_shape"].copy()
    else:
        shape = np.array(base_shape, dtype=np.float64)
        if len(shape) != 24:
            raise ValueError(f"Base shape must have length 24, got {len(shape)}")
        max_v = np.max(shape)
        if max_v > 0:
            shape = shape / max_v

    profile = shape * float(peak_kw)
    return profile


def format_profile_ascii_table(profile: np.ndarray, width: int = 35) -> str:
    """
    Generates a clean terminal ASCII horizontal bar preview of a 24-hour profile.

    Args:
        profile: 24-hour load array in kW.
        width: Maximum character width for ASCII bars.

    Returns:
        Formatted multi-line ASCII preview string.
    """
    lines = []
    max_val = np.max(profile) if len(profile) > 0 and np.max(profile) > 0 else 1.0
    lines.append(f"{'Hour':<6} | {'Load (kW)':<12} | {'Diurnal Distribution':<{width}}")
    lines.append("-" * (22 + width))

    for h in range(len(profile)):
        val = profile[h]
        bar_len = int(round((val / max_val) * width))
        bar = "#" * bar_len
        lines.append(f"H{h+1:02d}    | {val:>9.1f} kW | {bar}")

    lines.append("-" * (22 + width))
    lines.append(f"Peak: {np.max(profile):.1f} kW | Min: {np.min(profile):.1f} kW | Total: {np.sum(profile):,.1f} kWh/day")
    return "\n".join(lines)


def load_profile_from_csv(csv_path: Union[str, Path]) -> ValidationResult:
    """Loads and validates a 24-hour load profile from an external CSV file."""
    p = Path(csv_path).resolve()
    if not p.is_file():
        return ValidationResult(
            valid=False,
            errors=[f"[ERROR] [file]: CSV file not found at path '{csv_path}'"],
        )

    try:
        df = pd.read_csv(p)
        # Search for load column
        target_col = None
        for cand in ["Total_Load_kW", "Load_kW", "Load", "load_kw", "load"]:
            if cand in df.columns:
                target_col = cand
                break

        if target_col is None:
            # Check column 1 if numeric
            if len(df.columns) >= 2 and pd.to_numeric(df.iloc[:, 1], errors="coerce").notnull().sum() >= 24:
                target_col = df.columns[1]
            else:
                return ValidationResult(
                    valid=False,
                    errors=[f"[ERROR] [csv.columns]: No recognizable load column found in {df.columns.tolist()}"],
                )

        vals = pd.to_numeric(df[target_col], errors="coerce").dropna().values[:24]
        return validate_load_profile(vals)

    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[f"[ERROR] [csv.parse]: Failed to parse CSV file: {e}"],
        )


def build_custom_configuration(
    bus_ratings: List[Dict[str, Any]],
    load_profile: Union[List[float], np.ndarray],
    author: str = "EcoGridAI Operator",
    description: str = "Custom IEEE 33-Bus Microgrid Configuration",
) -> Dict[str, Any]:
    """
    Validates and packages parameters into a standardized custom configuration dictionary.

    Returns:
        Structured configuration dictionary ready for persistence.
    """
    res_buses = validate_bus_ratings(bus_ratings)
    if not res_buses.valid:
        raise ValueError(f"Bus ratings validation failed: {res_buses.errors}")

    res_load = validate_load_profile(load_profile)
    if not res_load.valid:
        raise ValueError(f"Load profile validation failed: {res_load.errors}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    config: Dict[str, Any] = {
        "version": "1.0.0",
        "created_at": timestamp,
        "author": author,
        "description": description,
        "bus_ratings": res_buses.data["ratings"],
        "system_capacities": {
            "total_pv_kw": res_buses.data["total_pv_kw"],
            "total_wind_kw": res_buses.data["total_wind_kw"],
            "pv_buses": res_buses.data["pv_buses"],
            "wind_buses": res_buses.data["wind_buses"],
        },
        "load_profile": {
            "hourly_load_kw": [round(float(x), 2) for x in res_load.data["profile"]],
            "peak_load_kw": round(float(res_load.data["peak_kw"]), 2),
            "min_load_kw": round(float(res_load.data["min_kw"]), 2),
            "total_load_kwh": round(float(res_load.data["total_kwh"]), 2),
            "load_factor": round(float(res_load.data["load_factor"]), 4),
        },
    }

    return config


def save_custom_config(
    config_dict: Dict[str, Any],
    filepath: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Saves validated custom configuration to JSON file.

    Args:
        config_dict: Standardized configuration dictionary.
        filepath: Target output path. Defaults to Resource_optimizer_real/custom_config.json.

    Returns:
        Resolved Path to saved configuration file.
    """
    out_path = Path(filepath) if filepath else CONFIG["default_config_path"]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)

    print(f" [Custom Config] Configuration successfully saved to: {out_path.resolve()}")
    print(f" [Custom Config] Saved at: {config_dict.get('created_at', datetime.now().isoformat())}")
    print(f" [Custom Config] PV Capacity: {config_dict['system_capacities']['total_pv_kw']:.1f} kW across buses {config_dict['system_capacities']['pv_buses']}")
    print(f" [Custom Config] Wind Capacity: {config_dict['system_capacities']['total_wind_kw']:.1f} kW across buses {config_dict['system_capacities']['wind_buses']}")
    print(f" [Custom Config] Peak Load: {config_dict['load_profile']['peak_load_kw']:.1f} kW | Daily: {config_dict['load_profile']['total_load_kwh']:,.1f} kWh")

    return out_path.resolve()


def load_custom_config(
    filepath: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Loads and verifies custom configuration from JSON file.

    Returns:
        Configuration dictionary if valid and existing, else None.
    """
    in_path = Path(filepath) if filepath else CONFIG["default_config_path"]
    if not in_path.is_file():
        # Fallback check relative to current dir
        cand = Path(__file__).parent.parent / in_path.name
        if cand.is_file():
            in_path = cand
        else:
            return None

    try:
        with open(in_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Validate structure
        res_bus = validate_bus_ratings(cfg.get("bus_ratings", []))
        load_vals = cfg.get("load_profile", {}).get("hourly_load_kw", [])
        res_load = validate_load_profile(load_vals)

        if not res_bus.valid or not res_load.valid:
            print(f" [Custom Config] Warning: Config at {in_path} contains validation errors:")
            for err in res_bus.errors + res_load.errors:
                print(f"   {err}")
            return None

        return cfg
    except Exception as e:
        print(f" [Custom Config] Error loading {in_path}: {e}")
        return None
