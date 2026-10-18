# Daily cloud research

The [private GitHub Actions workflow](https://github.com/nikelef/venture-ai-ceo/actions/workflows/research.yml) runs daily at **05:23 UTC**. It also permits an owner-initiated dispatch on `main`. No push/PR/fork trigger runs the research job. Render separately deploys app source commits automatically.

This is the existing **research-only** pilot: it scores the dated register of ten opportunities and refreshes up to 18 public RSS signals. No LLM key, paid model, checkout, notification webhook, customer data or sales operation is configured. Fresh news is not buyer validation, and the dated vendor evidence does not become newly researched merely because a job ran again.

## What runs and persists

1. A standard `ubuntu-24.04` hosted runner checks out this private repository with read-only contents/actions permission and without persistent Git credentials. Official actions are pinned to verified commit SHAs. Python and product tests must pass first.
2. The cloud wrapper checks the repository, main branch, trigger, first attempt, shutdown flag and owner-confirmed zero-spend configuration before contacting services. It restores only the latest completed execution, never silently rolling back to an older successful artifact.
3. The official GitHub CLI retrieves private artifact metadata and the ZIP using the job's ephemeral token. The artifact digest, file whitelist, decompression/file-size limits, run/source provenance, database/report hashes, SQLite integrity and audit chain are checked. Path traversal, symlinks, unexpected customer/commerce files and lost/expired history stop execution.
4. The bounded worker runs once. Its daily run ceiling and failure circuit breaker persist across cloud executions. A verified database snapshot, source-only research report and manifest are retained as the private `venture-research-state` artifact for seven days. Nothing is written to the source repository or public site by the research job.

The job timeout is **three minutes**, with one shared concurrency group. The database cap is **2 MiB**, the report cap **500,000 bytes**, and the archive cap **4 MiB**. Artifacts exclude customer/payment records, API keys, runtime environment dumps and test commerce tables. No cache storage or custom/large runner is requested. Four research runs per UTC day and three consecutive failed runs are the worker's hard ceilings; manual dispatches also count. Old execution re-runs are rejected to prevent state rollback; a new reviewed dispatch is required.

## Verification evidence

| Execution | Outcome | State evidence |
|---|---|---|
| [39160638894](https://github.com/nikelef/venture-ai-ceo/actions/runs/39160638894) | Success; actual hosted tests, live feed retrieval and artifact upload | 9 audit events, 1 research run, 18 feed signals |
| [39160738590](https://github.com/nikelef/venture-ai-ceo/actions/runs/39160738590) | Success after one-time bootstrap was disabled | Restored run 39160638894; 18 audit events, 2 research runs, 18 feed signals |

Both used source `50853b5c788926e292c656792a411be3fdf1e6b6`. Downloaded snapshots passed hash and SQLite integrity checks. The second checkpoint audit digest is `b5b96e0479f7e8a24bf725ae2ff66cd10d8a4f3f6cd53fb79340f626cfe50dcd`. These observed runs were manual dispatches; the future scheduled trigger has not yet fired at this verification checkpoint. The schedule is active, and no laptop process is required.

## Budget and service behavior

The owner explicitly confirmed no payment method on both GitHub and Render. [GitHub Actions billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions) describes included standard-runner/storage allowances and blocking at quota without a valid payment method. GitHub Free currently includes 2,000 minutes/month and 500 MB shared artifact storage; other repositories consume the same account allowance. No paid plan was selected, and GitHub's billing details were not independently inspected. If payment settings change, review the guard before continuing. Do not automatically raise quotas, attach payment methods or upgrade plans.

[Render cron](https://render.com/docs/cronjobs) carries a minimum charge, so none was created. This workflow avoids pretending that a sleeping free web service is a durable scheduler. [GitHub schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) are best-effort and may be delayed/dropped under load. Quota exhaustion, account policy or failed/expired state can stop the pilot without charges; there is no uptime or delivery SLA.

## Shutdown and recovery

Repository variables are nonsecret operational switches:

- `VENTURE_RESEARCH_ENABLED=true`: set to `false` to stop allocating research jobs.
- `VENTURE_SHUTDOWN=false`: set to `true` to stop research inside an allocated job.
- `VENTURE_GITHUB_ZERO_SPEND_CONFIRMED=true`: records the owner's current billing safeguard confirmation. Removing it disables the job.
- `VENTURE_CLOUD_BOOTSTRAP_ALLOWED=false`: one-time initialization was revoked after the first successful run. Do not reenable merely to erase missing history, daily caps or failures.

Use the private workflow page for run logs, conclusions and artifacts. No normal owner notification or message is sent by application code; GitHub's existing account notification preferences may report workflow outcomes. No repository-wide notification preference was changed.

If no state artifact survives, if the latest run was cancelled/timed out, or if verification fails, the wrapper stops for recovery review instead of silently resetting its audit or budget state. Review the last private snapshot and external run history, restore only checked research state, and document any explicit recovery authority. The retained artifacts have immutable contents while present but may expire or be deleted by authorized administrators. They are not a permanent WORM archive or a production customer/order database.
