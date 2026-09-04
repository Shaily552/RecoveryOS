# RecoveryOS

AI-powered payment recovery decision engine that predicts the highest-value recovery action while applying safety guardrails, policy intelligence, escalation rules, and audit logging.

## Problem

Failed payments create recoverable revenue loss, but applying the same recovery action to every customer is inefficient.

RecoveryOS evaluates each failed payment and chooses the recovery strategy with the highest expected incremental value.

## What RecoveryOS Does

For every payment failure, RecoveryOS:

1. Evaluates the customer and payment context.
2. Predicts expected recovery under multiple actions.
3. Estimates incremental recovery (uplift) over no action.
4. Subtracts the cost of each intervention.
5. Selects the action with the highest expected net value.
6. Applies business guardrails and stopping rules.
7. Escalates cases requiring manual review.
8. Retrieves relevant payment recovery guidance using RAG.
9. Generates an explanation for the decision.
10. Records the decision in an audit log.

## Recovery Actions

RecoveryOS evaluates five possible actions:

- No Action
- Retry
- Payment Update
- Reminder
- Personalized Offer

Personalized offers are treated as an experimental business action in this project and are not presented as an official Razorpay recommendation.

## Machine Learning

RecoveryOS uses a T-learner uplift modeling approach.

A separate Random Forest model is trained for each recovery action to estimate expected recovered amount.

The models are trained using randomized historical action assignments, allowing offline comparison of different recovery strategies.

### Decision Logic

For each action:

```text
Predicted Recovery
        ↓
Incremental Recovery (Uplift)
        ↓
Action Cost
        ↓
Expected Net Value
        ↓
Best Action
        ↓
Guardrails
        ↓
Final Action
```

## Offline Evaluation

RecoveryOS was evaluated on 10,000 held-out synthetic payment events.

| Policy | Recovery Value |
|---|---:|
| Historical Policy | ₹10.41M |
| RecoveryOS ML Policy | ₹14.90M |
| Oracle Policy | ₹15.75M |

### Results

- **₹14.90M** expected recovery under the RecoveryOS policy
- **₹4.49M improvement** over the historical policy
- **94.6% oracle coverage**

These results come from an offline evaluation on synthetic data. They should not be interpreted as production or real-world Razorpay revenue results.

## Guardrails & Escalation

RecoveryOS applies safety and business rules after ML policy selection.

Examples include:

- Preventing excessive retries
- Redirecting authentication failures toward payment updates
- Avoiding uneconomical offers for low-value transactions
- Preventing reminders for events outside the useful recovery window
- Prioritizing payment updates for certain subscription failure scenarios

Cases such as repeated payment failures can be escalated for manual review.

These guardrails and escalation rules are RecoveryOS design rules, not official Razorpay policies.

## Policy Intelligence / RAG

RecoveryOS includes a policy knowledge base derived from relevant Razorpay documentation.

The system retrieves relevant policy context and uses it to support decision explanations.

The retrieved knowledge base is intended for RecoveryOS explanation and retrieval, not as universal, legal, financial, or merchant-specific policy guidance.

## Audit Trail

Every prediction is recorded in `backend/audit_log.json`.

The audit record includes:

- Timestamp
- Input event
- ML recommendation
- Final action
- Guardrail decision
- Escalation status
- Escalation reason
- Decision metrics
- Retrieved policy context

The frontend also displays a concise decision audit trail for traceability.

## Project Structure

```text
RecoveryOS/
├── backend/
│   ├── app.py
│   └── audit_log.json
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── ml/
│   ├── data/
│   │   ├── policy_evaluation.csv
│   │   ├── recovery_policy.md
│   │   └── revenue_events.csv
│   │
│   ├── models/
│   │   ├── policy_value_models.joblib
│   │   ├── recovery_probability_model.joblib
│   │   └── uplift_models.joblib
│   │
│   └── src/
│       ├── data_generator.py
│       ├── decision_engine.py
│       ├── evaluate_policy.py
│       ├── guardrails.py
│       ├── rag_engine.py
│       ├── recovery_engine.py
│       ├── train_policy_model.py
│       ├── train_recovery_model.py
│       └── train_uplift_models.py
│
└── README.md
```
