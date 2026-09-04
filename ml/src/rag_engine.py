from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = BASE_DIR / "data" / "recovery_policy.md"


def load_knowledge_base():
    with open(KNOWLEDGE_BASE, "r", encoding="utf-8") as file:
        return file.read()


def chunk_text(text):
    """
    Split the knowledge base into logical sections.
    Each ## heading becomes one retrievable policy chunk.
    """

    sections = re.split(r"\n## ", text)

    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        if not section.startswith("#"):
            section = "## " + section

        chunks.append(section)

    return chunks


def normalize(text):
    """
    Normalize text for matching.
    """

    return re.sub(
        r"[^a-z0-9_ ]+",
        " ",
        text.lower()
    )


def extract_title(chunk):
    """
    Extract the Markdown section title.
    """

    match = re.search(
        r"^##\s+(.+)",
        chunk,
        re.MULTILINE
    )

    if match:
        return match.group(1).strip()

    return ""


def keyword_score(query, chunk):
    """
    Calculate relevance using weighted keyword matching.

    Specific payment-recovery concepts receive higher weights
    than generic words such as payment or recovery.
    """

    query_text = normalize(query)
    chunk_text_normalized = normalize(chunk)
    title = normalize(extract_title(chunk))

    query_words = set(query_text.split())
    chunk_words = set(chunk_text_normalized.split())
    title_words = set(title.split())

    score = 0.0

    # ---------------------------------------------------------
    # 1. Basic word overlap
    # ---------------------------------------------------------

    generic_words = {
        "payment",
        "recovery",
        "action",
        "customer",
        "event",
        "failure",
        "recommended",
        "model"
    }

    for word in query_words:

        if word in generic_words:
            weight = 0.5
        else:
            weight = 1.5

        if word in chunk_words:
            score += weight

        # Section titles are more important than body text
        if word in title_words:
            score += weight * 2.0

    # ---------------------------------------------------------
    # 2. Domain-specific concepts
    # ---------------------------------------------------------

    concept_groups = {

        "authentication": [
            "authentication",
            "authentication_failure",
            "auth"
        ],

        "payment_update": [
            "payment_update",
            "payment",
            "card",
            "payment_method",
            "change",
            "details"
        ],

        "subscription": [
            "subscription",
            "subscription_failure",
            "halted",
            "pending",
            "retry"
        ],

        "notification": [
            "notification",
            "notifications",
            "email",
            "sms",
            "customer_action"
        ],

        "webhook": [
            "webhook",
            "webhooks",
            "payment_failed",
            "events",
            "delivery",
            "exponential"
        ],

        "payment_link": [
            "payment_link",
            "payment_links",
            "expiry",
            "expired"
        ],

        "retry": [
            "retry",
            "attempt",
            "attempts",
            "temporary"
        ],

        "reminder": [
            "reminder",
            "customer_action",
            "notification"
        ],

        "offer": [
            "offer",
            "personalized"
        ]
    }

    for concept, terms in concept_groups.items():

        query_has_concept = any(
            term in query_text
            for term in terms
        )

        if not query_has_concept:
            continue

        matches = sum(
            1
            for term in terms
            if term in chunk_text_normalized
        )

        if matches:
            score += matches * 3.0

        # Stronger boost if the concept appears in the title
        title_matches = sum(
            1
            for term in terms
            if term in title
        )

        score += title_matches * 5.0

    return score


def retrieve(query, top_k=3):
    """
    Retrieve the most relevant policy sections.

    Retrieval uses weighted domain-aware relevance instead
    of simple raw word overlap.
    """

    text = load_knowledge_base()
    chunks = chunk_text(text)

    scored_chunks = []

    for chunk in chunks:

        score = keyword_score(
            query,
            chunk
        )

        if score > 0:
            scored_chunks.append(
                (score, chunk)
            )

    # Highest relevance first.
    # Original position is only used as a deterministic tie-breaker.
    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        chunk
        for score, chunk in scored_chunks[:top_k]
    ]


def generate_explanation(event, action, scores):
    """
    Generate a concise explanation using ML decision
    metrics plus retrieved policy context.
    """

    query = f"""
    event type: {event.get('event_type', '')}
    failure reason: {event.get('failure_reason', '')}
    payment method: {event.get('payment_method', '')}
    recommended action: {action}
    payment recovery
    """

    relevant_sections = retrieve(query)

    selected = scores[action]

    uplift = selected["uplift"]
    cost = selected["cost"]
    net_value = selected["net_value"]

    if action == "retry":
        action_reason = (
            "Retry is recommended because the model predicts "
            "positive incremental recovery from another payment attempt."
        )

    elif action == "payment_update":
        action_reason = (
            "Payment update is recommended because the model predicts "
            "higher incremental recovery from correcting the payment method."
        )

    elif action == "reminder":
        action_reason = (
            "Reminder is recommended because customer action may be "
            "needed to complete the payment."
        )

    elif action == "personalized_offer":
        action_reason = (
            "Personalized offer is recommended because the model predicts "
            "sufficient incremental recovery to justify the offer cost."
        )

    else:
        action_reason = (
            "No action is recommended because intervention does not "
            "provide positive incremental value."
        )

    explanation_text = (
        f"{action_reason} "
        f"The model estimates ₹{uplift:,.2f} incremental recovery "
        f"over no action, with an estimated cost of ₹{cost:,.2f}, "
        f"giving ₹{net_value:,.2f} net value."
    )

    return {
        "action": action,
        "explanation": explanation_text,
        "predicted_recovery": round(
            selected["predicted_recovery"],
            2
        ),
        "baseline_recovery": round(
            selected["baseline_recovery"],
            2
        ),
        "uplift": round(
            uplift,
            2
        ),
        "cost": round(
            cost,
            2
        ),
        "net_value": round(
            net_value,
            2
        ),
        "policy_context": relevant_sections
    }