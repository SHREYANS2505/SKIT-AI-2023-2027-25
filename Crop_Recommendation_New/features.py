"""Feature preparation and descriptive agronomy helpers."""
import pandas as pd
from .config import NUMERIC_FEATURES, CATEGORICAL_FEATURES

def add_derived_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add transparent derived features without modifying the caller's frame."""
    result = frame.copy()
    result["npk_total"] = result[["nitrogen", "phosphorus", "potassium"]].sum(axis=1)
    result["npk_balance"] = result[["nitrogen", "phosphorus", "potassium"]].max(axis=1) - result[["nitrogen", "phosphorus", "potassium"]].min(axis=1)
    result["temperature_band"] = pd.cut(
        result["temperature"], bins=[-10, 15, 25, 35, 60],
        labels=["cool", "mild", "warm", "hot"], include_lowest=True
    ).astype(str)
    result["rainfall_band"] = pd.cut(
        result["rainfall"], bins=[-1, 40, 80, 140, 450],
        labels=["low", "moderate", "high", "very_high"], include_lowest=True
    ).astype(str)
    return result

def summarize_numeric(frame: pd.DataFrame) -> dict:
    """Return stable descriptive statistics for numeric agronomy features."""
    summary = {}
    for column in NUMERIC_FEATURES:
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        summary[column] = {
            "count": int(values.count()),
            "mean": float(values.mean()),
            "median": float(values.median()),
            "std": float(values.std(ddof=1) if len(values) > 1 else 0),
            "min": float(values.min()),
            "max": float(values.max()),
        }
    return summary

def category_counts(frame: pd.DataFrame) -> dict:
    """Summarize each categorical feature without imposing an ordering."""
    return {column: frame[column].value_counts(dropna=False).to_dict()
            for column in CATEGORICAL_FEATURES}
