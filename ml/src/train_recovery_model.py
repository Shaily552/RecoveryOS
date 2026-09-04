import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, mean_absolute_error
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# -----------------------------
# 1. LOAD DATA
# -----------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "revenue_events.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)

# -----------------------------
# 2. FEATURES
# -----------------------------

features = [
    "customer_age",
    "customer_tenure_days",
    "previous_transactions",
    "previous_success_rate",
    "previous_failures",
    "amount",
    "event_type",
    "payment_method",
    "failure_reason",
    "attempts",
    "hours_since_event",
    "checkout_intent",
    "engagement_score",
    "is_repeat_customer"
]

X = df[features]

# Target: whether revenue was recovered
y = df["recovered"]

categorical = [
    "event_type",
    "payment_method",
    "failure_reason"
]

numerical = [
    col for col in features
    if col not in categorical
]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)
    ]
)

# -----------------------------
# 3. TRAIN RECOVERY MODEL
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        max_depth=14,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    ))
])

print("Training recovery model...")

model.fit(X_train, y_train)

# -----------------------------
# 4. EVALUATE
# -----------------------------

pred_prob = model.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, pred_prob)

print("\n================================")
print("RECOVERY MODEL RESULTS")
print("================================")
print(f"ROC-AUC: {auc:.4f}")

# -----------------------------
# 5. SAVE MODEL
# -----------------------------

import joblib

model_path = MODEL_DIR / "recovery_probability_model.joblib"

joblib.dump(model, model_path)

print(f"\nModel saved to:")
print(model_path)