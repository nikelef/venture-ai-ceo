# Commerce implementation and blocked activation

No live checkout, orders, captured payments, refunds, payouts or revenue exist. The evaluator is local and free. There is no public webhook endpoint. `PAYMENTS_ENABLED=true` stops the pilot rather than enabling commerce. API keys cannot override the permission engine. No owner notification has been sent.

## Implemented and exercised locally

- A pure hosted-checkout request shape for a hypothetical EUR 9 test order. It does not create a Checkout Session. `create_hosted_checkout` is deliberately blocked, and the storefront contains no checkout control.
- Raw-body Stripe-style v1 signature verification with HMAC SHA-256, constant-time comparison, multiple signatures for rotation, a bounded request body/header, and a five-minute past/future timestamp tolerance. Synthetic tests cover signatures and replay. This is not evidence that a Stripe endpoint or account is configured.
- A separate, explicitly **test-only** order/event ledger with matching amount, currency, order and test-session references. Unpaid completion events cannot fulfill; a matching later asynchronous paid test event can. Live or missing-mode events are rejected.
- Persistent deduplication and idempotent fulfillment to an integrity-checked ZIP containing only original evaluator source. Receipt-like test artifacts are labeled as synthetic, never emailed and never counted as revenue. Replays return the existing artifact; tampering stops delivery.
- Integer-minor-unit reconciliation exercises with separate currencies, gross captured test amounts, refunds, processor fees and operating costs. Missing fee evidence leaves net unknown. Transfers, duplicate IDs, pending events and live data are rejected. This covers a small test subset, not a complete provider ledger, tax ledger or dispute processor.

## Prerequisites before any real payment

1. Confirm the lawful seller, business/tax arrangement, support channel, price/tax disclosures, product license, delivery promise and applicable consumer/refund/privacy requirements. The files ending `_DRAFT.md` require legal review; placeholders do not establish compliance.
2. The owner must complete identity, tax and payout setup directly with a licensed provider, such as [Stripe's official dashboard](https://dashboard.stripe.com/). Do not create a financial account, accept agreements, change payouts or request credentials or banking identifiers through this agent.
3. Separately authorize and verify the provider integration, costs and activation. Keep test/live credentials and storage separate. Create a hosted session with a server-controlled order/amount and idempotency key; never infer payment from a redirect or browser claim. No live transport currently exists.
4. Configure HTTPS webhooks and durable cloud storage/worker execution, then test actual provider-signed events through the endpoint. Independently retrieve the Checkout Session, PaymentIntent/charge and balance transactions; match provider references, status, amount, currency and order. Implement pagination, retries, event reordering, refunds, disputes, exchange rates and tax treatment without duplicate fulfillment.
5. Verify customer access to the deliverable, contact/support and refund path. External delivery and the licensed refund path are currently unconfigured. Test cloud restore, failure recovery, authorization, shutdown and privacy controls.
6. Emit a first normal owner notification only when a genuine live customer payment is independently confirmed captured/settled and matched to a delivered or fulfillable order. Record source IDs, timestamp and status; separate fees/refunds and avoid reporting incomplete net as verified. Synthetic fixtures, internal transfers and clicks cannot trigger it. Security/legal/budget alerts remain exceptions.

Implementation references checked on 2026-10-18: [Checkout session creation](https://docs.stripe.com/api/checkout/sessions/create), [webhook verification and retries](https://docs.stripe.com/events/manage-webhook-endpoints), [official Python signature implementation](https://github.com/stripe/stripe-python/blob/master/stripe/_webhook.py), and [balance transaction fields](https://docs.stripe.com/api/balance_transactions/object). These references establish protocol details, not this project's legal readiness or verified integration.
