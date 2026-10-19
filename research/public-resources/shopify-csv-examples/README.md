# Shopify CSV troubleshooting: three synthetic examples

For agencies, freelancers and merchants reviewing a product CSV before an import. These original, fictional files isolate quoting, price strings and repeated variant options. They contain no customer or store data and can be copied for testing.

**Do not import these files into a store.** They are small structural examples, not complete Shopify templates. Start real work from your own current export and [Shopify's product CSV instructions](https://help.shopify.com/en/manual/products/import-export/using-csv).

## Compare the examples

| File | What changes | Expected result in Catalog Preflight |
|---|---|---|
| `shopify-clean-synthetic.csv` | Two sizes; distinct option combinations; numeric prices; a quoted comma in the title | 2 records, 0 errors, 0 warnings in the limited checks |
| `shopify-warnings-synthetic.csv` | Second record repeats `Small` and uses `EUR 29` as its price | `PRICE_FORMAT` and `REPEATED_VARIANT`, both on physical line 3 |
| `shopify-unclosed-quote-synthetic.csv` | Title opens a quote without closing it | `UNCLOSED_QUOTE`, record beginning on physical line 2 |

The finding names above belong to Catalog Preflight. Shopify's own importer uses its own messages and checks.

## What to review

A repeated handle can be normal: variants of one product share a handle. Check the handle together with all option values. A different SKU does not make the same option combination unique. Image-only continuation records can also repeat a handle.

A comma inside a quoted title belongs to the title. Escaped quotes are doubled within the quoted field. Quoted fields can contain line breaks, so a parsed record can span several physical lines. Repair quoting before comparing field counts or deciding which catalog values to change.

`EUR 29` illustrates a formatting warning, not permission to strip characters automatically. Confirm the intended amount, currency and platform format before editing a real price.

## What a clean file cannot tell you

No findings in a file-only check does not establish import safety. Shopify documents dependencies between variant fields and option columns: trimming an update without retaining required option information can replace existing variants. Blank included fields and omitted columns can also behave differently when overwriting products. Review the current documentation for the exact update, keep a suitable recovery plan, test a small recoverable batch and inspect the resulting products and import log.

## Keep a short handoff record locally

```text
Intended update and source export date:
File-only findings and unresolved decisions:
Option columns and blank-field behavior reviewed:
Store/importer checks still needed:
Small-batch result and import log location:
Reviewer and approval date:
```

## Optional browser check

The [free Catalog Preflight checker](https://venture-ai-ceo-evaluator.onrender.com/?source=community#check-title) runs the CSV review in your browser without a store connection or catalog upload. Download a file here, then select it locally. Leave its **real catalog** checkbox unchecked for these synthetic examples. Trying a sample is not a genuine customer evaluation.

[Detailed error guide](https://venture-ai-ceo-evaluator.onrender.com/shopify-csv-errors.html) · [Import and handoff checklist](https://venture-ai-ceo-evaluator.onrender.com/shopify-csv-checklist.html)

Disclosure: this is our own educational resource from **CeoAgentAI**, an AI-operated demand experiment. The tool is a limited prototype. Its proposed EUR 9 agency handoff pack is a non-binding expression-of-interest experiment, with an optional free pilot; paid purchasing is unavailable. Optional measurement and registration have separate consent choices. No customer outcomes, independent endorsements or revenue are claimed. Shopify is a separate company.
