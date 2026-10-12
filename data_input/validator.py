"""
validator.py - Rigorous Parameter & Profile Validation Engine for EcoGridAI

Role: Validates custom generator bus ratings, IEEE 33-bus topological constraints,
24-hour diurnal load profiles, and input CSV dataset schemas with explicit error taxonomy.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


@dataclass
class ValidationResult:
    """Standardized validation outcome container."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "data": self.data,
        }


def format_error(field_name: str, message: str) -> str:
    """Formats standardized error message with taxonomy."""
    return f"[ERROR] [{field_name}]: {message}"


def format_warning(field_name: str, message: str) -> str:
    """Formats standardized warning message with taxonomy."""
    return f"[WARNING] [{field_name}]: {message}"


def validate_bus_ratings(ratings: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validates generator allocations and nameplate ratings across IEEE 33-bus system.

    Validation Rules:
      1. Bus index must be an integer in [1, 33].
      2. Rating must be strictly positive and <= 10,000 kW.
      3. No duplicate bus allocations (only one generator per bus index).
      4. Generator type must be 'PV' / 'Solar' or 'Wind'.
      5. Warnings issued if total capacity is unusually low (< 100 kW).

    Args:
        ratings: List of dicts e.g. [{"type": "PV", "bus": 13, "rating_kw": 851.5}]

    Returns:
        ValidationResult with status, errors, warnings, and sanitized rating list.
    """
    errors: List[str] = []
    warnings: List[str] = []
    sanitized: List[Dict[str, Any]] = []

    if not ratings or not isinstance(ratings, list):
        errors.append(format_error("ratings", "Ratings list is empty or invalid format."))
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    seen_buses: set = set()
    total_pv_kw: float = 0.0
    total_wind_kw: float = 0.0

    for idx, item in enumerate(ratings):
        if not isinstance(item, dict):
            errors.append(format_error(f"rating[{idx}]", "Item must be a dictionary."))
            continue

        # Type validation
        gen_type_raw = str(item.get("type", "")).strip().upper()
        if gen_type_raw in ["PV", "SOLAR"]:
            gen_type = "PV"
        elif gen_type_raw in ["WIND", "WT"]:
            gen_type = "Wind"
        else:
            errors.append(
                format_error(
                    f"rating[{idx}].type",
                    f"Invalid generator type '{item.get('type')}'. Supported types: 'PV', 'Wind'."
                )
            )
            continue

        # Bus validation
        bus_raw = item.get("bus")
        try:
            bus_id = int(bus_raw)
            if bus_id < 1 or bus_id > 33:
                errors.append(
                    format_error(
                        f"rating[{idx}].bus",
                        f"Bus number {bus_id} is out of range (valid IEEE 33-bus range: 1–33)."
                    )
                )
                continue
        except (ValueError, TypeError):
            errors.append(
                format_error(
                    f"rating[{idx}].bus",
                    f"Bus identifier '{bus_raw}' is not a valid integer."
                )
            )
            continue

        # Duplicate bus check
        if bus_id in seen_buses:
            errors.append(
                format_error(
                    f"rating[{idx}].bus",
                    f"Duplicate generator allocation detected at Bus {bus_id}. Each bus permits at most 1 generation source."
                )
            )
            continue
        seen_buses.add(bus_id)

        # Rating kW validation
        rating_raw = item.get("rating_kw", item.get("rating"))
        try:
            rating_kw = float(rating_raw)
            if rating_kw <= 0.0:
                errors.append(
                    format_error(
                        f"rating[{idx}].rating_kw",
                        f"Rating {rating_kw:.2f} kW is invalid. Capacity must be strictly positive (> 0 kW)."
                    )
                )
                continue
            if rating_kw > 10000.0:
                errors.append(
                    format_error(
                        f"rating[{idx}].rating_kw",
                        f"Rating {rating_kw:.2f} kW exceeds system thermal threshold (maximum: 10,000 kW per bus)."
                    )
                )
                continue
        except (ValueError, TypeError):
            errors.append(
                format_error(
                    f"rating[{idx}].rating_kw",
                    f"Rating value '{rating_raw}' is not a valid number."
                )
            )
            continue

        if gen_type == "PV":
            total_pv_kw += rating_kw
        else:
            total_wind_kw += rating_kw

        sanitized.append({
            "type": gen_type,
            "bus": bus_id,
            "rating_kw": rating_kw,
            "label": item.get("label", f"{gen_type}_Bus{bus_id}"),
        })

    # Portfolio warnings
    if total_pv_kw > 0 and total_pv_kw < 100.0:
        warnings.append(format_warning("total_pv", f"Total PV capacity ({total_pv_kw:.1f} kW) is unusually small."))
    if total_wind_kw > 0 and total_wind_kw < 100.0:
        warnings.append(format_warning("total_wind", f"Total Wind capacity ({total_wind_kw:.1f} kW) is unusually small."))

    is_valid = len(errors) == 0 and len(sanitized) > 0
    return ValidationResult(
        valid=is_valid,
        errors=errors,
        warnings=warnings,
        data={
            "ratings": sanitized,
            "total_pv_kw": total_pv_kw,
            "total_wind_kw": total_wind_kw,
            "pv_buses": [r["bus"] for r in sanitized if r["type"] == "PV"],
            "wind_buses": [r["bus"] for r in sanitized if r["type"] == "Wind"],
        } if is_valid else None,
    )


def validate_load_profile(profile: Union[List[float], np.ndarray, pd.Series]) -> ValidationResult:
    """
    Validates a 24-hour diurnal microgrid load profile.

    Validation Rules:
      1. Must contain exactly 24 hourly data points.
      2. All hourly values must be strictly positive (> 0 kW).
      3. Peak load must exceed 100 kW.
      4. Issues warning if load factor (average/peak) is unusually low (< 0.20).

    Args:
        profile: Sequence or array of 24 hourly load values in kW.

    Returns:
        ValidationResult with status, errors, warnings, and verified numpy array.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if profile is None:
        errors.append(format_error("load_profile", "Load profile is None."))
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    try:
        arr = np.array(profile, dtype=np.float64)
    except Exception as e:
        errors.append(format_error("load_profile", f"Could not convert profile to float array: {e}"))
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    # 1. Length check
    if len(arr) != 24:
        errors.append(
            format_error(
                "load_profile.length",
                f"Load profile contains {len(arr)} hourly rows (expected exactly 24 hours)."
            )
        )
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    # 2. Positivity check
    non_positive_indices = np.where(arr <= 0.0)[0]
    if len(non_positive_indices) > 0:
        for idx in non_positive_indices:
            errors.append(
                format_error(
                    f"load_profile.hour_{idx+1}",
                    f"Non-positive load value {arr[idx]:.2f} kW detected at Hour {idx+1} (must be > 0 kW)."
                )
            )

    # NaN / Inf check
    if np.isnan(arr).any() or np.isinf(arr).any():
        errors.append(format_error("load_profile", "Profile contains NaN or infinite values."))

    if len(errors) > 0:
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    peak_kw = float(np.max(arr))
    min_kw = float(np.min(arr))
    total_kwh = float(np.sum(arr))
    avg_kw = float(np.mean(arr))

    # 3. Peak load threshold
    if peak_kw < 100.0:
        errors.append(
            format_error(
                "load_profile.peak",
                f"Peak load ({peak_kw:.1f} kW) must be greater than 100 kW for microgrid dispatch simulation."
            )
        )
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    # 4. Load factor warning
    load_factor = avg_kw / peak_kw if peak_kw > 0 else 0
    if load_factor < 0.20:
        warnings.append(
            format_warning(
                "load_profile.load_factor",
                f"Unusually low load factor ({load_factor:.2f}). Peak is very sharp relative to average consumption."
            )
        )

    return ValidationResult(
        valid=True,
        errors=[],
        warnings=warnings,
        data={
            "profile": arr,
            "peak_kw": peak_kw,
            "min_kw": min_kw,
            "total_kwh": total_kwh,
            "avg_kw": avg_kw,
            "load_factor": load_factor,
        },
    )


def validate_csv_columns(
    df: pd.DataFrame,
    expected_cols: Optional[List[str]] = None,
) -> ValidationResult:
    """
    Validates CSV table columns and null value constraints.

    Args:
        df: Input pandas DataFrame
        expected_cols: Required column names. Defaults to ["Hour", "Total_Load_kW"].

    Returns:
        ValidationResult indicating schema validity.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if df is None or not isinstance(df, pd.DataFrame):
        errors.append(format_error("csv", "Provided data is not a valid DataFrame."))
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    if expected_cols is None:
        expected_cols = ["Hour", "Total_Load_kW"]

    for col in expected_cols:
        if col not in df.columns:
            errors.append(format_error("csv.columns", f"Missing mandatory column '{col}' in CSV dataset."))

    if len(errors) > 0:
        return ValidationResult(valid=False, errors=errors, warnings=warnings, data=None)

    # Check nulls
    cleaned_df = df.copy()
    for col in expected_cols:
        null_count = int(cleaned_df[col].isnull().sum())
        if null_count > 0:
            warnings.append(
                format_warning("csv.nulls", f"{null_count} null rows detected in column '{col}'; applying forward fill.")
            )
            cleaned_df[col] = cleaned_df[col].ffill().bfill()

    return ValidationResult(
        valid=True,
        errors=[],
        warnings=warnings,
        data=cleaned_df,
    )
