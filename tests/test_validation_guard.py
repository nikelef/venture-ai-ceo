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
