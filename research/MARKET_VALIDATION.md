# Demand research — 19 October 2026 (owner local date)

Decision: test the existing Shopify tool as an **agency catalog handoff** proposition. Keep the checker free; proposed total price is **EUR 9 per catalog handoff pack**, without a subscription. This is a low-cost experiment, not a conclusion that a differentiated paid market exists. Do not build payments or expand the product on the strength of the previous 75/100 research score.

## What the evidence supports

Public merchant posts describe missing variants, images and inventory after catalog imports, including a failed attempt to restore an export. These are consequential operational problems. The cause in any particular store is not independently established. Our limited file checks **cannot predict deletions, compare store state, provide rollback or fix API/importer behavior**. Severe complaints must not become claims that our current tool prevents those outcomes.

Matrixify reviews include an agency using it for client migrations and valuing its dry run, and a merchant using it for more than 5,000 SKUs. Other reviewers describe spreadsheet complexity and billing/plan confusion; developer replies dispute parts of those complaints. This supports demand for the incumbent category and for support. It is **not** willingness to pay us. Individual reviews were read; Shopify Magic summaries were not counted as independent customers.

The direct free substitute CSV Preflight advertises local browser checks, Shopify variant collision checks, fixes and downloads, with a larger file limit. Therefore “private/browser-only” and “before import” are **not sufficient differentiation**. We have not audited its implementation or verified its marketing claims. The narrow remaining hypothesis is that a simple, value-redacted handoff report with clear exclusions and correction guidance is useful enough to buy for an occasional client job. Even this can be replicated and may prove too weak.

## Buyer segments and disconfirmation

| Segment | Reason to test | Reason they may not pay |
|---|---|---|
| Freelance Shopify migration specialists and small agencies, with an import in the next 30 days | Repeated client handoffs; a report can support review | Matrixify already has a valued dry run and extensive documentation; a JSON report may be enough |
| Catalog operations teams with supplier files | Recurring formatting and option problems | They often need mapping, automation and store-state checks beyond this tool |
| Occasional small merchants | Specific import failures create urgency | Free native guidance and free checkers; low recurrence and likely support burden |
| Large/multi-store or enterprise catalogs | High consequences and budgets | Current 2 MiB/10,000-record scope, no store integration and no service guarantee are inadequate |

Prioritize the first segment for this experiment. Treat role, platform and near-term job answers as **self-reported qualification**, not identity verification. Do not infer ability to pay from a job title.

## Competition and current offers

| Solution | Posted price, checked this run | Strength / implication |
|---|---|---|
| Shopify native CSV import and documentation | Included platform functionality; no separate checker purchase | Official error and format guidance; store-aware importer remains essential |
| Matrixify | Free demo; USD 20 / 50 / 200 per 30 days on its pricing page | Import/export, dry runs, large files, support, migrations; direct paid-category evidence appears in merchant reviews, not audited receipts |
| Ablestar Bulk Product Editor | Free limited plan; USD 30 / 60 / 120 per month on its app listing | Preview and undo, CSV updates, scheduling; stronger operational capabilities than a local preflight |
| CSV Preflight / csvimportchecker.com | Core checker advertised free, no account | Directly undermines privacy-only differentiation; vendor claims, not an independent feature audit |
| Nabu / Ced / Simprosys / Multifeed | Search-returned app listings/reviews, not a complete pricing audit | Established feed tools have broad syncing and support. Price or approval failures often require store/account investigation, not TSV structure checks |

Pricing is an advertised offer, not verified captured revenue. No app was bought, installed in a store or contacted.

## Compare the existing hypotheses

