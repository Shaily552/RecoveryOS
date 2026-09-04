const form = document.getElementById("recoveryForm");
const results = document.getElementById("results");


form.addEventListener("submit", async function (event) {

    event.preventDefault();

    const button = form.querySelector("button");
    button.textContent = "Analyzing...";
    button.disabled = true;

    const data = {
        customer_age: Number(document.getElementById("customer_age").value),
        customer_tenure_days: Number(document.getElementById("customer_tenure_days").value),
        previous_transactions: Number(document.getElementById("previous_transactions").value),
        previous_success_rate: Number(document.getElementById("previous_success_rate").value),
        previous_failures: Number(document.getElementById("previous_failures").value),
        amount: Number(document.getElementById("amount").value),

        event_type: document.getElementById("event_type").value,
        payment_method: document.getElementById("payment_method").value,
        failure_reason: document.getElementById("failure_reason").value,

        attempts: Number(document.getElementById("attempts").value),
        hours_since_event: Number(document.getElementById("hours_since_event").value),
        checkout_intent: Number(document.getElementById("checkout_intent").value),
        engagement_score: Number(document.getElementById("engagement_score").value),
        is_repeat_customer: Number(
            document.getElementById("is_repeat_customer").value
        )
    };


    try {

        const response = await fetch(
            "/predict",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            }
        );


        if (!response.ok) {
            throw new Error("API request failed");
        }


        const result = await response.json();

        displayResult(result);

    } catch (error) {

        alert(
            "Could not connect to RecoveryOS API.\n\n" +
            "Make sure the backend server is running."
        );

        console.error(error);

    } finally {

        button.textContent = "Analyze Recovery Opportunity";
        button.disabled = false;
    }
});


function formatCurrency(value) {

    return "₹" + Number(value).toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );
}


function formatAction(action) {

    return action
        .replaceAll("_", " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}


function displayResult(result) {

    const decision = result.decision;


    // =========================
    // MAIN RECOMMENDATION
    // =========================

    document.getElementById("recommendedAction").textContent =
        formatAction(result.recommended_action);


    document.getElementById("guardrailReason").textContent =
        result.guardrail_reason;


    document.getElementById("netValue").textContent =
        formatCurrency(decision.net_value);


    // =========================
    // METRICS
    // =========================

    document.getElementById("predictedRecovery").textContent =
        formatCurrency(decision.predicted_recovery);


    document.getElementById("baselineRecovery").textContent =
        formatCurrency(decision.baseline_recovery);


    document.getElementById("uplift").textContent =
        formatCurrency(decision.uplift);


    document.getElementById("actionCost").textContent =
        formatCurrency(decision.cost);


    // =========================
    // AI EXPLANATION
    // =========================

    document.getElementById("explanation").textContent =
        decision.explanation;


    // =========================
    // GUARDRAIL STATUS
    // =========================

 const guardrailStatus =
    document.getElementById("guardrailStatus");

if (result.escalation_required) {

    guardrailStatus.textContent =
        "Review Required";

} else if (result.ml_action !== result.recommended_action) {

    guardrailStatus.textContent =
        "Action Adjusted";

} else {

    guardrailStatus.textContent =
        "Action Approved";
}

      // =========================
    // ESCALATION STATUS
    // =========================

    const escalationPanel =
        document.getElementById("escalationPanel");

    const escalationStatus =
        document.getElementById("escalationStatus");

    const escalationReason =
        document.getElementById("escalationReason");


    if (result.escalation_required) {

        escalationPanel.className =
            "escalation-panel requires-review";

        escalationStatus.textContent =
            "Manual Review Required";

        escalationReason.textContent =
            result.escalation_reason;

    } else {

        escalationPanel.className =
            "escalation-panel no-escalation";

        escalationStatus.textContent =
            "No Escalation Required";

        escalationReason.textContent =
            "No escalation required";
    }

        // =========================
    // AUDIT TRAIL
    // =========================

    document.getElementById("auditTimestamp").textContent =
        new Date().toLocaleString("en-IN", {
            dateStyle: "medium",
            timeStyle: "short"
        });

    document.getElementById("auditMLAction").textContent =
        formatAction(result.ml_action);

    document.getElementById("auditFinalAction").textContent =
        formatAction(result.recommended_action);

    document.getElementById("auditEscalation").textContent =
        result.escalation_required
            ? "Manual Review Required"
            : "No Escalation";


                document.getElementById("auditGuardrail").textContent =
        result.guardrail_reason;

    document.getElementById("auditNetValue").textContent =
        formatCurrency(decision.net_value);
    // =========================
    // ACTION COMPARISON
    // =========================

    const comparison =
        document.getElementById("actionComparison");

    comparison.innerHTML = "";


    const scores = result.scores;

    const values = Object.values(scores).map(
        score => Number(score.net_value)
    );

    const maxValue = Math.max(
        ...values,
        1
    );


    Object.entries(scores).forEach(
        ([action, score]) => {

            const row =
                document.createElement("div");

            row.className = "action-row";


            const header =
                document.createElement("div");

            header.className = "action-header";


            const name =
                document.createElement("span");

            name.className = "action-name";

            name.textContent =
                formatAction(action);


            const value =
                document.createElement("span");

            value.className = "action-value";

            value.textContent =
                formatCurrency(score.net_value);


            header.appendChild(name);
            header.appendChild(value);


            const bar =
                document.createElement("div");

            bar.className = "action-bar";


            const fill =
                document.createElement("div");

            fill.className = "action-fill";


            const percentage =
                Math.max(
                    0,
                    (Number(score.net_value) / maxValue) * 100
                );


            fill.style.width =
                percentage + "%";


            if (
                action === result.recommended_action
            ) {

                fill.style.background =
                    "#16a34a";

            }


            bar.appendChild(fill);

            row.appendChild(header);
            row.appendChild(bar);

            comparison.appendChild(row);
        }
    );


    // =========================
    // POLICY CONTEXT
    // =========================

    const policyContainer =
        document.getElementById("policyContext");

    policyContainer.innerHTML = "";

    const policySections =
        decision.policy_context || [];


    policySections.forEach((section, index) => {

        const item =
            document.createElement("div");

        item.className =
            "policy-item";


        const lines = section
            .split("\n")
            .map(line => line.trim())
            .filter(line => line.length > 0);


        let title =
            `Policy Reference ${index + 1}`;

        let content = [];


        lines.forEach(line => {

            if (line.startsWith("## ")) {

                title =
                    line
                        .replace(/^## /, "")
                        .trim();

            }

            else if (
                !line.startsWith("#") &&
                !line.startsWith("---") &&
                !line.startsWith("Source:") &&
                !line.startsWith("http")
            ) {

                content.push(
                    line
                        .replace(/^### /, "")
                        .replace(/^- /, "• ")
                        .replace(/`/g, "")
                );
            }
        });


        const badge =
            document.createElement("div");

        badge.className =
            "policy-badge";

        badge.textContent =
            `Retrieved #${index + 1}`;


        const heading =
            document.createElement("div");

        heading.className =
            "policy-title";

        heading.textContent =
            title;


        const body =
            document.createElement("div");

        body.className =
            "policy-body";


        body.textContent =
            content
                .slice(0, 8)
                .join("\n");


        item.appendChild(badge);
        item.appendChild(heading);
        item.appendChild(body);

        policyContainer.appendChild(item);
    });


    // =========================
    // SHOW RESULTS
    // =========================

    results.classList.remove("hidden");

    results.scrollIntoView({
        behavior: "smooth"
    });
}