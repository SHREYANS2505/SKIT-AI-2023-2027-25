import pytest
import pandas as pd
from src.data_validation import validate_sample, validate_frame
from src.recommend import recommend
from src.config import FEATURES

def sample():
    return {"nitrogen":55,"phosphorus":45,"potassium":40,"temperature":26,
            "humidity":65,"ph":6.5,"rainfall":70,"soil_type":"loamy",
            "season":"kharif","region_zone":"sub_humid"}

def test_valid_sample_is_normalized():
    assert validate_sample(sample())["soil_type"] == "loamy"

def test_missing_feature_raises():
    bad = sample()
    bad.pop("rainfall")
    with pytest.raises(ValueError):
        validate_sample(bad)

def test_unknown_category_raises():
    bad = sample()
    bad["soil_type"] = "unknown"
    with pytest.raises(ValueError):
        validate_sample(bad)

def test_out_of_range_raises():
    bad = sample()
    bad["humidity"] = 101
    with pytest.raises(ValueError):
        validate_sample(bad)

def test_recommendations_ranked():
    results = recommend(sample(), top_k=5)
    assert len(results) == 5
    assert results[0]["probability"] >= results[-1]["probability"]
    assert all(0 <= item["probability"] <= 1 for item in results)
