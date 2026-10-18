import copy
import hashlib
import hmac
import json
import os
import secrets
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from ai_ceo.audit import Store
from ai_ceo.commerce import (TestCommerce, create_hosted_checkout, reconcile_test_transactions,
                             test_checkout_parameters, verify_signature)
from ai_ceo.policy import PolicyDenied


class CommerceTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".tmp" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.environment = patch.dict(os.environ, {"AI_CEO_DATA_DIR": self.temp.name}, clear=True)
        self.environment.start()
        self.store = Store(Path(self.temp.name))
        self.commerce = TestCommerce(self.store)
        self.order_id = self.commerce.create_order()
        self.secret = secrets.token_hex(32)  # Ephemeral test-only signature key; never printed or stored.
        self.now = 1800000000
        self.event = {"id": "evt_synthetic_1", "object": "event", "livemode": False,
            "type": "checkout.session.completed", "data": {"object": {
                "id": "cs_test_synthetic", "object": "checkout.session", "livemode": False,
                "mode": "payment", "status": "complete", "payment_status": "paid", "amount_total": 900,
                "currency": "eur", "metadata": {"order_id": self.order_id}}}}

    def tearDown(self):
        self.store.close()
        self.environment.stop()
        self.temp.cleanup()

    def signed(self, event=None, timestamp=None):
        timestamp = self.now if timestamp is None else timestamp
        payload = json.dumps(self.event if event is None else event).encode()
        signature = hmac.new(self.secret.encode(), str(timestamp).encode() + b"." + payload, hashlib.sha256).hexdigest()
        return payload, f"t={timestamp},v1={signature}"

    def ingest(self, event=None):
        payload, signature = self.signed(event)
        return self.commerce.ingest(payload, signature, self.secret, now=self.now)

    def test_raw_signature_validates_and_rejects_tamper_expiry_future_and_duplicate_timestamp(self):
        payload, signature = self.signed()
        self.assertEqual(verify_signature(payload, signature, self.secret, now=self.now)["id"], self.event["id"])
        for body, header, now in ((payload + b" ", signature, self.now), (payload, signature, self.now + 301),
                                  (payload, signature, self.now - 301), (payload, signature + f",t={self.now}", self.now)):
            with self.assertRaises(ValueError):
                verify_signature(body, header, self.secret, now=now)

    def test_rotation_allows_any_valid_v1_signature(self):
        payload, signature = self.signed()
        header = signature + ",v1=" + "0" * 64
        self.assertEqual(verify_signature(payload, header, self.secret, now=self.now)["id"], self.event["id"])

    def test_malformed_signed_data_does_not_modify_orders(self):
        for data in (None, [], {"object": []}, {"object": None}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.ingest({**self.event, "data": data})
        self.assertEqual(self.store.connection.execute("SELECT status FROM test_orders WHERE id=?", (self.order_id,)).fetchone()[0], "pending")

    def test_live_and_unknown_mode_events_never_enter_test_ledger(self):
        for mode in (True, None, 0):
            event = {**self.event, "livemode": mode}
            with self.assertRaises(PolicyDenied):
                self.ingest(event)
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM test_webhooks").fetchone()[0], 0)

    def test_unpaid_completed_event_does_not_fulfill_but_later_async_paid_event_can(self):
        unpaid = copy.deepcopy(self.event)
        unpaid["data"]["object"]["payment_status"] = "unpaid"
        self.assertEqual(self.ingest(unpaid), "ignored_test_event")
        with self.assertRaises(PolicyDenied):
            self.commerce.fulfill(self.order_id)
        delayed = {**self.event, "id": "evt_synthetic_delayed", "type": "checkout.session.async_payment_succeeded"}
        self.assertEqual(self.ingest(delayed), "test_paid_not_revenue")
        self.assertTrue(self.commerce.fulfill(self.order_id).is_file())

    def test_order_amount_currency_and_reference_must_match(self):
        for field, value in (("amount_total", 1), ("amount_total", True), ("currency", "usd"), ("status", "open"),
                             ("metadata", {"order_id": "unknown"})):
            event = copy.deepcopy(self.event)
            event["data"]["object"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.ingest(event)
        with self.assertRaises(PolicyDenied):
            self.commerce.fulfill(self.order_id)

    def test_webhook_and_fulfillment_replays_are_idempotent_and_auditable(self):
        self.assertEqual(self.ingest(), "test_paid_not_revenue")
        count = self.store.verify()
        self.assertEqual(self.ingest(), "test_paid_not_revenue")
        self.assertEqual(self.store.verify(), count)
        artifact = self.commerce.fulfill(self.order_id)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        self.assertEqual(self.commerce.fulfill(self.order_id), artifact)
        self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), digest)
        with zipfile.ZipFile(artifact) as bundle:
            self.assertIsNone(bundle.testzip())
            self.assertIn("catalog.js", bundle.namelist())
            self.assertIn("NOT A PURCHASE OR REVENUE", bundle.read("READ-ME.txt").decode())
        altered = {**self.event, "type": "different"}
        with self.assertRaises(ValueError):
            self.ingest(altered)
        artifact.write_bytes(b"changed")
        with self.assertRaises(PolicyDenied):
            self.commerce.fulfill(self.order_id)

    def test_checkout_is_blocked_and_only_pure_test_parameters_can_be_built(self):
        params = test_checkout_parameters(self.order_id, "https://example.org")
        self.assertEqual(params["line_items[0][price_data][unit_amount]"], 900)
        self.assertEqual(params["metadata[order_id]"], self.order_id)
        for url in ("https://localhost/", "https://example.org/?redirect=other", "https://example.org/unreviewed"):
            with self.assertRaises(ValueError):
                test_checkout_parameters(self.order_id, url)
        with self.assertRaises(PolicyDenied):
            create_hosted_checkout(self.order_id)

    def test_reconciliation_keeps_currencies_fees_refunds_and_costs_separate(self):
        rows = [{"id": "txn_test_1", "currency": "eur", "type": "charge", "amount": 1000, "fee": 50,
                 "livemode": False, "status": "available"},
                {"id": "txn_test_2", "currency": "eur", "type": "refund", "amount": -200, "fee": 0,
                 "livemode": False, "status": "available"},
                {"id": "txn_test_3", "currency": "usd", "type": "charge", "amount": 500, "fee": None,
                 "livemode": False, "status": "available"}]
        result = reconcile_test_transactions(rows, {"eur": 100})
        self.assertEqual(result["currencies"]["eur"]["gross_captured_minor"], 1000)
        self.assertEqual(result["currencies"]["eur"]["refunds_minor"], 200)
        self.assertEqual(result["currencies"]["eur"]["net_after_processor_costs_minor"], 750)
        self.assertEqual(result["currencies"]["eur"]["contribution_minor"], 650)
        self.assertIsNone(result["currencies"]["usd"]["net_after_processor_costs_minor"])
        self.assertFalse(result["is_revenue"])
        for altered in ([rows[0], rows[0]], [{**rows[0], "livemode": True}], [{**rows[0], "type": "transfer"}],
                        [{**rows[0], "amount": 1.5}], [{**rows[0], "status": "pending"}]):
            with self.assertRaises(ValueError):
                reconcile_test_transactions(altered)


if __name__ == "__main__":
    unittest.main()
