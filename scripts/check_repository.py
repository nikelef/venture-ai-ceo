"""Check intended tracked paths and common credential patterns without printing values."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"AKIA[A-Z0-9]{16}"),
    re.compile(rb"(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}"),
    re.compile(rb"\bIBAN\s*[:=]\s*[\"']?[A-Z]{2}\d{2}[A-Z0-9]{10,}"),
]
PRIVATE_DIRS = {".tools", ".tmp", ".venv", "data", "runtime", "private", "backups", "customers", "financial",
                ".aws", ".codex", ".agents", "__pycache__", "logs", "output", "outputs"}


def main() -> int:
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    staged_names = set(subprocess.check_output(["git", "ls-files", "--cached", "-z"], cwd=ROOT).decode("utf-8").split("\0"))
    problems, count = [], 0
    for name in sorted(set(names.decode("utf-8").split("\0")) - {""}):
        path = ROOT / name
        parts = Path(name).parts
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or set(parts) & PRIVATE_DIRS:
            problems.append((name, "private path or symlink"))
            continue
        if path.name != ".env.example" and (path.name.startswith(".env") or path.suffix.lower() in {
            ".env", ".key", ".pem", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3", ".log", ".zip", ".exe"
        }):
            problems.append((name, "sensitive or generated file type"))
            continue
        if path.stat().st_size > 500_000:
            problems.append((name, "unexpected large file; manual inspection required"))
            continue
        versions = [("working file", path.read_bytes())]
        if name in staged_names:
            versions.append(("Git index", subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)))
        for version, raw in versions:
            if any(rule.search(raw) for rule in RULES):
                problems.append((name, f"credential-like content in {version}; value withheld"))
        count += 1
    for name, reason in problems:
        print(f"BLOCKED: {name}: {reason}")
    print(f"Repository scan: {count} files examined; {len(problems)} findings. Pattern scan is not proof of absence.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
