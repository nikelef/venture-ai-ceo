# Deployment and activation record

Repository: https://github.com/nikelef/venture-ai-ceo — private, owner `nikelef`, default branch `main`. Created and pushed with GitHub CLI on 2026-10-18. GitHub CLI uses the OS secure credential store. The official portable CLI is local in ignored `.tools/`; do not commit it or its authentication state.

Render access was verified with a read-only service listing in owner-approved workspace **NE** (`tea-db494dlg1s2s738mef60`). No resource, environment variable, deployment, domain or billing setting was changed. The existing Maritime-Carbon service is outside this project and must remain untouched. Access to the account does not establish that Render's GitHub App can clone the new private repository.

## Why deployment remains blocked

The authorized outlay is EUR 0. Current [Render free-instance documentation](https://render.com/docs/free) and [static-site documentation](https://render.com/docs/static-sites), retrieved on 2026-10-18, state that static sites consume included bandwidth and pipeline minutes. Supplementary usage may be billed. The available connector cannot prove that this workspace has no payment method or enforce a zero-charge bandwidth/build safeguard. Do not infer it from a `free` label, and do not change shared workspace billing settings affecting other services.

Render's free service types do not include a persistent worker or cron job. Free web services sleep, have ephemeral local state and cannot substitute for a verified durable scheduler. Free Postgres expires and is unsuitable for the required ongoing order/audit persistence. No chargeable worker, cron, database, disk or keep-alive workaround has been provisioned.

The local preview also contains a readiness notice requiring operator/hosting privacy review. A complete legal/tax identity, payment provider and support channel are not configured.

## Prepared static evaluator

`render.yaml` defines exactly one new static service using **only** this repository and publishing **only** `web/`. Auto-deployment is off. No paid compute plan, domain, datastore or scheduler is included. Its build runs the product tests. Committing the file does not deploy it. It contains no secrets. Current schema validation checks structure, not account permission or billing readiness. The Render CLI is not installed, so platform-aware `render blueprints validate render.yaml` validation has not been run.

After secure billing safeguards and the public notice have been verified, use the official [Blueprint creation flow](https://dashboard.render.com/blueprint/new?repo=https://github.com/nikelef/venture-ai-ceo) in workspace NE. If the repository is unavailable, the owner must use Render's official GitHub connection/installation consent flow and grant access only to `venture-ai-ceo`. Do not install an App broadly across unrelated repositories. Do not ask for tokens in chat. Inspect the exact one-service configuration and confirm no new charge or agreement before applying. The agent should execute the available deployment tools itself once these prerequisites are satisfied.

After creation, verify a terminal successful deploy, actual `onrender.com` URL, TLS, static assets and response headers; confirm CSV reports on synthetic inputs, disabled payment/upload routes, and absence of private paths. Record the service/deploy IDs and the exact deployed commit. Do not claim deployment, GitHub linking or scheduled operation before those checks succeed.

## Scheduler and durable state

`python -m ai_ceo.scheduler --runs 2 --interval-seconds 3600` executes a bounded foreground schedule. It has no installed timer and stops when its process or machine stops. Four research runs per UTC day are the hard maximum; three consecutive failed runs open the circuit breaker. It stops on the first scheduler error and checks shutdown during waits. Review a stale in-progress run before recovering it; do not erase audit history to bypass limits.

The local SQLite database uses atomic run reservations and a hash-chained append-only event API. Backups are checked with SQLite's integrity check. Keep backups outside ephemeral cloud storage before any cloud activation; they currently exist only on the laptop. An external immutable audit anchor and durable cloud database remain unconfigured. PostgreSQL migration, concurrency review, backup restore and durable scheduler execution must pass before live commerce. Neither a file in Git nor a configured command proves that a cloud worker ran.

No GitHub Actions workflow is activated: private-repository runner allowances and overage controls have not been verified. No notifications, email, posts, analytics or outreach have been sent.
