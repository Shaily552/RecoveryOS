import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "revenue_events.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)

ACTIONS = [
    "no_action",
    "retry",
    "payment_update",
    "reminder",
    "personalized_offer"
]

FEATURES = [
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

# --------------------------------
# Create training target
# --------------------------------
# We train on OBSERVED recovery amount.
# Counterfactual columns are NOT features.

X_base = df[FEATURES].copy()

categorical = [
    "event_type",
    "payment_method",
    "failure_reason"
]

numerical = [
    x for x in FEATURES if x not in categorical
]

preprocessor = ColumnTransformer([
    ("num", "passthrough", numerical),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)
])

models = {}

# --------------------------------
# Train one value model per action
# --------------------------------

for action in ACTIONS:

    print(f"Training value model: {action}")

    subset = df[df["action"] == action].copy()

    X = subset[FEATURES]
    y = subset["recovered_amount"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=200,
            max_depth=14,
            min_samples_leaf=8,
            random_state=42,
            n_jobs=-1
        ))
    ])

    model.fit(X_train, y_train)

    models[action] = model

# --------------------------------
# Save
# --------------------------------

model_path = MODEL_DIR / "policy_value_models.joblib"

joblib.dump(models, model_path)

print("\n================================")
print("POLICY MODEL COMPLETE")
print("================================")
print(f"Saved to: {model_path}")