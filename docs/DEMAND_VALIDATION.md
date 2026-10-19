# Demand validation operations

The public free checker and proposed EUR 9 offer remain live. Owner identity and scoped Neon authorization are resolved, and the collector passed live QA while stopped. Registration/measurement are paused until final public and monitor activation checks below complete.

## Evidence collector prepared

- Dedicated Neon project `cool-firefly-02159743`, `venture-demand-validation`, Frankfurt, in connected organization `org-bold-glitter-92191180` (`Nikitas8`). The API confirmed organization plan `free` twice. No upgrade, payment method, subscription, Auth, AI Gateway or paid backup was enabled.
- Schema preparation branch `br-little-shadow-bac5g9ii` (`schema-v1`); clean experiment branch `br-polished-feather-ba3h1u8g` (`experiment-v1`) inherits the empty schema. No customer data was copied from another project.
- Three small tables: versioned consent/session flags, encrypted voluntary contacts/answers and admission limits. No catalog files, names, store URLs, payment data, IPs or user agents are stored by the app. Normal provider connection logs remain subject to provider policies. Retention runs before each consented admission and during daily aggregate reads.
- Application role `venture_collector`: verified non-superuser, no role/database creation, no inherited privileges; SELECT/INSERT/DELETE only on these three tables, plus column-limited UPDATE for session flags and admission counts. It cannot mark a buyer independently verified.
- Prepared function slug `evidence`, Node.js 24, pool maximum two, TLS `verify-full`, five-second database connection/query timeouts. A public function now exists on the experiment branch; see the deployment and QA update below.
- Bounds: 500 session admissions/day, 5,000 retained sessions, 500 registrations, 4 KiB request bodies, fixed fields and enums, no arbitrary upload endpoint. Identity ownership and independence are not inferred from email uniqueness. QA uses a separate secret and `test=true`, excluded from all aggregate queries.
- Added voluntary consent, no cookies/storage/fingerprinting, in-memory browser session, AES-256-GCM encrypted contact, keyed deduplication and random receipt for deletion. Browser samples cannot generate a completed real-file evaluation. Raw contact/report data never enters GitHub artifacts.
- App retention target 30 days, daily purge prepared in the aggregate check plus expiry on activity. Provider restore/log retention can differ. The currently paused system has no registrations. Do not promise a daily purge has executed before the monitor is actually activated and verified.

## Free-plan safeguards

