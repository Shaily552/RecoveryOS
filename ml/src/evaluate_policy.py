import warnings
warnings.filterwarnings(
    "ignore",
    message="`sklearn.utils.parallel.delayed` should be used with `sklearn.utils.parallel.Parallel`"
)

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split


# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "revenue_events.csv"
MODEL_PATH = BASE_DIR / "models" / "uplift_models.joblib"
OUTPUT_PATH = BASE_DIR / "data" / "policy_evaluation.csv"


# =========================
# CONFIG
# =========================

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


# =========================
# LOAD DATA + MODELS
# =========================

df = pd.read_csv(DATA_PATH)
models = joblib.load(MODEL_PATH)

# Recreate the exact held-out test set
train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42
)

X_test = test_df[FEATURES]

print("=" * 50)
print("POLICY EVALUATION")
print("=" * 50)
print(f"Training rows: {len(train_df):,}")
print(f"Testing rows : {len(test_df):,}")


# =========================
# BULK ML PREDICTIONS
# =========================

print("\nGenerating predictions...")

predictions = {}

for action in ACTIONS:
    predictions[action] = models[action].predict(X_test)

baseline = predictions["no_action"]


# =========================
# ACTION COSTS
# =========================

amount = test_df["amount"].to_numpy()

costs = {
    "no_action": np.zeros(len(test_df)),
    "retry": np.full(len(test_df), 2.0),
    "payment_update": np.full(len(test_df), 1.0),
    "reminder": np.full(len(test_df), 1.0),
    "personalized_offer": 0.08 * amount
}


# =========================
# ML POLICY DECISION
# =========================

net_values = []

for action in ACTIONS:
    uplift = predictions[action] - baseline
    net = uplift - costs[action]
    net_values.append(net)

net_values = np.column_stack(net_values)

best_indices = np.argmax(net_values, axis=1)
ml_actions = np.array(ACTIONS)[best_indices]

ml_expected_values = net_values[
    np.arange(len(test_df)),
    best_indices
]


# =========================
# TRUE COUNTERFACTUAL VALUE
# =========================

true_recovery = np.column_stack([
    test_df[f"potential_{action}_recovery"].to_numpy()
    for action in ACTIONS
])

cost_matrix = np.column_stack([
    costs[action]
    for action in ACTIONS
])

true_net_values = true_recovery - cost_matrix

# Actual synthetic value of the action chosen by ML
ml_true_values = true_net_values[
    np.arange(len(test_df)),
    best_indices
]

# Best possible action using ground-truth counterfactuals
oracle_values = true_net_values.max(axis=1)


# =========================
# HISTORICAL POLICY VALUE
# =========================

historical_actions = test_df["action"].to_numpy()

historical_cost = np.zeros(len(test_df))

historical_cost[historical_actions == "retry"] = 2.0
historical_cost[historical_actions == "payment_update"] = 1.0
historical_cost[historical_actions == "reminder"] = 1.0
historical_cost[historical_actions == "personalized_offer"] = (
    0.08 * amount[historical_actions == "personalized_offer"]
)

historical_values = (
    test_df["recovered_amount"].to_numpy()
    - historical_cost
)


# =========================
# RESULTS
# =========================

historical_total = historical_values.sum()
ml_total = ml_true_values.sum()
oracle_total = oracle_values.sum()

improvement = ml_total - historical_total
oracle_gap = oracle_total - ml_total

print("\n" + "=" * 50)
print("RESULTS")
print("=" * 50)

print(f"Historical policy : ₹{historical_total:,.2f}")
print(f"ML policy         : ₹{ml_total:,.2f}")
print(f"Oracle policy     : ₹{oracle_total:,.2f}")

print(f"\nML improvement    : ₹{improvement:,.2f}")
print(f"Gap to oracle     : ₹{oracle_gap:,.2f}")

print("\nML action distribution:")
print(pd.Series(ml_actions).value_counts())


# =========================
# SAVE EVALUATION
# =========================

evaluation = test_df[
    ["event_type", "failure_reason", "amount", "action"]
].copy()

evaluation.rename(
    columns={"action": "historical_action"},
    inplace=True
)

evaluation["ml_action"] = ml_actions
evaluation["historical_net_value"] = historical_values
evaluation["ml_expected_net_value"] = ml_expected_values
evaluation["ml_true_net_value"] = ml_true_values
evaluation["oracle_net_value"] = oracle_values

evaluation.to_csv(OUTPUT_PATH, index=False)

print(f"\nSaved evaluation to:")
print(OUTPUT_PATH)

print("\nEvaluation complete.")