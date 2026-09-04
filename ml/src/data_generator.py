import numpy as np
import pandas as pd

np.random.seed(42)

N = 50000

# ============================================================
# 1. CUSTOMER / BEHAVIOURAL FEATURES
# ============================================================

customer_age = np.random.randint(18, 65, N)

customer_tenure_days = (
    np.random.exponential(500, N).astype(int) + 1
)

previous_transactions = np.random.poisson(12, N)

previous_success_rate = np.clip(
    np.random.beta(8, 2, N),
    0.05,
    0.99
)

previous_failures = np.maximum(
    np.round(
        previous_transactions * (1 - previous_success_rate)
    ),
    0
).astype(int)

checkout_intent = np.random.beta(6, 3, N)

engagement_score = np.random.beta(5, 3, N)

is_repeat_customer = (
    customer_tenure_days > 90
).astype(int)


# ============================================================
# 2. REVENUE EVENT
# ============================================================

amount = np.random.lognormal(
    mean=7.2,
    sigma=1.0,
    size=N
)

amount = np.clip(amount, 100, 100000)

amount = np.round(amount, 2)

event_type = np.random.choice(
    [
        "payment_failure",
        "checkout_abandonment",
        "subscription_failure",
        "overdue_invoice"
    ],
    N,
    p=[0.40, 0.25, 0.20, 0.15]
)

payment_method = np.random.choice(
    [
        "upi",
        "card",
        "netbanking",
        "wallet"
    ],
    N,
    p=[0.40, 0.35, 0.15, 0.10]
)

failure_reason = np.random.choice(
    [
        "insufficient_funds",
        "bank_decline",
        "expired_card",
        "technical_failure",
        "authentication_failure",
        "unknown"
    ],
    N
)

attempts = np.random.poisson(1.2, N)

hours_since_event = np.random.exponential(12, N)


# ============================================================
# 3. RECOVERY ACTIONS
# ============================================================

actions = [
    "no_action",
    "retry",
    "payment_update",
    "reminder",
    "personalized_offer"
]


# ============================================================
# 4. FUNCTION TO CALCULATE POTENTIAL RECOVERY
#
# This creates the "counterfactual world":
#
# What would happen if we chose each possible action?
# ============================================================

def calculate_recovery(
    action,
    amount,
    previous_success_rate,
    checkout_intent,
    engagement_score,
    attempts,
    hours_since_event,
    event_type,
    failure_reason,
    is_repeat_customer
):

    score = (
        1.6 * previous_success_rate
        + 1.1 * checkout_intent
        + 0.8 * engagement_score
        + 0.35 * is_repeat_customer
        - 0.25 * attempts
        - 0.12 * (hours_since_event / 24)
    )

    # --------------------------------------------------------
    # Action-specific intelligence
    # --------------------------------------------------------

    if action == "retry":

        score += 0.35

        score += 0.30 * (
            failure_reason == "technical_failure"
        )

        score += 0.20 * (
            payment_method == "upi"
        )

    elif action == "payment_update":

        score += 0.55

        score += 0.50 * (
            failure_reason == "expired_card"
        )

        score += 0.20 * (
            event_type == "subscription_failure"
        )

    elif action == "reminder":

        score += 0.30

        score += 0.35 * checkout_intent

        score += 0.20 * (
            event_type == "overdue_invoice"
        )

    elif action == "personalized_offer":

        score += 0.40

        score += 0.40 * engagement_score

        score += 0.30 * checkout_intent

    elif action == "no_action":

        score -= 0.15

    # --------------------------------------------------------
    # Convert score → probability
    # --------------------------------------------------------

    probability = 1 / (1 + np.exp(-(
        score - 2.0
    )))

    probability = np.clip(
        probability,
        0.01,
        0.99
    )

    # --------------------------------------------------------
    # Potential recovery amount
    # --------------------------------------------------------

    recovery_probability = probability

    expected_amount = (
        amount *
        recovery_probability *
        np.random.uniform(
            0.85,
            1.0,
            len(amount)
        )
    )

    return recovery_probability, expected_amount


