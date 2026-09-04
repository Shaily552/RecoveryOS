import pandas as pd
import joblib
from pathlib import Path

from guardrails import apply_guardrails


BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = BASE_DIR / "models" / "uplift_models.joblib"
DATA_PATH = BASE_DIR / "data" / "revenue_events.csv"

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


models = joblib.load(MODEL_PATH)
df = pd.read_csv(DATA_PATH)


def action_cost(action, amount):
    if action == "no_action":
        return 0.0
    if action == "retry":
        return 2.0
    if action == "payment_update":
        return 1.0
    if action == "reminder":
        return 1.0
    if action == "personalized_offer":
        return 0.08 * amount


def choose_action(event):

    X = pd.DataFrame([event])[FEATURES]

    predicted_recovery = {}

    # Predict recovery under every possible action
    for action in ACTIONS:
        predicted_recovery[action] = models[action].predict(X)[0]

    # No-action is the baseline
    baseline = predicted_recovery["no_action"]

    scores = {}

    # Calculate uplift and net value
    for action in ACTIONS:

        uplift = predicted_recovery[action] - baseline

        cost = action_cost(
            action,
            event["amount"]
        )

        net_value = uplift - cost

        scores[action] = {
            "predicted_recovery": predicted_recovery[action],
            "baseline_recovery": baseline,
            "uplift": uplift,
            "cost": cost,
            "net_value": net_value
        }

    # ML recommendation
    ml_action = max(
        scores,
        key=lambda action: scores[action]["net_value"]
    )

    # Apply business guardrails
    final_action, guardrail_reason = apply_guardrails(
        event,
        ml_action
    )

    return final_action, ml_action, guardrail_reason, scores


if __name__ == "__main__":

    print("\n========================================")
    print("RECOVERYOS DECISION ENGINE")
    print("========================================")

    for i in range(5):

        event = df.iloc[i].to_dict()

        final_action, ml_action, reason, scores = choose_action(event)

        print(f"\nEvent #{i + 1}")
        print(f"Event type : {event['event_type']}")
        print(f"Amount     : ₹{event['amount']:,.2f}")
        print(f"Reason     : {event['failure_reason']}")

        print(f"\nML recommendation : {ml_action}")
        print(f"Final action      : {final_action}")
        print(f"Guardrail result  : {reason}")

        print("\nDecision scores:")

        for action in ACTIONS:

            s = scores[action]

            print(
                f"{action:25s}"
                f" recovery=₹{s['predicted_recovery']:,.2f}"
                f" uplift=₹{s['uplift']:,.2f}"
                f" cost=₹{s['cost']:,.2f}"
                f" net=₹{s['net_value']:,.2f}"
            )