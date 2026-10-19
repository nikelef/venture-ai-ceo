"""Read aggregate evidence only; never promote unverified intent into demand."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit

COUNTS = ("engaged_sessions", "candidate_relevant_sessions", "product_interactions", "completed_evaluations",
          "sample_sessions", "registrations", "pilot_requests", "qualified_pilots_unverified",
          "willing_to_pay_unverified", "independently_verified_willing_to_pay")


def assessment(data: dict) -> dict:
    if data.get("experiment") != "agency-handoff-v1" or data.get("price_cents") != 900 or data.get("currency") != "EUR":
        raise ValueError("Unexpected experiment or price")
    if any(type(data.get(key)) is not int or not 0 <= data[key] <= 5000 for key in COUNTS):
        raise ValueError("Invalid aggregate counts")
    if type(data.get("collection_enabled")) is not bool:
        raise ValueError("Missing collection state")
    if data["completed_evaluations"] > data["candidate_relevant_sessions"] or data["independently_verified_willing_to_pay"] > data["willing_to_pay_unverified"]:
        raise ValueError("Inconsistent evidence counts")
    sources = data.get("acquisition_sources")
    if not isinstance(sources, list) or len(sources) > 6:
        raise ValueError("Invalid source summary")
    for source in sources:
        if set(source) != {"source", "sessions"} or source["source"] not in {"direct", "organic", "guide", "community", "directory", "other"}:
            raise ValueError("Unexpected source data")
        if type(source["sessions"]) is not int or not 0 <= source["sessions"] <= 5000:
            raise ValueError("Invalid source counts")
    if sum(source["sessions"] for source in sources) != data["candidate_relevant_sessions"]:
        raise ValueError("Source totals do not match")
    if not data["collection_enabled"]:
        decision = "blocked_collection_paused"
    elif data["independently_verified_willing_to_pay"] >= 3:
        decision = "review_customer_evidence_before_development"
    elif data["registrations"]:
        decision = "review_unverified_interest_continue_free_experiment"
    else:
        decision = "distribution_unresolved_continue_free_experiment"
    return {"experiment": "agency-handoff-v1", "checked_at": datetime.now(timezone.utc).isoformat(),
            "collection_enabled": data["collection_enabled"], "counts": {key: data[key] for key in COUNTS},
            "acquisition_sources": sources, "verified_unique_visitors": None,
            "decision": decision, "demand_validated": False, "payments_enabled": False,
            "targets": {"genuine_relevant_visitors": 100, "completed_evaluations": 10,
                        "qualified_voluntary_pilots": 5, "independent_explicit_willing_to_pay": 3},
            "caveat": "Consented sessions can include repeat people. Email ownership, qualification and independence require review. No traffic alone is not a demand rejection."}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None  # Never forward the read secret to a different URL.


def main() -> None:
    endpoint = os.environ.get("VALIDATION_SUMMARY_URL", "")
    key = os.environ.get("VALIDATION_READ_KEY", "")
    url = urlsplit(endpoint)
    if url.scheme != "https" or not url.hostname or not url.hostname.endswith(".aws.neon.tech") or url.username or url.password or url.path != "/summary" or url.query or url.fragment:
        raise SystemExit("A verified Neon summary URL is required")
    if not key:
        raise SystemExit("Aggregate read secret is not configured")
    request = Request(endpoint, headers={"Authorization": "Bearer " + key, "User-Agent": "Venture-aggregate-monitor/1"})
    try:
        with build_opener(NoRedirects()).open(request, timeout=20) as response:
            raw = response.read(16001)
            if len(raw) > 16000:
                raise ValueError("Response too large")
        result = assessment(json.loads(raw))
    except Exception:
        raise SystemExit("Aggregate evidence check failed; do not infer missing traffic or demand") from None
    target = Path("runtime/validation-artifact/summary.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "demand_validated": False,
                      "collection_enabled": result["collection_enabled"]}))


if __name__ == "__main__":
    main()
