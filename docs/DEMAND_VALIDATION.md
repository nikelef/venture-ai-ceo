# Demand validation operations

The public free checker, proposed EUR 9 handoff offer and original guide can be deployed now. Personal registration and optional session measurement are **paused**, not operational. Do not call a disabled form a live signup funnel.

## Evidence collector prepared

- Dedicated Neon project `cool-firefly-02159743`, `venture-demand-validation`, Frankfurt, in connected organization `org-bold-glitter-92191180` (`Nikitas8`). The API confirmed organization plan `free` twice. No upgrade, payment method, subscription, Auth, AI Gateway or paid backup was enabled.
- Schema preparation branch `br-little-shadow-bac5g9ii` (`schema-v1`); clean experiment branch `br-polished-feather-ba3h1u8g` (`experiment-v1`) inherits the empty schema. No customer data was copied from another project.
- Three small tables: versioned consent/session flags, encrypted voluntary contacts/answers and admission limits. No catalog files, names, store URLs, payment data, IPs or user agents are stored by the app. Normal provider connection logs remain subject to provider policies. Retention runs before each consented admission and during daily aggregate reads.
- Application role `venture_collector`: verified non-superuser, no role/database creation, no inherited privileges; SELECT/INSERT/DELETE only on these three tables, plus column-limited UPDATE for session flags and admission counts. It cannot mark a buyer independently verified.
- Prepared function slug `evidence`, Node.js 24, pool maximum two, TLS `verify-full`, five-second database connection/query timeouts. No public function currently exists: `list_functions` returned an empty list after approval rejection.
- Bounds: 500 session admissions/day, 5,000 retained sessions, 500 registrations, 4 KiB request bodies, fixed fields and enums, no arbitrary upload endpoint. Identity ownership and independence are not inferred from email uniqueness. QA uses a separate secret and `test=true`, excluded from all aggregate queries.
- Added voluntary consent, no cookies/storage/fingerprinting, in-memory browser session, AES-256-GCM encrypted contact, keyed deduplication and random receipt for deletion. Browser samples cannot generate a completed real-file evaluation. Raw contact/report data never enters GitHub artifacts.
- App retention target 30 days, daily purge prepared in the aggregate check plus expiry on activity. Provider restore/log retention can differ. The currently paused system has no registrations. Do not promise a daily purge has executed before the monitor is actually activated and verified.

## Free-plan safeguards

Current primary references: [Neon plans](https://neon.com/docs/introduction/plans), [Neon pricing](https://neon.com/pricing), [Render free services](https://render.com/docs/free).

Neon Free has 100 CU-hours, 1 GB storage and 5 GB public network transfer per project, with hard suspension/failure at allowance exhaustion rather than automatic paid overages. Our additional project caps are 72,000 compute seconds, 100 MB egress and 100 MB logical database size; compute stays at 0.25 CU. The initial 20 MB optional storage cap blocked even schema creation. Automatic review first rejected the increase; after official free-plan limits and the account plan were reverified, a 100 MB cap was accepted. This changed an application cap below the existing 1 GB free allowance, not the billing plan.

No additional Render web service was created. Maritime-Carbon uses a free instance in the same workspace; a second Render instance would consume its shared 750 monthly free instance hours. Its service and database were not changed. The existing static site remains the frontend. Owner attestations of no payment method on Render/GitHub remain attestations, not independent billing access.

## Activation blockers and concrete owner decision

1. Supply the operator name and usable public privacy contact authorized for publication. The GitHub public profile currently supplies `Nikitas8` and no public email. [GDPR Article 13](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) requires controller identity/contact information. Consent must identify who receives the data; do not invent a company or publish inferred personal details. Owner input requested while independent work continued.
2. Automatic approval review rejected the Neon function deployment, stating that transmitting a database password, encryption key and access keys to Neon needs explicit authorization for that sensitive destination/payload. The retry after least-privilege and official deployment-environment verification was also rejected. **Do not retry, change tools or use automatically injected privileged credentials to bypass the rejection.**

The reviewable request is to deploy this isolated, initially paused function to the connected **Neon Free** project/branch above and put newly generated, collector-only values into Neon's documented deployment environment:

| Variable | Purpose / scope |
|---|---|
| `VALIDATION_DATABASE_URL` | Only `venture_collector` on this experiment's database, TLS verified |
| `CONTACT_ENCRYPTION_KEY` | Encrypt/de-duplicate the voluntary contact field |
| `VALIDATION_READ_KEY` | Read only aggregate summary through the API |
| `VALIDATION_QA_KEY` | Mark synthetic enrollment tests so they cannot count as demand |
| `VALIDATION_STOPPED=true` | Keep real collection paused through live QA |

These are generated application secrets, not GitHub/OAuth, Neon account API, bank or existing-project credentials. Temporary local secret material is removed while authorization is pending; generate new values for the approved deployment and set the dedicated role password then. Never print or commit them. A subsequent activation also needs authorization to put **only the aggregate read key** in this private repository's GitHub Actions secret `VENTURE_VALIDATION_READ_KEY`; no database password or contact-encryption key goes to GitHub. Native approvals must apply to the actual tool payload. No owner should paste a secret into chat.

After authorization: rebuild and hash the bundle, deploy paused, verify real health/CORS/SQL/receipt deletion using `test=true`, prove genuine metrics remain empty, then configure the exact endpoint and CSP. Confirm the public privacy notice and activate measurement/form only after both gates are met. Enable the guarded monitor and record actual activation time. Do not backdate activity.

## Automated monitoring prepared

`python -m ai_ceo.validation` accepts a verified HTTPS Neon `/summary` URL and aggregate read key through environment variables. It refuses redirects, validates bounded count/source fields, excludes all contact data from output, writes only `runtime/validation-artifact/summary.json`, and never infers genuine unique people from sessions. The workflow job stays gated off until activation. A missing endpoint or failing check is a blocker, not evidence of no visitors or rejected demand.

Local tests: `python scripts/run_tests.py`; `node --test --test-isolation=none tests/catalog.test.cjs tests/demand.test.mjs`. The Windows test runner creates only synthetic fixtures with inherited workspace permissions to avoid private temporary-directory ACL failures. Windows sandbox blocks Node child-process spawning, so local Node tests use no process isolation. Linux CI uses normal test isolation. Dependencies were downloaded from the official npm registry with integrity verification; lifecycle scripts were not run locally. Hosted CI then completed a clean install, all 67 tests, the production dependency audit (zero reported vulnerabilities) and the bundle build. **Live collector integration remains unverified.**

## Decisions and distribution

See [market evidence](../research/MARKET_VALIDATION.md), [experiment protocol](../research/experiments/agency-handoff-v1.json) and [permitted channels](../research/DISTRIBUTION.md). The free checker is already functional. The proposed paid pack is not sold. Initial targets are 100 genuine relevant visitors, 10 completed real evaluations, five qualified voluntary pilots and three independent buyers explicitly willing to pay EUR 9. Candidate sessions, unverified email forms, competitor reviews and test fixtures cannot satisfy those claims automatically.

Until qualified exposure exists, the decision is **distribution unresolved**, with collection currently blocked. Do not expand product scope, activate payments, report hypothetical revenue or silently pivot because a new site has no measured traffic.
