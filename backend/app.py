from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sys
import json
from datetime import datetime, timezone
from pathlib import Path



# =========================
# PROJECT PATHS
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ML_SRC = PROJECT_ROOT / "ml" / "src"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
AUDIT_LOG_PATH = PROJECT_ROOT / "backend" / "audit_log.json"

sys.path.insert(0, str(ML_SRC))


# =========================
# ML IMPORTS
# =========================

from decision_engine import choose_action
from rag_engine import generate_explanation


# =========================
# FASTAPI
# =========================

app = FastAPI(
    title="RecoveryOS API",
    description="ML-powered payment recovery decision engine",
    version="1.0.0"
)


# =========================
# REQUEST MODEL
# =========================

class RecoveryEvent(BaseModel):
    customer_age: int
    customer_tenure_days: int
    previous_transactions: int
    previous_success_rate: float
    previous_failures: int
    amount: float
    event_type: str
    payment_method: str
    failure_reason: str
    attempts: int
    hours_since_event: float
    checkout_intent: float
    engagement_score: float
    is_repeat_customer: int


# =========================
# API ROUTES
# =========================

@app.get("/api")
def api_root():
    return {
        "name": "RecoveryOS",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

def write_audit_log(event, ml_action, final_action,
                    guardrail_reason, escalation_required,
                    escalation_reason, decision):

    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "ml_action": ml_action,
        "final_action": final_action,
        "guardrail_reason": guardrail_reason,
        "escalation_required": escalation_required,
        "escalation_reason": escalation_reason,
        "decision": decision
    }

    if AUDIT_LOG_PATH.exists():
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as file:
            try:
                audit_log = json.load(file)
            except json.JSONDecodeError:
                audit_log = []
    else:
        audit_log = []

    audit_log.append(audit_entry)

    with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as file:
        json.dump(
            audit_log,
            file,
            indent=2,
            default=float
        )


@app.post("/predict")
def predict(event: RecoveryEvent):

    event_data = event.model_dump()

    final_action, ml_action, guardrail_reason, scores = choose_action(
        event_data
    )

    from guardrails import evaluate_escalation

    escalation_required, escalation_reason = evaluate_escalation(
        event_data,
        final_action,
        guardrail_reason
    )

    explanation = generate_explanation(
        event_data,
        final_action,
        scores
    )

    write_audit_log(
        event=event_data,
        ml_action=ml_action,
        final_action=final_action,
        guardrail_reason=guardrail_reason,
        escalation_required=escalation_required,
        escalation_reason=escalation_reason,
        decision=explanation
    )

    return {
        "recommended_action": final_action,
        "ml_action": ml_action,
        "guardrail_reason": guardrail_reason,
        "escalation_required": escalation_required,
        "escalation_reason": escalation_reason,
        "decision": explanation,
        "scores": scores
    }




# =========================
# FRONTEND
# =========================

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True
    ),
    name="frontend"
)