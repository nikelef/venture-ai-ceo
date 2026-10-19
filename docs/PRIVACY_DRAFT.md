# Privacy implementation and operator record — 19 October 2026

This document replaces the earlier placeholder draft for the limited demand experiment. The [public notice](../web/review-notice.html) is the visitor-facing source. It is a description of implemented controls, not an independent legal certification. Payments remain disabled.

## Owner-confirmed controller

- Registered business/controller and project contact: **CeoAgentAI**, as explicitly confirmed by the owner; registration has not been independently verified.
- All project, support and privacy correspondence: **ceoagentai@proton.me**.
- Public address: **Verantzerou 1, 10677 Athens, Greece**. The owner clarified that 10677 is the postal code, not a PO Box number.
- Telephone: **+30 210 3823709**.
- Publication of these details and the dedicated Neon deployment with collector-only secrets was explicitly authorized in this mission.

No VAT number, tax status, DPO appointment, payment-provider verification or independent business-registration verification is asserted.

## Purposes, fields and lawful bases

The checker never uploads CSV data, filenames, headings, values or reports. Optional measurement uses affirmative consent under Article 6(1)(a): role, coarse acquisition category, creation time, versioned consent, hashed random token and fixed engagement/action flags. Tokens are kept only in page memory; no analytics cookies, browser storage or fingerprinting.

A separate unchecked consent covers email and selected answers for this exact pilot/feedback experiment. Registration does not require measurement consent. AES-256-GCM encrypts the normalized email; HMAC supports duplicate detection; a hashed random receipt supports withdrawal. Answers include role, platform, timing, problem, optional pilot request, yes/no/unsure willingness, EUR 9 proposed price, source, timestamp, consent version and a synthetic-test marker. No purchasing, marketing subscription or automated email verification occurs.

Essential service/security and support processing use legitimate interests (Article 6(1)(f)); statutory rights handling uses legal obligations (Article 6(1)(c)). The limited legitimate interests are service availability, abuse prevention and responding to a request. Safeguards: no application IP/user-agent storage, fixed fields, no raw request logging, short retention, separate optional consent, capacity limits, encryption and restricted access. This does not make optional analytics “essential.”

## Retention and requests

Application records expire after 30 days, purged on consented session admission and aggregate monitoring. Availability gaps can delay deletion; do not promise a daily purge ran until its actual execution is verified. Database restore history is configured at six hours. A recovery must reapply unresolved deletions before collection resumes. Aggregate-only GitHub artifacts have seven-day retention; no contacts or session identifiers enter them.

Open-page session deletion remains permitted after activity-token expiry and during shutdown. Registration withdrawal uses its private receipt, even during shutdown. Correction can use deletion followed by a new consented form. Access, correction, erasure, restriction, objection, applicable portability and lost-receipt requests use the public privacy email. Verify ownership proportionately; do not ask for credentials or identity documents by default.

**Mailbox responsibility:** CeoAgentAI must handle correspondence and applicable rights deadlines, normally one month with legally permitted exceptions. No mailbox access or automated email worker has been configured for this agent. The public notice states request-based retention criteria rather than inventing automated mailbox deletion. Respond about the exact pilot only with appropriate opt-in context; no newsletter or unrelated marketing.

Complaint route: [Hellenic DPA](https://www.dpa.gr/en/individuals/complaint-to-the-hellenic-dpa), or the person's competent local authority. No automated decision with legal or similarly significant effects is made.

## Processors, regions and transfers

- Render: existing static site/CDN, ordinary connection metadata; [terms](https://render.com/terms) incorporate its [DPA](https://render.com/dpa). No customer CSV upload.
- Neon/Databricks: dedicated project `cool-firefly-02159743`, experiment branch `br-polished-feather-ba3h1u8g`, database **venture_validation**, application role `venture_collector`. Database and completed function invocation hostname are AWS Frankfurt / eu-central-1. [Current Neon schedule](https://neon.com/platform-terms) incorporates the Databricks MCSA; MCSA section 4 incorporates the [DPA](https://www.databricks.com/legal/dpa). This is not a new contract signature by this agent.
- GitHub: private source, CI and aggregate-only monitoring; [privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). No contact, receipt, token or source-file data in artifacts.
- Proton: correspondence only when someone chooses to email the controller; Swiss provider [privacy](https://proton.me/legal/privacy) and [DPA](https://proton.me/legal/dpa). Do not promise external email is end-to-end encrypted.

EU database placement does not imply every processing operation is EU-only. Provider support/security/subprocessors can involve the US and other countries. The linked DPAs describe applicable standard contractual clauses and other safeguards. Neon's current schedule specifically identifies US-based Grafana in addition to Databricks subprocessors. Provider-specific log retention and every actual transfer have not been independently audited; the public notice discloses this limitation and supplies a contact for safeguard information. Reassess changes before expanding processing.

## Deployment and evidence controls

Neon API still reports the Free organization/plan. Project caps remain 72,000 compute seconds (20 CU-hours), 100 MB transfer and 100 MB logical size; compute is fixed at 0.25 CU. Current Free-plan documentation lists 100 CU-hours, 0.5 GB storage and 5 GB transfer; previous project notes quoted an older 1 GB allowance. Our lower caps remain unchanged. Functions are advertised free during beta; no paid plan, additional Render instance, AI service or account-level change is authorized.

Fresh secrets were generated through native Neon operations and stored in the dedicated function deployment environment. No plaintext secret was printed or written to a file. For local native QA/Actions setup, a temporary current-user Windows DPAPI blob carries only QA/contact/read keys, never the database password; its decrypted contents stay in process memory. Remove the protected blob after setup. Only the aggregate-read key may go into this private repository's designated Actions secret through native secret-setting transport. Never put database, encryption or QA secrets into GitHub.

The running function was deployed initially stopped. Public `/status` identifies the application; Neon's reserved `/healthz` returns a platform “ok” and is not application/SQL health evidence. QA-only `/diagnostics` checks the actual role and verified TLS socket without returning records. Synthetic QA must always carry its private QA header and remain excluded by SQL summaries. No visitor/buyer claim follows from our own checks.

Activation requires the public privacy notice, live method/CORS/consent/encryption/deletion/retention/quota/security checks, clean synthetic fixtures, exact CSP/endpoint, and a verified aggregate-only monitor. Preserve tests and evidence, and keep real collection stopped on any material failure.

Activation completed on 19 October 2026: backend at 09:23:29.332258 UTC and public controls at 09:30:59.225533 UTC. All gates above passed; see [activation evidence](../research/experiments/collector-activation-2026-10-19.json). The aggregate-only monitor's active cloud read succeeded. Initial observed customer counters are zero, with unique visitors unverified. A first scheduled firing and interactive visual browser QA remain unobserved; neither is claimed as completed.

The temporary DPAPI transport was removed and absence verified after setup. No application secrets remain in local plaintext files or intended source/artifacts; the native deployed environment and the aggregate-only GitHub Actions secret retain their authorized values.
