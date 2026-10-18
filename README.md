# Venture CEO

Current demand experiment: a free local Shopify CSV checker with a proposed **EUR 9 agency handoff pack**, a worked public import checklist, and a prepared consented evidence collector. **Purchasing is unavailable. Measurement and registration are paused** pending the operator privacy contact and native authorization for collector-only secrets in Neon. No demand or revenue has been demonstrated. See [validation operations](docs/DEMAND_VALIDATION.md) and [market evidence](research/MARKET_VALIDATION.md).

A private, zero-outlay research pilot and a working browser-local catalog CSV evaluator. **The free evaluator is published and daily cloud research is enabled. No checkout, customer payment or revenue is active or verified.** Operating instructions remain in [MASTER_PROMPT.md](MASTER_PROMPT.md).

App: **https://venture-ai-ceo-evaluator.onrender.com**. Source: [nikelef/venture-ai-ceo](https://github.com/nikelef/venture-ai-ceo), private, default branch `main`. Render in the approved NE workspace successfully cloned this private repository and automatically deploys source commits. The owner confirmed no payment method on Render and GitHub. No existing unrelated service or billing setting was modified.

Cloud research runs daily at **05:23 UTC** through [GitHub Actions](https://github.com/nikelef/venture-ai-ceo/actions/workflows/research.yml). Two real cloud executions succeeded, including recovery of the prior private audit state; the future scheduled firing is not yet observed. See [cloud automation](docs/CLOUD_AUTOMATION.md) for verification, seven-day retention, quotas and shutdown.

## Run locally

Python 3.11+ is sufficient; the application has no third-party runtime dependencies. Node.js 24 was used for the browser-product tests. No API key, account signup or payment method is needed.

```powershell
python -m ai_ceo.worker
python -m ai_ceo.worker --health
python -m ai_ceo.server
```

The local evaluator is at **http://127.0.0.1:8000/** while the preview process runs. It serves only an allowlist of public assets. The conceptual research page is separately stored in `data/public/index.html`; it is not a shop. Stop the preview with Ctrl+C. No local process starts automatically; the cloud workflow is separate.

Default execution replays dated, curated public evidence and scores ten opportunities using the master prompt's weights. It selects a winner plus two alternates and preserves counterarguments, assumptions, provenance and confidence. It is not a fresh market scan or demand validation. Optional `python -m ai_ceo.worker --live-feeds` refreshes three allowlisted RSS endpoints; this does not refresh the vendor evidence or prove buying intent.

The evaluator checks UTF-8 comma-separated files locally in the browser: quoting, record shape, duplicate headings and a limited subset of Shopify catalog hints. It supports current/legacy heading aliases, handles image continuation rows, and downloads JSON diagnostics without source headings or cell values. It makes no upload, analytics or model requests. A clean report does not guarantee a successful import. It never modifies a store.

## Verify

```powershell
python -m unittest discover -s tests -v
node --test tests/catalog.test.cjs
python scripts/check_repository.py
```

Tests cover budget and permission denials, shutdown, execution caps, circuit breakers, local HTTP behavior, audit tampering/backups, CSV parsing/privacy/resource limits, synthetic webhook signatures, order matching, duplicate events, idempotent test fulfillment and separate-currency reconciliation. Payment fixtures are synthetic; passing them does not verify a live provider or sale. Local HTTP integration is tested; visual browser inspection was unavailable in this session.

## Budget, state and shutdown

- Authorized incremental operating outlay is **EUR 0**. Model calls, publishing, payments and owner notifications are denied. Setting keys, `PAYMENTS_ENABLED=true` or a larger budget in the environment does not grant authority.
- Four research runs per UTC day are the hard maximum. Three consecutive failed runs open the circuit breaker. Stale in-progress runs require review. Each run records evidence hashes and runtime cost scope; it does not estimate this Codex session's cost.
- Local state is SQLite in ignored `data/`, with append-only audit triggers, a hash chain and checked backups. Cloud research persists checked snapshots as private seven-day Actions artifacts. This is not a permanent immutable customer/order ledger. Private state and backups stay out of Git.
- `AI_CEO_SHUTDOWN=true` or `data/STOP` stops new research and local preview requests. The bounded scheduler checks during waits. Downloaded evaluator copies are independent files.

For a bounded foreground schedule:

```powershell
python -m ai_ceo.scheduler --runs 2 --interval-seconds 3600
```

This local scheduler runs only while its process and computer run. The separate daily GitHub Actions workflow works while the laptop is off; no local timer or always-on agent is installed.

The application reads process environment variables and does not load `.env` automatically. `.env.example` contains empty/example settings. Secrets belong in environment variables or a deployment secret manager. Never provide bank logins, authentication codes or payout details to this application or commit them to Git.

## Readiness and evidence

- [Research and skeptical selection](research/RESEARCH.md) and [source register](research/opportunities.json)
- [Deployment constraints and prepared Render configuration](docs/DEPLOYMENT.md)
- [Provider adapter and unverified integration limits](docs/PROVIDERS.md)
- [Commerce implementation and blocked activation](docs/COMMERCE_READINESS.md)
- [Current blockers and continuation work](docs/STATUS.md)
- [Privacy draft](docs/PRIVACY_DRAFT.md), [terms draft](docs/TERMS_DRAFT.md), [refunds draft](docs/REFUNDS_DRAFT.md) — all require legal review

The Render static evaluator is live from this repository only; `render.yaml` mirrors the intended configuration. With the owner-confirmed absence of payment methods, platform documentation describes quota blocking rather than paid overages. No Render paid cron, worker, database, domain or plan was enabled. Account billing changes require revisiting the safeguard.

Commerce components are **test-only**: signed synthetic events, a separate test ledger, a local deliverable ZIP and integer reconciliation exercises. Hosted checkout transport, onboarding, live payment verification, customer delivery, refunds, support, legal/tax readiness and verified-revenue notifications remain unconfigured. No test result is counted as revenue.
