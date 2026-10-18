import contextlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_ceo.audit import Store
from ai_ceo.opportunities import ranked
from ai_ceo.policy import Action, PolicyDenied, authorize
from ai_ceo.scheduler import run as schedule
from ai_ceo.worker import DEFAULT_EVIDENCE, fetch_feed, main, public_https, query_model, validate
from test_worker import IDEA, SOURCES


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".tmp" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.directory = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {"AI_CEO_DATA_DIR": str(self.directory)}, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def test_zero_budget_rejects_all_spending_and_external_authority(self):
        authorize(Action.RESEARCH)
        for action in (Action.MODEL, Action.PAYMENT, Action.PUBLISH, Action.NOTIFY, "research"):
            with self.subTest(action=action), self.assertRaises(PolicyDenied):
                authorize(action)
        for amount in ("0.01", "-1", "NaN", "Infinity"):
            with self.subTest(amount=amount), self.assertRaises(PolicyDenied):
                authorize(Action.RESEARCH, cost_eur=amount)

    def test_environment_cannot_raise_budget(self):
        for amount in ("100", "NaN", "Infinity", "garbage"):
            with patch.dict(os.environ, {"MONTHLY_BUDGET_EUR": amount}), self.assertRaises(PolicyDenied):
                authorize(Action.RESEARCH)

    def test_shutdown_and_payments_switch_fail_closed(self):
        for key in ("AI_CEO_SHUTDOWN", "PAYMENTS_ENABLED"):
            with patch.dict(os.environ, {key: "true"}), self.assertRaises(PolicyDenied):
                authorize(Action.RESEARCH)
        (self.directory / "STOP").touch()
        with self.assertRaises(PolicyDenied):
            authorize(Action.RESEARCH, data_dir=self.directory)

    def test_configured_model_cannot_make_billable_request(self):
        with patch.dict(os.environ, {"AI_API_KEY": "test-placeholder", "AI_API_BASE_URL": "https://example.org/v1",
                                     "AI_MODEL": "example", "MAX_LLM_CALLS_PER_RUN": "1"}), \
                patch("urllib.request.build_opener") as network:
            with self.assertRaises(PolicyDenied):
                query_model(SOURCES)
            network.assert_not_called()

    def test_feed_allowlist_and_private_link_rejection(self):
        with patch("urllib.request.build_opener") as network:
            with self.assertRaises(PolicyDenied):
                fetch_feed("https://127.0.0.1/private")
            network.assert_not_called()
        for url in ("http://example.org", "https://localhost/x", "https://10.0.0.1", "https://[::1]/",
                    "https://user:password@example.org/", "https://example.org:8443/", "https://host.local/"):
            self.assertFalse(public_https(url), url)
        self.assertTrue(public_https("https://example.org/signal"))

    def test_boolean_score_and_nonfinite_price_are_rejected(self):
        for value in ({**IDEA, "score": True}, {**IDEA, "price_hypothesis_eur": float("nan")}):
            with self.assertRaises(ValueError):
                validate(value, SOURCES)

    def test_audit_append_only_backup_and_tamper_detection(self):
        store = Store(self.directory)
        try:
            store.append("checked", {"outlay_eur": "0"})
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE events SET payload='{}'")
            store.connection.rollback()
            self.assertEqual(store.verify(), 1)
            backup = self.directory / "backups" / "copy.sqlite3"
            store.backup(backup)
            with contextlib.closing(sqlite3.connect(backup)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], 1)
            store.connection.execute("DROP TRIGGER events_no_update")
            store.connection.execute("UPDATE events SET payload='{}'")
            store.connection.commit()
            with self.assertRaises(PolicyDenied):
                store.verify()
        finally:
            store.close()

    def test_execution_ceiling_and_in_progress_lock(self):
        store = Store(self.directory)
        try:
            run_id = store.start_run(1, 3)
            with self.assertRaises(PolicyDenied):
                store.start_run(4, 3)
            store.finish_run(run_id, success=True, evidence={})
            with self.assertRaises(PolicyDenied):
                store.start_run(1, 3)
            with self.assertRaises(PolicyDenied):
                store.finish_run(run_id, success=True, evidence={})
        finally:
            store.close()

    def test_failure_breaker(self):
        store = Store(self.directory)
        try:
            for _ in range(3):
                run_id = store.start_run(4, 3)
                store.finish_run(run_id, success=False, evidence={"error_type": "TestFailure"})
            with self.assertRaises(PolicyDenied):
                store.start_run(4, 3)
        finally:
            store.close()

    def test_ten_ranked_opportunities_keep_assumptions_explicit(self):
        candidates, sources = ranked(DEFAULT_EVIDENCE)
        self.assertEqual(len(candidates), 10)
        self.assertEqual(candidates[0]["id"], "catalog-preflight")
        self.assertEqual(candidates[0]["weighted_score"], 75)
        self.assertTrue(all(not item["demand_validated"] for item in candidates))
        self.assertEqual(len(sources), 9)

    def test_complete_offline_run_never_calls_network_or_claims_live_operation(self):
        with patch("urllib.request.build_opener") as network, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([]), 0)
            self.assertEqual(main(["--health"]), 0)
            network.assert_not_called()
        report = json.loads((self.directory / "decision.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "research_only")
        self.assertFalse(report["is_revenue"])
        self.assertEqual(report["model_calls"], 0)
        self.assertFalse(report["metadata"]["cloud_schedule_verified"])
        self.assertEqual(len(list((self.directory / "backups").glob("*.sqlite3"))), 1)

    def test_scheduler_stops_on_first_error_and_checks_shutdown_while_waiting(self):
        calls = []
        def failed(_):
            calls.append(1)
            return 2
        self.assertEqual(schedule(4, 60, worker=failed, sleep=lambda _: self.fail("must not sleep")), 2)
        self.assertEqual(calls, [1])
        def stop(_):
            (self.directory / "STOP").touch()
        with self.assertRaises(PolicyDenied):
            schedule(2, 60, worker=lambda _: 0, sleep=stop)


if __name__ == "__main__":
    unittest.main()