Current primary references: [Neon plans](https://neon.com/docs/introduction/plans), [Neon pricing](https://neon.com/pricing), [Render free services](https://render.com/docs/free).

Neon Free currently documents 100 CU-hours, 0.5 GB storage and 5 GB public network transfer per project, with hard suspension/failure at allowance exhaustion rather than automatic paid overages. Our additional project caps are 72,000 compute seconds, 100 MB egress and 100 MB logical database size; compute stays at 0.25 CU. The initial 20 MB optional storage cap blocked even schema creation. Automatic review first rejected the increase; after official free-plan limits and the account plan were reverified, a 100 MB cap was accepted. This changed an application cap below the currently documented 0.5 GB free allowance, not the billing plan.

No additional Render web service was created. Maritime-Carbon uses a free instance in the same workspace; a second Render instance would consume its shared 750 monthly free instance hours. Its service and database were not changed. The existing static site remains the frontend. Owner attestations of no payment method on Render/GitHub remain attestations, not independent billing access.

## Authorization and live QA — updated 19 October 2026

The owner supplied and authorized publication of **CeoAgentAI**, **ceoagentai@proton.me**, **Verantzerou 1, 10677 Athens, Greece**, **+30 210 3823709**, and clarified 10677 is the postal code. Business registration is owner-attested, not independently verified. The public notice and separate consents are version **2026-10-19-v2**; see [privacy implementation](PRIVACY_DRAFT.md).

The owner explicitly authorized the dedicated collector's generated secrets and native Neon deployment. Native operations accepted the restricted-role password reset, fresh CSPRNG keys and deployment; the earlier approval blocker is resolved for this scoped action. No unrelated project, account plan or role was changed.

- Function: `evidence`, experiment branch `br-polished-feather-ba3h1u8g`, database **venture_validation**.
- Native URL: https://br-polished-feather-ba3h1u8g-evidence.compute.c-8.eu-central-1.aws.neon.tech
- Completed reviewed code deployment: **2**, initially `VALIDATION_STOPPED=true`.
- Public application status is **/status**. Neon's reserved /healthz returns platform “ok,” which does not prove application/DB health.
- **48 live checks passed** while stopped, including real restricted-role/TLS diagnostics, exact-origin CORS, methods, consent/body validation, encrypted synthetic registration, duplicate rejection, GCM verification/wrong-key rejection, separate measurement consent, QA exclusion, receipt/session deletion, expiry purge and real database admission-cap rejection.
- Restricted native SQL verified synthetic session/contact records and the 31-day-old fixtures were removed. The temporary daily cap was restored to its prior value. Genuine counters stayed zero; verified unique visitors remain unknown.
- Local **45 Python + 23 Node tests passed**. No generated contact/read/QA keys matched intended source content; generic repository scan also applies.
- No plaintext secrets in files, argv, terminal output, artifacts or commits. Temporary QA transport uses current-user Windows DPAPI, containing no database password. Remove its ignored encrypted blob after setup. Only the aggregate-read key may be placed in GitHub's designated Actions secret.

Registration remains paused until this public notice is deployed, the aggregate-only monitor is configured and verified, and the exact endpoint/CSP is published. Record backend and public activation timestamps separately; do not backdate activation to schema preparation or QA. Contacts never go into GitHub. No payments are authorized.

Before subsequent code-only deploys, omit environment to inherit the existing protected values. Never replace the full environment with a lone shutdown flag without checking API replacement semantics. Do not rotate the contact encryption key while records exist without an approved migration. Emergency shutdown can deploy reviewed code that hard-stops enrollment while preserving the environment and withdrawal handling; public controls and monitoring have separate shutdown gates.

## Automated monitoring prepared

`python -m ai_ceo.validation` accepts a verified HTTPS Neon `/summary` URL and aggregate read key through environment variables. It refuses redirects, validates bounded count/source fields, excludes all contact data from output, writes only `runtime/validation-artifact/summary.json`, and never infers genuine unique people from sessions. The workflow job stays gated off until activation. A missing endpoint or failing check is a blocker, not evidence of no visitors or rejected demand.

Local tests: `python scripts/run_tests.py`; `node --test --test-isolation=none tests/catalog.test.cjs tests/demand.test.mjs`. The Windows test runner creates only synthetic fixtures with inherited workspace permissions to avoid private temporary-directory ACL failures. Windows sandbox blocks Node child-process spawning, so local Node tests use no process isolation. Linux CI uses normal test isolation. Dependencies were downloaded from the official npm registry with integrity verification; lifecycle scripts were not run locally. Hosted CI then completed a clean install, all 67 tests, the production dependency audit (zero reported vulnerabilities) and the bundle build. **The later 48-check live integration passed while stopped; activation is tracked separately below.**

## Decisions and distribution

See [market evidence](../research/MARKET_VALIDATION.md), [experiment protocol](../research/experiments/agency-handoff-v1.json) and [permitted channels](../research/DISTRIBUTION.md). The free checker is already functional. The proposed paid pack is not sold. Initial targets are 100 genuine relevant visitors, 10 completed real evaluations, five qualified voluntary pilots and three independent buyers explicitly willing to pay EUR 9. Candidate sessions, unverified email forms, competitor reviews and test fixtures cannot satisfy those claims automatically.

Until qualified exposure exists, the decision is **distribution unresolved**, with collection currently blocked. Do not expand product scope, activate payments, report hypothetical revenue or silently pivot because a new site has no measured traffic.
