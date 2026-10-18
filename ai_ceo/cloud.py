"""Bounded GitHub Actions research with private, integrity-checked state artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

from ai_ceo.audit import Store, utcnow
from ai_ceo.policy import Action, PolicyDenied, authorize
from ai_ceo.worker import main as research

REPOSITORY = "nikelef/venture-ai-ceo"
WORKFLOW = "research.yml"
ARTIFACT = "venture-research-state"
MAX_ARCHIVE = 4 * 1024 * 1024
FILES = {"research.sqlite3": 2 * 1024 * 1024, "state.json": 16_384, "decision.json": 500_000}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GitHub:
    """The official gh client handles authenticated API/redirect transport."""
    def api(self, suffix: str) -> dict:
        result = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/actions/{suffix}"],
                                capture_output=True, timeout=30, check=False)
        if result.returncode or len(result.stdout) > 1_000_000:
            raise RuntimeError("GitHub state metadata unavailable")
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise ValueError("Invalid GitHub metadata")
        return value

    def download(self, artifact_id: int, target: Path) -> None:
        with target.open("wb") as output:
            result = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"],
                                    stdout=output, stderr=subprocess.PIPE, timeout=40, check=False)
        if result.returncode or target.stat().st_size > MAX_ARCHIVE:
            raise RuntimeError("State archive download failed or exceeded its limit")


def restore(client: GitHub, directory: Path, *, run_id: str, allow_bootstrap: bool) -> str | None:
    """Never silently roll back to older state or reset a missing history."""
    history = client.api(f"workflows/{WORKFLOW}/runs?per_page=100")
    runs = history.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("Missing workflow history")
    prior = [row for row in runs if str(row.get("id")) != run_id]
    if not prior:
        if history.get("total_count", len(runs)) > len(runs) or not allow_bootstrap:
            raise PolicyDenied("Initial cloud state requires explicit one-time bootstrap authority")
        return None
    prior.sort(key=lambda row: int(row["run_number"]), reverse=True)
    previous = prior[0]
    if previous.get("status") != "completed" or previous.get("conclusion") not in {"success", "failure"} or previous.get("head_branch") != "main" or previous.get("event") not in {"schedule", "workflow_dispatch"}:
        raise PolicyDenied("Previous cloud execution requires recovery review")
    previous_id = str(previous["id"])
    if not previous_id.isdigit():
        raise ValueError("Invalid previous execution reference")
    listing = client.api(f"runs/{previous_id}/artifacts?per_page=100")
    artifacts = [row for row in listing.get("artifacts", []) if row.get("name") == ARTIFACT and row.get("expired") is False]
    if len(artifacts) != 1 or type(artifacts[0].get("size_in_bytes")) is not int or not 0 < artifacts[0]["size_in_bytes"] <= MAX_ARCHIVE:
        raise PolicyDenied("Latest cloud state artifact missing, expired or oversized")
    artifact = artifacts[0]
    if type(artifact.get("id")) is not int:
        raise ValueError("Invalid artifact reference")
    archive_path = directory.parent / "previous-state.zip"
    client.download(artifact["id"], archive_path)
    if archive_path.stat().st_size > MAX_ARCHIVE:
        raise ValueError("State archive exceeds its size cap")
    digest = artifact.get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest) or sha256(archive_path) != digest[7:]:
        raise PolicyDenied("GitHub artifact digest verification failed")
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        names = [info.filename for info in members]
        if len(names) != len(set(names)) or not {"research.sqlite3", "state.json"} <= set(names) or not set(names) <= set(FILES):
            raise ValueError("Unexpected or duplicate state archive entries")
        for info in members:
            if info.file_size > FILES[info.filename] or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Oversized or symlinked state archive entry")
            with archive.open(info) as stream:
                raw = stream.read(FILES[info.filename] + 1)
            if len(raw) > FILES[info.filename]:
                raise ValueError("Expanded state file exceeds its cap")
            (directory / info.filename).write_bytes(raw)
    state = json.loads((directory / "state.json").read_bytes())
    if state.get("schema_version") != 1 or state.get("repository") != REPOSITORY or state.get("mode") != "research_only" or state.get("run_id") != previous_id:
        raise PolicyDenied("State provenance does not match the previous execution")
    if state.get("source_commit") != previous.get("head_sha"):
        raise PolicyDenied("State source revision does not match GitHub execution evidence")
    if sha256(directory / "research.sqlite3") != state.get("database_sha256"):
        raise PolicyDenied("Restored state database hash mismatch")
    report = directory / "decision.json"
    if report.exists() and sha256(report) != state.get("report_sha256"):
        raise PolicyDenied("Restored report hash mismatch")
    store = Store(directory)
    try:
        store.verify()
        if store.connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise PolicyDenied("Restored database integrity check failed")
        tables = {row[0] for row in store.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != {"events", "runs"}:
            raise PolicyDenied("Only research state may be restored into cloud automation")
    finally:
        store.close()
    return previous_id


def snapshot(directory: Path, destination: Path, *, run_id: str, source_commit: str,
             worker_exit: int, previous_run_id: str | None) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    store = Store(directory)
    try:
        store.verify()
        audit_hash = store.append("cloud_invocation_complete", {"github_run_id": run_id,
            "source_commit": source_commit, "worker_exit": worker_exit, "is_revenue": False})
        store.backup(destination / "research.sqlite3")
    finally:
        store.close()
    if (destination / "research.sqlite3").stat().st_size > FILES["research.sqlite3"]:
        raise PolicyDenied("Research state reached its storage ceiling")
    report = directory / "decision.json"
    report_hash = None
    if report.exists():
        if report.stat().st_size > FILES["decision.json"]:
            raise PolicyDenied("Research report exceeds its storage ceiling")
        parsed = json.loads(report.read_bytes())
        if parsed.get("status") != "research_only" or parsed.get("is_revenue") is not False or parsed.get("has_live_checkout") is not False:
            raise PolicyDenied("Only noncommercial research reports may be archived")
        (destination / "decision.json").write_bytes(report.read_bytes())
        report_hash = sha256(report)
    state = {"schema_version": 1, "repository": REPOSITORY, "mode": "research_only", "run_id": run_id,
        "source_commit": source_commit, "created_at": utcnow(), "previous_run_id": previous_run_id,
        "worker_exit": worker_exit, "database_sha256": sha256(destination / "research.sqlite3"),
        "report_sha256": report_hash, "audit_hash": audit_hash, "authorized_outlay_eur": "0",
        "model_calls": 0, "verified_payment_count": 0,
        "platform_conclusion": "verify_in_github_after_job_finishes"}
    (destination / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def main(*, client: GitHub | None = None, worker=research) -> int:
    try:
        if os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("GITHUB_REPOSITORY") != REPOSITORY or os.getenv("GITHUB_REF") != "refs/heads/main":
            raise PolicyDenied("Cloud workflow is restricted to the private project main branch")
        if os.getenv("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"} or os.getenv("CLOUD_ZERO_SPEND_CONFIRMED") != "true":
            raise PolicyDenied("Cloud automation lacks an allowed trigger or owner-confirmed billing safeguard")
        if os.getenv("GITHUB_RUN_ATTEMPT") != "1":
            raise PolicyDenied("Re-running an old execution could roll state backward; use a new reviewed dispatch")
        run_id, commit = os.getenv("GITHUB_RUN_ID", ""), os.getenv("GITHUB_SHA", "")
        if not run_id.isdigit() or not re.fullmatch(r"[a-f0-9]{40}", commit) or not os.getenv("GH_TOKEN"):
            raise PolicyDenied("Missing native workflow identity or ephemeral token")
        root = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
        directory, artifact = root / "runtime" / "cloud-data", root / "runtime" / "cloud-artifact"
        authorize(Action.RESEARCH, data_dir=directory)
        directory.mkdir(parents=True, exist_ok=True)
        # The runner is fresh. Unexpected local leftovers are never used as recovery state.
        if any(directory.iterdir()):
            raise PolicyDenied("Cloud state directory must start empty")
        previous = restore(client or GitHub(), directory, run_id=run_id,
                           allow_bootstrap=os.getenv("CLOUD_BOOTSTRAP_ALLOWED") == "true")
        os.environ["AI_CEO_DATA_DIR"] = str(directory)
        code = worker(["--live-feeds"])
        state = snapshot(directory, artifact, run_id=run_id, source_commit=commit,
                         worker_exit=code, previous_run_id=previous)
        output = os.getenv("GITHUB_OUTPUT")
        if output:
            with Path(output).open("a", encoding="utf-8") as stream:
                stream.write("state_ready=true\n")
        summary = os.getenv("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write(f"Research-only cloud execution {run_id}. Worker exit: {code}. "
                             "No model calls, checkout or verified payments.\n\n"
                             f"Audit checkpoint: `{state['audit_hash']}`. State retained privately for seven days.\n")
        print(json.dumps({"mode": "research_only", "run_id": run_id, "previous_run_id": previous,
                          "worker_exit": code, "private_state_ready": True, "verified_payment_count": 0}))
        return code
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, sqlite3.Error, subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        print(f"CLOUD SAFE STOP: {type(exc).__name__}; review private execution/state evidence", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
