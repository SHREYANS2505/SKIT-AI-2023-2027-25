"""
=============================================================================
Module: financial_risk/train_models.py
Description:
    Trains an ensemble of Random Forest and Gradient Boosted Decision Trees
    (HistGradientBoosting / XGBoost architecture) for Indian Farmer
    Financial Risk Prediction & Credit Health Scoring.
=============================================================================
"""

import os
os.environ['LOKY_MAX_CPU_COUNT'] = '4'
import sys
import json
import pickle
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, f1_score

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'farmer_credit_data.csv')
RF_PATH = os.path.join(BASE_DIR, 'rf_model.pkl')
XGB_PATH = os.path.join(BASE_DIR, 'xgb_model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')
META_PATH = os.path.join(BASE_DIR, 'ensemble_meta.json')

FEATURE_COLS = [
    'total_land',
    'land_ownership_code',
    'irrigation_code',
    'farming_experience',
    'has_kcc',
    'has_insurance',
    'is_fpo_member',
    'crop_diversity',
    'annual_income',
    'monthly_income',
    'loan_amount',
    'existing_emi',
    'dti_ratio',
    'loan_to_land',
    'weather_risk_index',
    'mandi_price_trend',
    'days_to_due'
]

TARGET_COL = 'risk_class'

def train_financial_risk_ensemble():
    print("=" * 72)
    print("🌾 Training Financial Risk ML Ensemble (XGBoost + Random Forest)")
    print("=" * 72)

    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded {len(df)} records from {os.path.basename(DATASET_PATH)}")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].values

    # Train / Test Split (80 / 20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Random Forest Classifier (Bagging)
    print("\n1. Training Random Forest Classifier (160 Trees)...")
    rf_model = RandomForestClassifier(
        n_estimators=160,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42,
        n_jobs=1
    )
    rf_model.fit(X_train_scaled, y_train)

    rf_preds = rf_model.predict(X_test_scaled)
    rf_acc = accuracy_score(y_test, rf_preds)
    print(f"   • Random Forest Test Accuracy: {rf_acc * 100:.2f}%")

    # 2. Gradient Boosted Trees (XGBoost / HistGradientBoosting Architecture)
    print("\n2. Training Gradient Boosted Trees (XGBoost-style Architecture)...")
    xgb_model = HistGradientBoostingClassifier(
        max_iter=160,
        max_depth=6,
        learning_rate=0.08,
        l2_regularization=1.2,
        min_samples_leaf=20,
        random_state=42
    )
    xgb_model.fit(X_train_scaled, y_train)

    xgb_preds = xgb_model.predict(X_test_scaled)
    xgb_acc = accuracy_score(y_test, xgb_preds)
    print(f"   • Gradient Boosted Model Test Accuracy: {xgb_acc * 100:.2f}%")

    # 3. Soft-Voting Weighted Ensemble
    print("\n3. Evaluating Blended Ensemble (55% Gradient Boosting + 45% Random Forest)...")
    rf_prob = rf_model.predict_proba(X_test_scaled)
    xgb_prob = xgb_model.predict_proba(X_test_scaled)
    ensemble_prob = 0.55 * xgb_prob + 0.45 * rf_prob
    ensemble_preds = np.argmax(ensemble_prob, axis=1)

    ens_acc = accuracy_score(y_test, ensemble_preds)
    ens_f1 = f1_score(y_test, ensemble_preds, average='weighted')
    cm = confusion_matrix(y_test, ensemble_preds)

    print("-" * 72)
    print(f"📊 ENSEMBLE EVALUATION SCORECARD:")
    print(f"   • Accuracy:           {ens_acc * 100:.2f} %")
    print(f"   • Weighted F1-Score:  {ens_f1 * 100:.2f} %")
    print("-" * 72)
    print("\nDetailed Classification Report:")
    target_names = ['Low Risk (Safe)', 'Moderate Risk (Caution)', 'High Risk (Critical)']
    print(classification_report(y_test, ensemble_preds, target_names=target_names))

    print("Confusion Matrix:")
    print(f"                 Pred Low  Pred Mod  Pred High")
    print(f"  True Low      {cm[0][0]:8d}  {cm[0][1]:8d}  {cm[0][2]:9d}")
    print(f"  True Moderate {cm[1][0]:8d}  {cm[1][1]:8d}  {cm[1][2]:9d}")
    print(f"  True High     {cm[2][0]:8d}  {cm[2][1]:8d}  {cm[2][2]:9d}")

    # 4. 5-Fold Stratified Cross Validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores_rf = cross_val_score(rf_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    cv_scores_xgb = cross_val_score(xgb_model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    print(f"\n5-Fold Cross Validation:")
    print(f"   • Random Forest CV:       {cv_scores_rf.mean()*100:.2f}% (± {cv_scores_rf.std()*100:.2f}%)")
    print(f"   • Gradient Boosting CV:   {cv_scores_xgb.mean()*100:.2f}% (± {cv_scores_xgb.std()*100:.2f}%)")

    # Feature Importances from Random Forest
    importances = rf_model.feature_importances_
    feat_imp = sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
    print("\nTop 7 Key Risk Drivers (Feature Importance):")
    for feat, imp in feat_imp[:7]:
        print(f"   • {feat:<22}: {imp*100:.2f}%")

    # Save models & metadata
    with open(RF_PATH, 'wb') as f:
        pickle.dump(rf_model, f)
    with open(XGB_PATH, 'wb') as f:
        pickle.dump(xgb_model, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    meta = {
        'model_name': 'Financial Risk Ensemble (XGBoost + Random Forest)',
        'accuracy': round(float(ens_acc) * 100, 2),
        'f1_score': round(float(ens_f1) * 100, 2),
        'rf_accuracy': round(float(rf_acc) * 100, 2),
        'xgb_accuracy': round(float(xgb_acc) * 100, 2),
        'feature_names': FEATURE_COLS,
        'feature_importances': {feat: round(float(imp) * 100, 2) for feat, imp in feat_imp},
        'target_classes': {0: 'Low Risk (Safe)', 1: 'Moderate Risk (Caution)', 2: 'High Risk (Critical)'},
        'weights': {'xgb': 0.55, 'rf': 0.45}
    }

    with open(META_PATH, 'w') as f:
        json.dump(meta, f, indent=2)

    print("\n" + "=" * 72)
    print("✓ Successfully saved model artifacts:")
    print(f"   • {os.path.basename(RF_PATH)}")
    print(f"   • {os.path.basename(XGB_PATH)}")
    print(f"   • {os.path.basename(SCALER_PATH)}")
    print(f"   • {os.path.basename(META_PATH)}")
    print("=" * 72)

if __name__ == '__main__':
    train_financial_risk_ensemble()
