"""
RecoveryOS - Guardrails

Safety, business rules, and escalation rules applied
after ML policy selection.
"""

ACTIONS = [
    "no_action",
    "retry",
    "payment_update",
    "reminder",
    "personalized_offer"
]


def apply_guardrails(event, recommended_action):
    """
    Validate and adjust the ML recommendation using business rules.

    Returns:
        final_action, reason
    """

    amount = float(event.get("amount", 0))
    attempts = int(event.get("attempts", 0))
    hours_since_event = float(event.get("hours_since_event", 0))
    failure_reason = str(
        event.get("failure_reason", "")
    ).lower()
    event_type = str(
        event.get("event_type", "")
    ).lower()

    # 1. Never retry too many times
    if recommended_action == "retry" and attempts >= 3:
        return "payment_update", "Retry limit reached"

    # 2. Avoid retry for authentication failures
    if (
        recommended_action == "retry"
        and "authentication" in failure_reason
    ):
        return (
            "payment_update",
            "Authentication failure requires payment update"
        )

    # 3. Avoid offers for very small transactions
    if (
        recommended_action == "personalized_offer"
        and amount < 100
    ):
        return (
            "reminder",
            "Offer not economical for low-value transaction"
        )

    # 4. Avoid repeated reminders after a long delay
    if (
        recommended_action == "reminder"
        and hours_since_event > 72
    ):
        return (
            "no_action",
            "Event is too old for reminder"
        )

    # 5. Subscription failures should prioritize payment update
    if (
        recommended_action == "retry"
        and event_type == "subscription_failure"
    ):
        return (
            "payment_update",
            "Subscription failure requires payment update"
        )

    # 6. Invalid action fallback
    if recommended_action not in ACTIONS:
        return (
            "no_action",
            "Invalid recommendation"
        )

    return (
        recommended_action,
        "Approved by guardrails"
    )


def evaluate_escalation(event, final_action, guardrail_reason):
    """
    Determine whether the case should be escalated
    to manual review.

    These are RecoveryOS safety/business rules,
    not official Razorpay policies.

    Returns:
        escalation_required, escalation_reason
    """

    attempts = int(
        event.get("attempts", 0)
    )

    hours_since_event = float(
        event.get("hours_since_event", 0)
    )

    failure_reason = str(
        event.get("failure_reason", "")
    ).lower()

    # --------------------------------------------------
    # 1. Repeated payment failures
    # --------------------------------------------------

    if attempts >= 3:
        return (
            True,
            "Repeated payment failures require manual review"
        )

    # --------------------------------------------------
    # 2. Event outside automated recovery window
    # --------------------------------------------------

    if hours_since_event > 72:
        return (
            True,
            "Event is outside the automated recovery window"
        )

    # --------------------------------------------------
    # 3. Authentication issue after repeated attempts
    # --------------------------------------------------

    if (
        "authentication" in failure_reason
        and attempts >= 2
    ):
        return (
            True,
            "Repeated authentication failures require manual review"
        )

    # --------------------------------------------------
    # 4. No safe automated intervention
    # --------------------------------------------------

    if (
        final_action == "no_action"
        and guardrail_reason != "Approved by guardrails"
    ):
        return (
            True,
            "No safe automated intervention is available"
        )

    return (
        False,
        "No escalation required"
    )


if __name__ == "__main__":

    test_event = {
        "amount": 500,
        "attempts": 4,
        "hours_since_event": 2,
        "failure_reason": "authentication_failure",
        "event_type": "payment_failure"
    }

    ml_action = "retry"

    final_action, reason = apply_guardrails(
        test_event,
        ml_action
    )

    escalation, escalation_reason = evaluate_escalation(
        test_event,
        final_action,
        reason
    )

    print("========================================")
    print("RECOVERYOS GUARDRAIL TEST")
    print("========================================")

    print("ML recommendation :", ml_action)
    print("Final action      :", final_action)
    print("Guardrail result  :", reason)
    print("Escalation        :", escalation)
    print("Escalation reason :", escalation_reason)