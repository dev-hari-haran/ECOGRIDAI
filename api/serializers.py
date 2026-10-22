"""
api/serializers.py - Robust Serialization & Data Sanitation for JSON Responses

Converts numpy types, infinities, NaNs, and custom objects to JSON-safe Python native types.
"""

from typing import Any
import math
import numpy as np
import pandas as pd


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively converts numpy numbers, arrays, DataFrames, NaNs, and Infinities
    into valid JSON-safe native Python types.
    """
    if obj is None:
        return None

    if isinstance(obj, (bool, str)):
        return obj

    if isinstance(obj, (int, np.integer)):
        return int(obj)

    if isinstance(obj, (float, np.floating)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return val

    if isinstance(obj, np.ndarray):
        return [sanitize_for_json(x) for x in obj.tolist()]

    if isinstance(obj, pd.DataFrame):
        return [sanitize_for_json(row) for row in obj.to_dict(orient="records")]

    if isinstance(obj, pd.Series):
        return sanitize_for_json(obj.tolist())

    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(x) for x in obj]

    # Fallback to string or dict if possible
    if hasattr(obj, "to_dict"):
        return sanitize_for_json(obj.to_dict())

    return str(obj)
