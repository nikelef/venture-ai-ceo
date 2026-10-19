"""Bound this private workflow to four new trusted runs per UTC day."""
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from ai_ceo.validation import NoRedirects


def verified_research_run(data):
    """Never allow a PR/fork completion to reach the later read-secret step."""
    if (not isinstance(data, dict)
            or type(data.get("id")) is not int or data["id"] <= 0
            or data.get("path") != ".github/workflows/research.yml"
            or data.get("name") != "Daily research pilot"
            or data.get("event") not in {"schedule", "workflow_dispatch"}
            or data.get("status") != "completed" or data.get("conclusion") != "success"
            or data.get("head_branch") != "main" or data.get("run_attempt") != 1
            or data.get("head_repository", {}).get("full_name") != "nikelef/venture-ai-ceo"
            or not re.fullmatch(r"[0-9a-f]{40}", data.get("head_sha", ""))):
        raise ValueError("Untrusted research completion")
    return data["id"], data["head_sha"]


def get_json(url, token):
    request = Request(url, headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Venture-validation-guard"})
    with build_opener(NoRedirects()).open(request, timeout=15) as response:
        raw = response.read(100001)
    if len(raw) > 100000:
        raise ValueError("Response too large")
    return json.loads(raw)


def main():
    if (os.getenv("GITHUB_REPOSITORY") != "nikelef/venture-ai-ceo"
            or os.getenv("GITHUB_REF") != "refs/heads/main"
            or os.getenv("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch", "workflow_run"}
            or os.getenv("GITHUB_RUN_ATTEMPT") != "1"
            or os.getenv("ZERO_SPEND_CONFIRMED") != "true"
            or os.getenv("SHUTDOWN", "true") != "false"):
        raise SystemExit("Untrusted, repeated or disabled validation execution")
    token = os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("Read-only workflow token required")
    if os.getenv("GITHUB_EVENT_NAME") == "workflow_run":
        try:
            event_path = os.getenv("GITHUB_EVENT_PATH")
            if not event_path:
                raise ValueError()
            raw = Path(event_path).read_bytes()
            if len(raw) > 256000:
                raise ValueError()
            event = json.loads(raw)
            if event.get("repository", {}).get("full_name") != "nikelef/venture-ai-ceo":
                raise ValueError()
            expected = verified_research_run(event.get("workflow_run"))
            actual = get_json("https://api.github.com/repos/nikelef/venture-ai-ceo/actions/runs/" + str(expected[0]), token)
            if verified_research_run(actual) != expected:
                raise ValueError()
        except Exception:
            raise SystemExit("Research completion provenance could not be verified") from None
    day = datetime.now(timezone.utc).date().isoformat()
    query = urlencode({"created": ">=" + day, "per_page": 20})
    url = "https://api.github.com/repos/nikelef/venture-ai-ceo/actions/workflows/demand-validation.yml/runs?" + query
    try:
        runs = get_json(url, token)
        if type(runs["total_count"]) is not int or not 1 <= runs["total_count"] <= 4:
            raise ValueError()
        if str(os.getenv("GITHUB_RUN_ID")) not in {str(item["id"]) for item in runs["workflow_runs"]}:
            raise ValueError()
    except Exception:
        raise SystemExit("Validation run quota or provenance could not be verified") from None
    print("Trusted validation execution within four-run UTC ceiling; no paid API calls.")


if __name__ == "__main__":
    main()
