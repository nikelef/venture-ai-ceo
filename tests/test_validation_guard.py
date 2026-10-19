import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch
from scripts.validation_guard import main


class GuardTests(unittest.TestCase):
    def context(self):
        return {"GITHUB_REPOSITORY": "nikelef/venture-ai-ceo", "GITHUB_REF": "refs/heads/main",
                "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1",
                "ZERO_SPEND_CONFIRMED": "true", "SHUTDOWN": "false", "GH_TOKEN": "test-only-token",
                "GITHUB_RUN_ID": "123"}

    def test_untrusted_context_cannot_start_network_work(self):
        for change in ({"GITHUB_REPOSITORY": "other/project"}, {"GITHUB_REF": "refs/pull/1/merge"},
                       {"GITHUB_RUN_ATTEMPT": "2"}, {"SHUTDOWN": "true"}, {"ZERO_SPEND_CONFIRMED": "false"}):
            with self.subTest(change=change), patch.dict(os.environ, {**self.context(), **change}, clear=True), \
                    patch("scripts.validation_guard.build_opener") as network, self.assertRaises(SystemExit):
                main()
            network.assert_not_called()

    def invoke(self, count, ids):
        raw = json.dumps({"total_count": count, "workflow_runs": [{"id": item} for item in ids]}).encode()
        response = io.BytesIO(raw)
        with patch.dict(os.environ, self.context(), clear=True), \
                patch("scripts.validation_guard.build_opener") as network, contextlib.redirect_stdout(io.StringIO()):
            network.return_value.open.return_value = response
            main()

    def test_current_run_within_ceiling_is_accepted(self):
        self.invoke(4, [120, 121, 122, 123])

    def test_quota_or_missing_current_run_stops_execution(self):
        for count, ids in ((5, [123]), (1, [999]), (True, [123])):
            with self.subTest(count=count, ids=ids), self.assertRaises(SystemExit):
                self.invoke(count, ids)

    def upstream(self):
        return {"id": 456, "path": ".github/workflows/research.yml", "name": "Daily research pilot",
                "event": "schedule", "status": "completed", "conclusion": "success", "head_branch": "main",
                "run_attempt": 1, "head_repository": {"full_name": "nikelef/venture-ai-ceo"}, "head_sha": "a" * 40}

    def completion_context(self):
        return {**self.context(), "GITHUB_EVENT_NAME": "workflow_run", "GITHUB_EVENT_PATH": "signed-event.json"}

    def test_trusted_completion_is_checked_against_github_before_quota(self):
        for source in ("schedule", "workflow_dispatch"):
            upstream = {**self.upstream(), "event": source}
            event = {"repository": {"full_name": "nikelef/venture-ai-ceo"}, "workflow_run": upstream}
            quota = {"total_count": 4, "workflow_runs": [{"id": 123}]}
            with self.subTest(source=source), patch.dict(os.environ, self.completion_context(), clear=True), \
                    patch("scripts.validation_guard.Path.read_bytes", return_value=json.dumps(event).encode()), \
                    patch("scripts.validation_guard.build_opener") as network, contextlib.redirect_stdout(io.StringIO()):
                network.return_value.open.side_effect = [io.BytesIO(json.dumps(upstream).encode()), io.BytesIO(json.dumps(quota).encode())]
                main()
                self.assertEqual(network.return_value.open.call_count, 2)
                self.assertEqual(network.return_value.open.call_args_list[0].args[0].full_url,
                                 "https://api.github.com/repos/nikelef/venture-ai-ceo/actions/runs/456")

    def test_pr_fork_failure_wrong_workflow_and_untrusted_source_cannot_make_network_requests(self):
        changes = ({"event": "pull_request"}, {"head_branch": "feature"},
                   {"head_repository": {"full_name": "attacker/fork"}}, {"conclusion": "failure"},
                   {"path": ".github/workflows/other.yml"}, {"name": "Other workflow"},
                   {"run_attempt": 2}, {"id": "456"}, {"head_sha": "invalid"})
        for change in changes:
            event = {"repository": {"full_name": "nikelef/venture-ai-ceo"},
                     "workflow_run": {**self.upstream(), **change}}
            with self.subTest(change=change), patch.dict(os.environ, self.completion_context(), clear=True), \
                    patch("scripts.validation_guard.Path.read_bytes", return_value=json.dumps(event).encode()), \
                    patch("scripts.validation_guard.build_opener") as network, self.assertRaises(SystemExit):
                main()
            network.assert_not_called()

    def test_github_must_confirm_source_identity_and_result(self):
        event = {"repository": {"full_name": "nikelef/venture-ai-ceo"}, "workflow_run": self.upstream()}
        for change in ({"head_sha": "b" * 40}, {"id": 999}, {"conclusion": "failure"}):
            with self.subTest(change=change), patch.dict(os.environ, self.completion_context(), clear=True), \
                    patch("scripts.validation_guard.Path.read_bytes", return_value=json.dumps(event).encode()), \
                    patch("scripts.validation_guard.build_opener") as network, self.assertRaises(SystemExit):
                network.return_value.open.return_value = io.BytesIO(json.dumps({**self.upstream(), **change}).encode())
                main()
            self.assertEqual(network.return_value.open.call_count, 1)

    def test_missing_malformed_or_oversized_completion_event_fails_closed(self):
        for raw in (b"not-json", b"x" * 256001, b"{}"):
            with self.subTest(size=len(raw)), patch.dict(os.environ, self.completion_context(), clear=True), \
                    patch("scripts.validation_guard.Path.read_bytes", return_value=raw), \
                    patch("scripts.validation_guard.build_opener") as network, self.assertRaises(SystemExit):
                main()
            network.assert_not_called()
