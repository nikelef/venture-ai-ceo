# Venture CEO

A private, zero-outlay research pilot and a working local catalog CSV evaluator. **No business has launched, no checkout or cloud schedule is active, and no customer payment or revenue has been verified.** Operating instructions remain in [MASTER_PROMPT.md](MASTER_PROMPT.md).

The repository bootstrap was performed with GitHub CLI: [nikelef/venture-ai-ceo](https://github.com/nikelef/venture-ai-ceo), private, default branch `main`. Render account access works in the approved NE workspace. Deployment awaits verification of zero-charge usage safeguards and public operator/privacy readiness. No existing Render service has been modified.

## Run locally

Python 3.11+ is sufficient; the application has no third-party runtime dependencies. Node.js 24 was used for the browser-product tests. No API key, account signup or payment method is needed.

```powershell
python -m ai_ceo.worker
python -m ai_ceo.worker --health
python -m ai_ceo.server
```

The evaluator is at **http://127.0.0.1:8000/** while the preview process runs. It serves only an allowlist of public assets. The conceptual research page is separately stored in `data/public/index.html`; it is not a shop. Stop the preview with Ctrl+C. No process starts automatically.

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
- State is local SQLite in ignored `data/`, with append-only audit triggers, a hash chain and integrity-checked backups. This is not an externally immutable or cloud-backed ledger. Private state and backups stay out of Git.
- `AI_CEO_SHUTDOWN=true` or `data/STOP` stops new research and local preview requests. The bounded scheduler checks during waits. Downloaded evaluator copies are independent files.

For a bounded foreground schedule:

```powershell
python -m ai_ceo.scheduler --runs 2 --interval-seconds 3600
```

This runs only while that process and computer run. No cloud schedule, timer, background service or GitHub Actions workflow has been activated.

The application reads process environment variables and does not load `.env` automatically. `.env.example` contains empty/example settings. Secrets belong in environment variables or a deployment secret manager. Never provide bank logins, authentication codes or payout details to this application or commit them to Git.

## Readiness and evidence

- [Research and skeptical selection](research/RESEARCH.md) and [source register](research/opportunities.json)
- [Deployment constraints and prepared Render configuration](docs/DEPLOYMENT.md)
- [Provider adapter and unverified integration limits](docs/PROVIDERS.md)
- [Commerce implementation and blocked activation](docs/COMMERCE_READINESS.md)
- [Current blockers and continuation work](docs/STATUS.md)
- [Privacy draft](docs/PRIVACY_DRAFT.md), [terms draft](docs/TERMS_DRAFT.md), [refunds draft](docs/REFUNDS_DRAFT.md) — all require legal review

`render.yaml` prepares one static evaluator from this repository only. No deployment was performed. Render's current free hosting can incur usage overages, and its free service types do not include a durable worker/cron. The zero-outlay rule prevents activation until safeguards are verified.

Commerce components are **test-only**: signed synthetic events, a separate test ledger, a local deliverable ZIP and integer reconciliation exercises. Hosted checkout transport, onboarding, live payment verification, customer delivery, refunds, support, legal/tax readiness and verified-revenue notifications remain unconfigured. No test result is counted as revenue.
