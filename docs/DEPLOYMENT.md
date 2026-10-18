# Deployment record — 2026-10-18

The evaluator is published at **https://venture-ai-ceo-evaluator.onrender.com**.

| Setting | Verified value |
|---|---|
| Render workspace | Owner-approved NE (`tea-db494dlg1s2s738mef60`) |
| Service | `venture-ai-ceo-evaluator`, `srv-dbai14uq1p3s73bokg0g` |
| Type | Static site, with no compute plan, database, disk or paid cron |
| Private source | `https://github.com/nikelef/venture-ai-ceo`, branch `main` |
| Build | `node --test tests/catalog.test.cjs` |
| Published directory | `web/` only |
| Dependency installation | `SKIP_INSTALL_DEPS=true` |
| Automatic deployment | Enabled on source commits |

The owner explicitly confirmed that Render has no payment method and authorized publication. Current [Render free-tier documentation](https://render.com/docs/free) describes suspension/build blocking at included-usage limits without a payment method. That owner confirmation is the evidence about account billing; the connector does not expose payment-method details, so no independent inspection of those details is claimed. No payment method, budget, agreement, subscription or paid resource was added. If account billing changes, revisit the zero-outlay safeguard before continuing automation.

## Deployment evidence

Initial deploy `dep-dbai156q1p3s73bokh90` reached `live` on source `1e5de9326203bcf96a3161a5c0bb5271db518c31`. Successful cloning/building from this private repository independently established that Render's existing GitHub integration could access it; no new installation consent was needed.

Source commits subsequently triggered automatic deployments. Deploy `dep-dbai5tivcj2c73a98tjg` reached `live` on `50853b5c788926e292c656792a411be3fdf1e6b6` with trigger `new_commit`. Later documentation commits can replace that revision; check the latest service deploy instead of treating this historical checkpoint as permanently current.

HTTPS requests returned the expected evaluator, scripts, stylesheet, privacy notice and robots file. Downloaded public assets matched their source SHA-256 hashes. `.env`, `.git/config`, `data/decision.json` and `MASTER_PROMPT.md` returned 404. `/health.json` reports the static evaluator configuration with payments, uploads and model requests disabled. A static health document is not evidence of a running backend worker.

The public prototype notice identifies Render hosting and the public project maintainer, describes browser-local CSV handling and distinguishes the free evaluator from commercial readiness. No checkout, accounts, analytics, uploads or transactions are available. Commercial privacy/terms/refund templates still require review before sales.

The service was created directly through the Render connector. `render.yaml` mirrors the intended one-service configuration and passes the published schema; it is not an applied Blueprint and its additional header rules are not claimed as installed by the subset creation tool. The HTML itself contains a restrictive CSP. Do not blindly apply a second Blueprint or create a duplicate service.

## Automation and limits

Research runs in the private repository's [daily GitHub Actions workflow](https://github.com/nikelef/venture-ai-ceo/actions/workflows/research.yml), with verified cloud executions and private state recovery. See [cloud automation](CLOUD_AUTOMATION.md) for the exact evidence, schedule, safeguards and shutdown controls. No Render paid cron or keep-alive workaround is used; Render documents a minimum monthly charge for cron jobs.

The existing Maritime-Carbon service is unrelated and was not modified. No workspace-wide billing, environment, domain or integration settings were changed. The GitHub repository remains private; only the evaluator assets are public.
