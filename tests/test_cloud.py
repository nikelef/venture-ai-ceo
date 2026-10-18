import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from ai_ceo.audit import Store
from ai_ceo.cloud import ARTIFACT, FILES, REPOSITORY, main, restore, snapshot
from ai_ceo.policy import PolicyDenied
from ai_ceo.worker import main as offline_research

COMMIT = "a" * 40


class FakeGitHub:
    def __init__(self, archive=None, *, event="workflow_dispatch", conclusion="success"):
        self.archive = archive
        self.event, self.conclusion = event, conclusion

    def api(self, path):
        if path.startswith("workflows/"):
            return {"total_count": 0 if self.archive is None else 1, "workflow_runs": [] if self.archive is None else [
                {"id": 100, "run_number": 1, "status": "completed", "conclusion": self.conclusion,
                 "head_branch": "main", "event": self.event, "head_sha": COMMIT}]}
        raw = self.archive.read_bytes()
        return {"artifacts": [{"id": 1, "name": ARTIFACT, "expired": False, "size_in_bytes": len(raw),
                               "digest": "sha256:" + hashlib.sha256(raw).hexdigest()}]}

    def download(self, artifact_id, target):
        shutil.copyfile(self.archive, target)


class CloudTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".tmp" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ID": "100",
            "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": COMMIT, "GITHUB_WORKSPACE": str(self.root),
            "GH_TOKEN": "ephemeral-test-placeholder", "CLOUD_ZERO_SPEND_CONFIRMED": "true",
            "CLOUD_BOOTSTRAP_ALLOWED": "true"}, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def seed_archive(self, *, extras=None, state_change=None):
        data = self.root / "seed"
        os.environ["AI_CEO_DATA_DIR"] = str(data)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(offline_research([]), 0)
        exported = self.root / "exported"
        state = snapshot(data, exported, run_id="100", source_commit=COMMIT, worker_exit=0, previous_run_id=None)
        if state_change:
            state.update(state_change)
            (exported / "state.json").write_text(json.dumps(state), encoding="utf-8")
        archive = self.root / "state.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for path in exported.iterdir():
                output.writestr(path.name, path.read_bytes())
            for name, value in (extras or {}).items():
                output.writestr(name, value)
        return archive, state

    def test_first_run_requires_one_time_bootstrap_and_never_guesses_missing_state(self):
        directory = self.root / "fresh"
        directory.mkdir()
        with self.assertRaises(PolicyDenied):
            restore(FakeGitHub(), directory, run_id="100", allow_bootstrap=False)
        self.assertIsNone(restore(FakeGitHub(), directory, run_id="100", allow_bootstrap=True))

    def test_snapshot_restores_real_audit_chain_and_daily_limits(self):
        archive, state = self.seed_archive()
        target = self.root / "restored"
        target.mkdir()
        self.assertEqual(restore(FakeGitHub(archive), target, run_id="101", allow_bootstrap=False), "100")
        store = Store(target)
        try:
            self.assertEqual(store.verify(), 3)
            self.assertEqual(store.connection.execute("SELECT digest FROM events ORDER BY seq DESC LIMIT 1").fetchone()[0], state["audit_hash"])
            with self.assertRaises(PolicyDenied):
                store.start_run(1, 3)
        finally:
            store.close()

    def test_archive_traversal_extra_files_and_oversized_files_are_rejected(self):
        for index, extra in enumerate(({"../outside.txt": b"no"}, {"customer.json": b"no"},
                                        {"decision.json": b"x" * (FILES["decision.json"] + 1)})):
            # Each case uses fresh seed data to avoid intentionally resetting run state.
            case = self.root / f"case-{index}"
            case.mkdir()
            archive = case / "bad.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
                output.writestr("research.sqlite3", b"placeholder")
                output.writestr("state.json", b"{}")
                for name, raw in extra.items():
                    output.writestr(name, raw)
            with self.assertRaises(ValueError):
                restore(FakeGitHub(archive), case, run_id="101", allow_bootstrap=False)
            self.assertFalse((self.root / "outside.txt").exists())

    def test_state_provenance_and_database_hash_cannot_be_replaced(self):
        for index, change in enumerate(({"run_id": "999"}, {"database_sha256": "0" * 64}, {"source_commit": "b" * 40})):
            # Use a separate test workspace for each independent snapshot.
            original_root = self.root
            self.root = original_root / f"case-{index}"
            self.root.mkdir()
            archive, _ = self.seed_archive(state_change=change)
            target = self.root / "restore"
            target.mkdir()
            with self.assertRaises(PolicyDenied):
                restore(FakeGitHub(archive), target, run_id="101", allow_bootstrap=False)
            self.root = original_root

    def test_untrusted_or_cancelled_previous_execution_requires_review(self):
        target = self.root / "restore"
        target.mkdir()
        fake_path = self.root / "unused.zip"
        for client in (FakeGitHub(fake_path, event="pull_request"), FakeGitHub(fake_path, conclusion="cancelled")):
            with self.assertRaises(PolicyDenied):
                restore(client, target, run_id="101", allow_bootstrap=False)

    def test_context_billing_shutdown_and_rerun_guards_precede_network(self):
        for key, value in (("GITHUB_REPOSITORY", "other/repository"), ("GITHUB_REF", "refs/heads/other"),
                           ("CLOUD_ZERO_SPEND_CONFIRMED", "false"), ("AI_CEO_SHUTDOWN", "true"),
                           ("GITHUB_RUN_ATTEMPT", "2")):
            with patch.dict(os.environ, {key: value}), patch("ai_ceo.cloud.GitHub.api") as network, \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(), 2)
                network.assert_not_called()

    def test_cloud_wrapper_exports_real_offline_run_without_token_or_customer_data(self):
        os.environ["GITHUB_OUTPUT"] = str(self.root / "step-output")
        def offline(_):
            return offline_research([])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(client=FakeGitHub(), worker=offline), 0)
        exported = self.root / "runtime" / "cloud-artifact"
        self.assertEqual({path.name for path in exported.iterdir()}, set(FILES))
        state = json.loads((exported / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["mode"], "research_only")
        self.assertEqual(state["worker_exit"], 0)
        self.assertNotIn(os.environ["GH_TOKEN"], (exported / "state.json").read_text(encoding="utf-8"))
        self.assertIn("state_ready=true", (self.root / "step-output").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
