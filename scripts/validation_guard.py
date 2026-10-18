"""Bound this private workflow to four new trusted runs per UTC day."""
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from ai_ceo.validation import NoRedirects


def main():
    if (os.getenv("GITHUB_REPOSITORY") != "nikelef/venture-ai-ceo"
            or os.getenv("GITHUB_REF") != "refs/heads/main"
            or os.getenv("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}
            or os.getenv("GITHUB_RUN_ATTEMPT") != "1"
            or os.getenv("ZERO_SPEND_CONFIRMED") != "true"
            or os.getenv("SHUTDOWN", "true") != "false"):
        raise SystemExit("Untrusted, repeated or disabled validation execution")
    token = os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("Read-only workflow token required")
    day = datetime.now(timezone.utc).date().isoformat()
    query = urlencode({"created": ">=" + day, "per_page": 20})
    url = "https://api.github.com/repos/nikelef/venture-ai-ceo/actions/workflows/demand-validation.yml/runs?" + query
    request = Request(url, headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Venture-validation-guard"})
    try:
        with build_opener(NoRedirects()).open(request, timeout=15) as response:
            raw = response.read(100001)
        if len(raw) > 100000:
            raise ValueError()
        runs = json.loads(raw)
        if type(runs["total_count"]) is not int or not 1 <= runs["total_count"] <= 4:
            raise ValueError()
        if str(os.getenv("GITHUB_RUN_ID")) not in {str(item["id"]) for item in runs["workflow_runs"]}:
            raise ValueError()
    except Exception:
        raise SystemExit("Validation run quota or provenance could not be verified") from None
    print("Trusted validation execution within four-run UTC ceiling; no paid API calls.")


if __name__ == "__main__":
    main()
