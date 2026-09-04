# RecoveryOS Payment Recovery Knowledge Base

## Source Scope
This knowledge base is derived from official Razorpay documentation and is intended for RecoveryOS retrieval and explanation. It is not a universal payment-recovery policy and should not be presented as legal, financial, or merchant-specific policy.

---

## 1. Failed Payments and Webhooks

When a payment attempt fails, Razorpay records the payment as Failed. If the `payment.failed` webhook is enabled, Razorpay sends a notification to the configured endpoint. Businesses can then analyse the failure and notify the customer.

Important implementation note:
- Webhooks are asynchronous and near real-time.
- Business-critical synchronous use cases may use payment APIs for polling.
- A `payment.failed` webhook can sometimes be followed by a `payment.captured` webhook for the same transaction, including cases involving late authorisation or a customer retry.

RecoveryOS implication:
- A failed-payment event should not automatically be treated as permanently failed.
- The decision engine should consider retry timing and subsequent payment-state events.

Source:
https://razorpay.com/docs/webhooks/

---

## 2. Subscription Payment Failures

Razorpay Subscriptions can automatically retry failed recurring payments.

Documented failure scenarios include:
- Expired card
- Bank-blocked card
- Insufficient customer account balance
- Customer-cancelled mandate

For a failed subscription payment:
1. The Subscription moves to `pending`.
2. Razorpay notifies the merchant through relevant webhooks.
3. For card-based subscriptions, Razorpay automatically retries the payment on the following day.
4. In the documented T+3 retry model, retries occur on T+1, T+2 and T+3.
5. If retries are exhausted, the Subscription moves to `halted`.

When a customer changes the card while the subscription is in an applicable failed state, Razorpay can charge the new card; successful recovery can move the subscription back toward an active state.

RecoveryOS implication:
- Early subscription failures can justify a retry-oriented recovery action.
- Repeated failures should reduce the attractiveness of another retry.
- Card-update/payment-update messaging is relevant when the customer needs to change the payment method.
- The system should distinguish `pending` from `halted`.

Source:
https://razorpay.com/docs/payments/subscriptions/payment-retries/

---

## 3. Subscription Notifications

Razorpay supports Email, SMS and Webhook notifications for subscription events.

Customers may receive notifications for:
- Payment failures
- Required action after payment failure
- Card changes
- A subscription entering `halted` after retry attempts
- Successful charges and other subscription lifecycle events

RecoveryOS implication:
- A reminder or customer-action message can be appropriate when the payment failure requires customer intervention.
- Notification behaviour should be aligned with the current subscription state.

Source:
https://razorpay.com/docs/payments/subscriptions/notifications/

---

## 4. Payment Links

Razorpay Payment Links allow businesses to collect payments by sending a unique payment URL to customers through channels such as email or SMS.

Payment Links:
- Can be created from the Dashboard or APIs.
- Can be sent to customers through SMS/email.
- Can have an expiry date.
- Can be managed through APIs/Dashboard.
- Support webhook notifications for relevant events.

RecoveryOS implication:
- For an overdue invoice or payment that needs customer action, a payment-link-style recovery flow can be represented as a customer-facing recovery action.
- Expiry should be considered when designing reminder logic.

Source:
https://razorpay.com/docs/payments/payment-links/

---

## 5. Webhook Reliability

Razorpay webhook guidance states:
- Webhooks are asynchronous and near real-time.
- A non-2xx webhook response is treated as a delivery failure.
- Failed webhook deliveries are retried using an exponential backoff policy for 24 hours.
- Webhooks can be disabled if failures continue for the documented period.

RecoveryOS implication:
- RecoveryOS should treat webhook processing as an event-driven input.
- Production implementations should validate webhook requests and respond reliably.

Source:
https://razorpay.com/docs/webhooks/best-practices/

---

## 6. RecoveryOS Decision Guidance

The following rules are RecoveryOS design rules derived from the above documentation, not official Razorpay policies:

### Retry
Prefer a retry-oriented action when:
- The payment failure is recent.
- Retry attempts have not been exhausted.
- The failure is plausibly temporary.
- The event is a subscription payment in an eligible retry state.

### Payment Update
Prefer a payment-update action when:
- The customer likely needs to change card/payment details.
- Repeated retry attempts have failed.
- A subscription is in a state where customer payment-method correction is appropriate.

### Reminder
Prefer a reminder when:
- Customer action is required.
- A payment link or other payment-completion step needs attention.
- The event is old enough that an immediate retry is less appropriate.

### No Action
Use no action when:
- The expected incremental value of intervention is not positive after action cost.
- The event is outside the useful recovery window.
- Guardrails reject the available interventions.

### Personalized Offer
RecoveryOS treats personalized offers as an experimental business action. This is NOT an official Razorpay recovery recommendation. It should only be used when the ML model predicts sufficient incremental value and business guardrails permit it.

---

## 7. Guardrail Principles

RecoveryOS should:
- Limit repeated retry attempts.
- Avoid retrying indefinitely after repeated failures.
- Prefer customer payment-method correction when the failure indicates that correction is needed.
- Avoid economically irrational offers.
- Keep a clear distinction between ML recommendation and final guardrail-approved action.
- Treat the ML policy as a decision-support system rather than claiming that Razorpay officially recommends a particular action.

---

## Sources

1. Razorpay Docs — Webhooks
2. Razorpay Docs — Payment Retries
3. Razorpay Docs — Subscription Notifications
4. Razorpay Docs — Payment Links
5. Razorpay Docs — Webhooks Best Practices
