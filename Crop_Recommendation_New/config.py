"""Configuration and feature definitions for the alternative crop recommender."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "crop_data_alternative.csv"
MODEL_PATH = ROOT / "model" / "crop_model.joblib"
RANDOM_STATE = 2026
NUMERIC_FEATURES = [
    "nitrogen", "phosphorus", "potassium", "temperature",
    "humidity", "ph", "rainfall"
]
CATEGORICAL_FEATURES = ["soil_type", "season", "region_zone"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "crop"
