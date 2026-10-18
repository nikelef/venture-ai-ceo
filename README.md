# Venture CEO — research-first, no-bank-access AI CEO starter

## What is implemented
A zero-outlay research pilot scores ten documented opportunities from a curated register of public sources, records assumptions and skeptical reviews, selects one concept plus two alternates, and writes a clearly labeled research page. It stores a local SQLite audit chain, limits daily executions, stops after repeated failures, verifies a backup, and supports a bounded scheduler and shutdown switch. Default execution makes no network or model requests. `--live-feeds` explicitly refreshes three allowlisted public RSS endpoints; refreshed news is not buyer validation.

The EUR 0 ceiling is enforced in code. Setting a model key or a nonzero budget environment variable does not authorize spending. Model calls, payments, notifications and external publishing are blocked in this pilot. The optional OpenAI-compatible request adapter exists behind that gate and has not been verified against a live provider. A local hash chain detects retained-chain changes; external immutable anchoring remains a future prerequisite.

**No paid sales or deployment are activated.** The more comprehensive implementation and operating rules are in `MASTER_PROMPT.md` for Codex to build. This is a research prototype, not a finished autonomous commercial business.

## Start with Codex on Windows — no separate repository instructions

After extracting this package into a **new, dedicated directory** (not inside an existing project), double-click `START_AI_CEO.cmd`. It launches the installed Codex CLI with instructions to read and execute the complete `MASTER_PROMPT.md` — including **creating your private** `nikelef/venture-ai-ceo` **GitHub repository automatically**, committing only safe source files, connecting that repo to Render where feasible, and implementing the sales and payment architecture.

You do **not** need to type GitHub setup instructions or create the repository manually. You may need to complete a GitHub browser sign-in, grant Render/GitHub integration permissions, and later complete payment processor identity/tax/payout onboarding using the provider's own secure portal. Codex cannot lawfully do those personal verification steps for you. No payment or revenue capability is live in the current starter package; the master prompt tells Codex to **build and verify it**, not pretend it already exists. Creating or paying for cloud resources still requires your express authorization.

## Run locally
Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate             # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env
python -m ai_ceo.worker
python -m ai_ceo.worker --health
python -m http.server 8000 --directory data/public
```

The research page will be at http://localhost:8000/ . No API key is needed for the default curated-evidence replay. The tool reads environment variables but intentionally does not load .env automatically. Keep optional provider credentials in environment variables or a deployment secret manager. Do not assume a proprietary provider supports an OpenAI-compatible API.

Run `python -m ai_ceo.scheduler --runs 2 --interval-seconds 3600` for a bounded foreground schedule. This does not install a cloud schedule. Stop with `AI_CEO_SHUTDOWN=true` or a `data/STOP` file; the scheduler checks at least once per second while waiting. Crashed in-progress runs require review rather than automatic duplicate execution. Local state and backups are private and ignored by Git.

For a credential-free dry run of output validation and HTML creation:

```bash
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

## Cloud and money prerequisites
To operate while the laptop is off, deploy the worker to **a cloud scheduler or a persistent background worker** with secure environment variables, durable storage and monitoring. A local run stops when the process/computer stops. A static landing page is not a business and cannot collect genuine revenue. Before enabling money flows, set up a legitimate legal/tax business arrangement as applicable, secure payment-processor onboarding, hosted checkout, signed webhooks, order fulfillment, refunds/privacy/support, real audit records and money alerts. The owner should enter payout details **inside the payment provider's secure portal**, not in chat, voice input, GitHub or prompt text.

Do not commit `.env` or generated customer data. Defaults to **zero authorized spend**, no checkout and no automated publishing. This reflects deliberate least-privilege design, not a claim of current launch.

Render's scheduled cron jobs are a suitable option once a deployable repository, service permissions, credentials and persistent state are arranged. Any Render services must use the specific workspace selected by the owner.
