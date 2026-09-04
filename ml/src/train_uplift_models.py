import pandas as pd
import joblib

from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split


# ============================================================
# PATHS
# ============================================================

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


CATEGORICAL = [
    "event_type",
    "payment_method",
    "failure_reason"
]


NUMERICAL = [
    feature for feature in FEATURES
    if feature not in CATEGORICAL
]


# ============================================================
# MODEL
# ============================================================

def make_model():

    preprocessor = ColumnTransformer([
        (
            "num",
            "passthrough",
            NUMERICAL
        ),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            CATEGORICAL
        )
    ])

    model = Pipeline([
        (
            "preprocessor",
            preprocessor
        ),
        (
            "regressor",
            RandomForestRegressor(
                n_estimators=300,
                max_depth=16,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            )
        )
    ])

    return model


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42
)


print("\n========================================")
print("TRAINING UPLIFT / TREATMENT MODELS")
print("========================================")

print(f"Training rows: {len(train_df):,}")
print(f"Testing rows : {len(test_df):,}")


# ============================================================
# T-LEARNER
# ============================================================

models = {}

for action in ACTIONS:

    subset = train_df[
        train_df["action"] == action
    ].copy()

    X = subset[FEATURES]
    y = subset["recovered_amount"]

    model = make_model()

    print(
        f"{action:25s}"
        f" samples={len(subset):,}"
    )

    model.fit(X, y)

    models[action] = model


# ============================================================
# SAVE MODELS
# ============================================================

model_path = MODEL_DIR / "uplift_models.joblib"

joblib.dump(models, model_path)


# ============================================================
# COMPLETE
# ============================================================

print("\n========================================")
print("UPLIFT MODELS COMPLETE")
print("========================================")

print(f"Saved to: {model_path}")