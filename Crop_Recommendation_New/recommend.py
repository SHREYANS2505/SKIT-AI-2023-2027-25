"""Prediction interface with ranked class probabilities."""
from pathlib import Path
import joblib
import pandas as pd
from .config import MODEL_PATH, FEATURES
from .data_validation import validate_sample

def load_bundle(path=MODEL_PATH):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}. Run: python -m src.train")
    return joblib.load(path)

def recommend(sample: dict, bundle=None, top_k=3):
    """Return top-k crop candidates and confidence scores for a single sample."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    bundle = bundle or load_bundle()
    normalized = validate_sample(sample)
    frame = pd.DataFrame([{feature: normalized[feature] for feature in FEATURES}])
    pipeline = bundle["pipeline"]
    probabilities = pipeline.predict_proba(frame)[0]
    classes = pipeline.named_steps["classifier"].classes_
    ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
    return [{"crop": str(crop), "probability": round(float(prob), 5)}
            for crop, prob in ranked[:top_k]]

def explain_sample(sample: dict, bundle=None):
    """Return the recommendation and basic input summary for an application screen."""
    normalized = validate_sample(sample)
    return {
        "recommendations": recommend(normalized, bundle=bundle, top_k=5),
        "input_summary": {
            "npk_total": round(normalized["nitrogen"] + normalized["phosphorus"] + normalized["potassium"], 2),
            "temperature": normalized["temperature"],
            "rainfall": normalized["rainfall"],
            "soil_type": normalized["soil_type"],
            "season": normalized["season"],
        },
        "note": "Predictions are a data-science aid, not a substitute for local agronomic advice."
    }