| Hypothesis | Current evidence and substitute | Decision |
|---|---|---|
| Catalog Preflight | Real category pain; strong paid and free substitutes; working limited tool | Run the smallest falsifiable agency handoff experiment; commercial differentiation remains weak |
| WooCommerce preflight (previous alternate) | Built-in free importer already maps columns and reports results; no new firsthand purchase-intent evidence | Do not expand now |
| BigCommerce error locator (previous alternate) | Official importer already reports error CSV line numbers and has support | No demonstrated advantage; do not expand |
| Merchant Center structure check | Reported disapproval/price mismatch pain and paid feed apps, but problems frequently depend on website/account/policy state | Urgency alone does not make a local TSV checker adequate; keep as a research alternative |
| Variant collision / price-format checks | Already features of this and competing checkers | Not independent validated businesses |
| UTF-8/BOM helper | Free editor and importer substitutes | Weak standalone offer |
| Image-reference manifest | Cannot establish reachability, matching or rights from local syntax | Do not promise remote image recovery |
| RSS diagnostics / calendar check | Earlier vendor offers only; free validators and calendar correctness burden | Insufficient customer evidence to justify a pivot now |

No previous score is being used as a proxy for customer demand. This selection reflects low incremental build cost and a testable proposition, with an explicit risk that the correct outcome will be abandonment after sufficient qualified exposure.

## Public source register

Four Exa discovery searches returned six results each (24 returned results, not 24 verified buyers). Follow-up fetched ten unique primary problem, documentation, competitor and community-rules pages; repeated fetches were not new evidence. Sources below are original paraphrases and links only. No republication license is assumed, no catalog/user data was downloaded, and no quoted testimonials were reused on the landing page.

| Source | Observation / limitations |
|---|---|
| [Shopify variant-deletion discussion](https://community.shopify.com/t/csv-product-import-deleted-variants-shopify-you-got-some-explaining-to-do/582717) | January 2026 merchant report about a unit-price update; original posts and disputed replies. Anecdote, not a verified causal diagnosis |
| [Shopify failed catalog restore](https://community.shopify.com/t/shopify-product-catalog-csv-file-fails-to-upload-variants-inventory-data/402942) | March 2025 merchant reports 313 listings and missing variants/images/inventory. No independent store audit |
| [Matrixify reviews](https://apps.shopify.com/excel-export-import/reviews) | September 2026 migration/5,000-SKU praise, August complexity complaint, September plan/billing dispute. Review mix selected for counterevidence, not a representative survey |
| [Matrixify pricing](https://matrixify.app/pricing/) | Official posted plans; prior dry-run documentation also remains relevant |
| [Ablestar listing](https://apps.shopify.com/bulk-product-editor) | Primary offer and merchant reviews; feature claims have not been independently exercised |
| [CSV Preflight](https://csvimportchecker.com/) | Primary offer for a free local checker; direct substitute, vendor claims |
| [Shopify CSV format](https://help.shopify.com/en/manual/products/import-export/using-csv) | Platform guidance; not evidence of purchasing intent |
| [WooCommerce importer](https://woocommerce.com/document/product-csv-importer-exporter/) | Included import, export and mapping; current documentation |
| [BigCommerce troubleshooting](https://support.bigcommerce.com/s/article/Troubleshooting-Import-Issues?language=en_US) | Error reports already include CSV lines |
| [Shopify Community guidelines](https://community.shopify.com/guidelines) | App offers restricted to Ask and Offer; AI-generated messages prohibited, unsolicited private promotion prohibited. No posting attempted |

Additional discovery-only leads: [Nabu](https://apps.shopify.com/google-shopping-feed-2), [Simprosys negative reviews](https://apps.shopify.com/google-shopping-feed/reviews?page=1&ratings=1), [Multifeed reviews](https://apps.shopify.com/multiple-google-shopping-feeds/reviews), [Merchant Center price mismatch thread](https://community.shopify.com/t/shopify-markets-google-merchant-centre-pricing-error/392668/5). Recheck original pages before relying on individual claims or current pricing. None are customers of Venture CEO.

Legal/operations primary references: [EU consent requirements](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en), [EDPB rights guide](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en), [Google SEO guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [IndexNow protocol](https://www.indexnow.org/documentation). Search eligibility and submission are not proof of indexing or visitors.
