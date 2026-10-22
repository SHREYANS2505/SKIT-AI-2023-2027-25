"""Input/data validation helpers."""
from __future__ import annotations
import pandas as pd
from .config import FEATURES, TARGET, NUMERIC_FEATURES, CATEGORICAL_FEATURES

ALLOWED = {
    "soil_type": {"loamy", "clayey", "sandy", "silty"},
    "season": {"kharif", "rabi", "zaid"},
    "region_zone": {"arid", "semi_arid", "sub_humid", "humid"},
}
LIMITS = {
    "nitrogen": (0, 140), "phosphorus": (0, 145), "potassium": (0, 210),
    "temperature": (-5, 55), "humidity": (0, 100), "ph": (3, 10),
    "rainfall": (0, 400),
}

def validate_frame(frame: pd.DataFrame, require_target: bool = True) -> pd.DataFrame:
    """Validate schema and values; return a defensive copy."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")
    required = FEATURES + ([TARGET] if require_target else [])
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    out = frame[required].copy()
    if out.empty:
        raise ValueError("Dataset must contain at least one row.")
    for col in NUMERIC_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        if out[col].isna().any():
            raise ValueError(f"Column {col!r} contains missing or non-numeric values.")
        lo, hi = LIMITS[col]
        if not out[col].between(lo, hi).all():
            raise ValueError(f"Column {col!r} must be between {lo} and {hi}.")
    for col, allowed in ALLOWED.items():
        if out[col].isna().any() or not out[col].isin(allowed).all():
            raise ValueError(f"Column {col!r} has an unsupported category.")
    if require_target and (out[TARGET].isna().any() or (out[TARGET].astype(str).str.strip()=="").any()):
        raise ValueError("Target crop labels must be present.")
    return out

def validate_sample(sample: dict) -> dict:
    """Validate one feature dictionary and return normalized values."""
    missing = sorted(set(FEATURES) - set(sample))
    if missing:
        raise ValueError(f"Missing feature(s): {missing}")
    frame = pd.DataFrame([{k: sample[k] for k in FEATURES}])
    normalized = validate_frame(frame, require_target=False)
    return normalized.iloc[0].to_dict()
