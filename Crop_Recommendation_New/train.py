"""Train and persist a reproducible classification pipeline."""
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from .config import DATA_PATH, MODEL_PATH, FEATURES, TARGET, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from .data_validation import validate_frame

def build_pipeline(model_kind: str = "random_forest") -> Pipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler())])
    categorical = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                            ("encoder", OneHotEncoder(handle_unknown="ignore"))])
    prep = ColumnTransformer([("numeric", numeric, NUMERIC_FEATURES),
                              ("categorical", categorical, CATEGORICAL_FEATURES)])
    if model_kind == "extra_trees":
        estimator = ExtraTreesClassifier(n_estimators=240, min_samples_leaf=2,
                                         class_weight="balanced", random_state=2026,
                                         n_jobs=-1)
    elif model_kind == "random_forest":
        estimator = RandomForestClassifier(n_estimators=260, min_samples_leaf=2,
                                           class_weight="balanced_subsample",
                                           random_state=2026, n_jobs=-1)
    else:
        raise ValueError("model_kind must be 'random_forest' or 'extra_trees'")
    return Pipeline([("preprocess", prep), ("classifier", estimator)])

def train(data_path=DATA_PATH, model_path=MODEL_PATH, model_kind="random_forest"):
    frame = pd.read_csv(data_path)
    frame = validate_frame(frame, require_target=True)
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURES], frame[TARGET], test_size=0.22,
        random_state=2026, stratify=frame[TARGET]
    )
    pipeline = build_pipeline(model_kind)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = {
        "model_kind": model_kind,
        "rows": int(len(frame)),
        "classes": int(frame[TARGET].nunique()),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=sorted(frame[TARGET].unique())).tolist(),
        "labels": sorted(frame[TARGET].unique().tolist()),
    }
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "features": FEATURES, "metrics": metrics}, model_path)
    report_path = model_path.parent.parent / "reports" / "training_metrics.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    result = train()
    print(f"Saved model; holdout accuracy={result['accuracy']:.3f}")