# ============================================================
# 5. GENERATE COUNTERFACTUAL OUTCOMES
# ============================================================

potential_recoveries = {}

potential_probabilities = {}

for action in actions:

    probability, recovery = calculate_recovery(
        action,
        amount,
        previous_success_rate,
        checkout_intent,
        engagement_score,
        attempts,
        hours_since_event,
        event_type,
        failure_reason,
        is_repeat_customer
    )

    potential_probabilities[
        action
    ] = probability

    potential_recoveries[
        action
    ] = recovery


# ============================================================
# 6. OBSERVED ACTION
#
# In the real world, only ONE action happens.
# This creates the logged historical data.
# ============================================================

action = np.random.choice(
    actions,
    N,
    p=[
        0.15,
        0.25,
        0.20,
        0.25,
        0.15
    ]
)


# ============================================================
# 7. OBSERVED OUTCOME
# ============================================================

recovered = np.zeros(N, dtype=int)

recovered_amount = np.zeros(N)

observed_probability = np.zeros(N)

for current_action in actions:

    mask = action == current_action

    observed_probability[mask] = (
        potential_probabilities[current_action][mask]
    )

    recovered[mask] = (
        np.random.random(mask.sum())
        <
        potential_probabilities[current_action][mask]
    ).astype(int)

    recovered_amount[mask] = np.where(
        recovered[mask] == 1,
        potential_recoveries[current_action][mask],
        0
    )


# ============================================================
# 8. TIME TO RECOVERY
# ============================================================

time_to_recovery_hours = np.where(
    recovered == 1,
    np.random.exponential(10, N),
    np.nan
)


# ============================================================
# 9. COUNTERFACTUAL RECOVERY COLUMNS
#
# These are extremely important for our decision engine.
# ============================================================

counterfactual_columns = {}

for action_name in actions:

    safe_name = action_name.replace(
        "_",
        "_"
    )

    counterfactual_columns[
        f"potential_{safe_name}_recovery"
    ] = potential_recoveries[action_name]

    counterfactual_columns[
        f"potential_{safe_name}_probability"
    ] = potential_probabilities[action_name]


# ============================================================
# 10. FINAL DATAFRAME
# ============================================================

df = pd.DataFrame({

    "customer_age":
        customer_age,

    "customer_tenure_days":
        customer_tenure_days,

    "previous_transactions":
        previous_transactions,

    "previous_success_rate":
        previous_success_rate,

    "previous_failures":
        previous_failures,

    "amount":
        amount,

    "event_type":
        event_type,

    "payment_method":
        payment_method,

    "failure_reason":
        failure_reason,

    "attempts":
        attempts,

    "hours_since_event":
        hours_since_event,

    "checkout_intent":
        checkout_intent,

    "engagement_score":
        engagement_score,

    "is_repeat_customer":
        is_repeat_customer,

    "action":
        action,

    "recovered":
        recovered,

    "recovered_amount":
        recovered_amount,

    "time_to_recovery_hours":
        time_to_recovery_hours
})


# Add counterfactual information

for column_name, values in counterfactual_columns.items():

    df[column_name] = values


# ============================================================
# 11. SAVE DATASET
# ============================================================

output_path = "ml/data/revenue_events.csv"

df.to_csv(
    output_path,
    index=False
)


# ============================================================
# 12. REPORT
# ============================================================

print("\n========================================")
print("RECOVERYOS DATASET CREATED")
print("========================================")

print(f"Rows: {len(df):,}")

print(f"Columns: {len(df.columns)}")

print(
    f"Revenue at risk: ₹{df['amount'].sum():,.2f}"
)

print(
    f"Observed recovered revenue: "
    f"₹{df['recovered_amount'].sum():,.2f}"
)

print(
    f"Observed recovery rate: "
    f"{df['recovered'].mean():.2%}"
)

print("\nActions:")

print(
    df["action"].value_counts()
)

print("\nEvent types:")

print(
    df["event_type"].value_counts()
)

print("\nDataset saved to:")

print(output_path)

print("========================================")