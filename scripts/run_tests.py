"""Run tests; keep synthetic Windows fixtures inside the writable workspace."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (ROOT / ".tmp" / "tests").resolve()
original = tempfile.mkdtemp


def workspace_fixture(suffix=None, prefix=None, dir=None):
    # Python's Windows 0700 temporary-directory ACL can exclude a sandbox token.
    # Inherit the already-authorized workspace ACL for synthetic test files only.
    if dir is None or Path(dir).resolve() != FIXTURES:
        return original(suffix=suffix, prefix=prefix, dir=dir)
    prefix, suffix = prefix or "tmp", suffix or ""
    if any(char in prefix + suffix for char in "/\\"):
        raise ValueError("Unsafe fixture name")
    path = (FIXTURES / (prefix + uuid.uuid4().hex + suffix)).resolve()
    if path.parent != FIXTURES:
        raise ValueError("Fixture must stay in the workspace")
    path.mkdir()  # Normal inherited permissions, no ACL changes or elevated access.
    return str(path)


if __name__ == "__main__":
    if Path.cwd().resolve() != ROOT:
        raise SystemExit("Run from the project root")
    sys.path.insert(0, str(ROOT))
    if os.name == "nt":
        tempfile.mkdtemp = workspace_fixture
    try:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover("tests"))
    finally:
        tempfile.mkdtemp = original
    sys.exit(0 if result.wasSuccessful() else 1)
