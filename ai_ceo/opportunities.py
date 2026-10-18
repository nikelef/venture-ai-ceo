"""Deterministic scoring of curated evidence. Scores are judgments, not demand."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

WEIGHTS = {"urgency": 25, "distribution": 20, "fulfillment": 20,
           "margin": 15, "defensibility": 10, "safety": 10}


def ranked(path: Path) -> tuple[list[dict], list[dict]]:
    raw = path.read_bytes()
    if len(raw) > 200_000:
        raise ValueError("Evidence input too large")
    data = json.loads(raw)
    sources = data["sources"]
    if not isinstance(sources, list) or not 1 <= len(sources) <= 40:
        raise ValueError("Invalid evidence register")
    allowed = set()
    for source in sources:
        url = urlsplit(source["url"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("Invalid evidence URL")
        if source["id"] in allowed or not source.get("accessed_at") or not source.get("reuse"):
            raise ValueError("Missing evidence provenance or duplicate source")
        allowed.add(source["id"])
    candidates = data["opportunities"]
    if not isinstance(candidates, list) or len(candidates) != 10:
        raise ValueError("Exactly ten documented opportunities are required")
    output = []
    ids = set()
    for candidate in candidates:
        if candidate["id"] in ids:
            raise ValueError("Duplicate opportunity")
        ids.add(candidate["id"])
        scores = candidate["scores"]
        if set(scores) != set(WEIGHTS) or any(type(v) is not int or not 0 <= v <= 5 for v in scores.values()):
            raise ValueError("Invalid scoring dimensions")
        if not candidate["sources"] or not set(candidate["sources"]) <= allowed:
            raise ValueError("Opportunity cites unknown evidence")
        if not candidate.get("counterargument") or not candidate.get("assumption"):
            raise ValueError("Missing skeptical review")
        score = sum(Decimal(scores[key]) * weight / 5 for key, weight in WEIGHTS.items())
        output.append({**candidate, "weighted_score": float(score), "demand_validated": False})
    return sorted(output, key=lambda item: (-item["weighted_score"], item["id"])), sources
