"""Inactive commerce components, exercised with synthetic test events only.

No live events, live requests, emails, refunds, payouts or money notifications
are supported. The storefront has no checkout. Live activation needs a separate
readiness review, provider onboarding and independently verified evidence.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
import uuid
import zipfile
from pathlib import Path

from ai_ceo.audit import Store
from ai_ceo.policy import Action, PolicyDenied, authorize
from ai_ceo.worker import public_https

ROOT = Path(__file__).resolve().parent.parent
BUNDLE_FILES = ("index.html", "catalog.js", "app.js", "style.css", "review-notice.html")


def verify_signature(payload: bytes, header: str, endpoint_secret: str, *, now: int | None = None) -> dict:
    """Verify Stripe's timestamp + raw-body v1 HMAC; do not log any inputs."""
    if not isinstance(payload, bytes) or len(payload) > 262_144:
        raise ValueError("Webhook body is invalid or too large")
    if not isinstance(endpoint_secret, str) or len(endpoint_secret) < 16 or not isinstance(header, str) or len(header) > 2048:
        raise ValueError("Missing webhook configuration or invalid header")
    fields = [part.strip().split("=", 1) for part in header.split(",")]
    timestamps = [value for item in fields if len(item) == 2 for key, value in [item] if key == "t"]
    signatures = [value for item in fields if len(item) == 2 for key, value in [item] if key == "v1"]
    if len(timestamps) != 1 or not re.fullmatch(r"[0-9]{1,12}", timestamps[0]):
        raise ValueError("Invalid webhook timestamp")
    timestamp = int(timestamps[0])
    if abs((int(time.time()) if now is None else now) - timestamp) > 300:
        raise ValueError("Webhook timestamp outside tolerance")
    expected = hmac.new(endpoint_secret.encode("utf-8"), timestamps[0].encode("ascii") + b"." + payload, hashlib.sha256).hexdigest()
    if not any(re.fullmatch(r"[a-f0-9]{64}", signature) and hmac.compare_digest(expected, signature) for signature in signatures):
        raise ValueError("Webhook signature verification failed")
    event = json.loads(payload)
    if not isinstance(event, dict) or event.get("object") != "event" or not re.fullmatch(r"evt_[A-Za-z0-9_]{1,100}", str(event.get("id", ""))):
        raise ValueError("Invalid event envelope")
    return event


def test_checkout_parameters(order_id: str, base_url: str) -> dict[str, str | int]:
    """Pure request shape for a hypothetical EUR 9 test order; no API call."""
    if not re.fullmatch(r"[a-f0-9]{32}", order_id) or not public_https(base_url):
        raise ValueError("Invalid checkout reference or base URL")
    from urllib.parse import urlsplit
    parsed = urlsplit(base_url)
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("Checkout return host must not contain a path, query or fragment")
    return {"mode": "payment", "client_reference_id": order_id, "metadata[order_id]": order_id,
            "line_items[0][price_data][currency]": "eur", "line_items[0][price_data][unit_amount]": 900,
            "line_items[0][price_data][product_data][name]": "Catalog Preflight offline toolkit — TEST",
            "line_items[0][quantity]": 1, "success_url": base_url.rstrip("/") + "/order-status",
            "cancel_url": base_url.rstrip("/") + "/"}


def create_hosted_checkout(*_args, **_kwargs):
    authorize(Action.PAYMENT)
    raise PolicyDenied("Hosted checkout activation is not implemented for live use")


class TestCommerce:
    """Persistent test-only state. Nothing recorded here is revenue."""
    def __init__(self, store: Store):
        self.store = store
        self.store.connection.executescript("""
          CREATE TABLE IF NOT EXISTS test_orders (
            id TEXT PRIMARY KEY, amount_minor INTEGER NOT NULL, currency TEXT NOT NULL,
            status TEXT NOT NULL, artifact_hash TEXT);
          CREATE TABLE IF NOT EXISTS test_webhooks (
            id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, outcome TEXT NOT NULL);
        """)

    def create_order(self) -> str:
        authorize(Action.LOCAL_PRODUCT, data_dir=self.store.path.parent)
        order_id = uuid.uuid4().hex
        with self.store.connection:
            self.store.connection.execute("BEGIN IMMEDIATE")
            self.store.verify()
            self.store.connection.execute("INSERT INTO test_orders VALUES(?,900,'eur','pending',NULL)", (order_id,))
            self.store._append("test_order_created", {"order_id": order_id, "is_revenue": False})
        return order_id

    def ingest(self, payload: bytes, signature: str, secret: str, *, now: int | None = None) -> str:
        authorize(Action.LOCAL_PRODUCT, data_dir=self.store.path.parent)
        event = verify_signature(payload, signature, secret, now=now)
        if event.get("livemode") is not False:
            raise PolicyDenied("Live payment events are forbidden in this research pilot")
        digest = hashlib.sha256(payload).hexdigest()
        with self.store.connection:
            self.store.connection.execute("BEGIN IMMEDIATE")
            self.store.verify()
            prior = self.store.connection.execute("SELECT payload_hash,outcome FROM test_webhooks WHERE id=?", (event["id"],)).fetchone()
            if prior:
                if prior[0] != digest:
                    raise ValueError("Event ID reused with a different body")
                return prior[1]
            outcome = "ignored_test_event"
            if event.get("type") in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
                data = event.get("data")
                if not isinstance(data, dict) or not isinstance(data.get("object"), dict):
                    raise ValueError("Invalid checkout data envelope")
                session = data["object"]
                if session.get("livemode") is not False or session.get("object") != "checkout.session" or session.get("mode") != "payment":
                    raise ValueError("Invalid test checkout session")
                if session.get("payment_status") == "paid":
                    metadata = session.get("metadata")
                    if not isinstance(metadata, dict) or not isinstance(metadata.get("order_id"), str) or not re.fullmatch(r"[a-f0-9]{32}", metadata["order_id"]):
                        raise ValueError("Invalid order metadata")
                    order_id = metadata["order_id"]
                    order = self.store.connection.execute("SELECT amount_minor,currency FROM test_orders WHERE id=?", (order_id,)).fetchone()
                    if order is None or type(session.get("amount_total")) is not int or (session["amount_total"], session.get("currency")) != order:
                        raise ValueError("Test checkout does not match an existing order")
                    if session.get("status") != "complete" or not re.fullmatch(r"cs_test_[A-Za-z0-9_]+", str(session.get("id", ""))):
                        raise ValueError("Test session is incomplete or missing its provider reference")
                    self.store.connection.execute("UPDATE test_orders SET status='test_paid' WHERE id=? AND status='pending'", (order_id,))
                    outcome = "test_paid_not_revenue"
            self.store.connection.execute("INSERT INTO test_webhooks VALUES(?,?,?)", (event["id"], digest, outcome))
            self.store._append("test_webhook_processed", {"provider_event_id": event["id"], "payload_sha256": digest,
                                                         "outcome": outcome, "is_revenue": False})
            return outcome

    def fulfill(self, order_id: str) -> Path:
        authorize(Action.LOCAL_PRODUCT, data_dir=self.store.path.parent)
        if not re.fullmatch(r"[a-f0-9]{32}", order_id):
            raise ValueError("Invalid test order identifier")
        with self.store.connection:
            self.store.connection.execute("BEGIN IMMEDIATE")
            self.store.verify()
            order = self.store.connection.execute("SELECT status,artifact_hash FROM test_orders WHERE id=?", (order_id,)).fetchone()
            if order is None or order[0] not in {"test_paid", "test_fulfilled"}:
                raise PolicyDenied("Test order has no signed matching paid event")
            directory = self.store.path.parent / "test_fulfillment"
            directory.mkdir(exist_ok=True)
            artifact = directory / f"{order_id}.zip"
            if order[0] == "test_fulfilled":
                if not artifact.exists() or hashlib.sha256(artifact.read_bytes()).hexdigest() != order[1]:
                    raise PolicyDenied("Fulfillment artifact integrity check failed")
                return artifact
            temporary = artifact.with_suffix(".zip.tmp")
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for name in BUNDLE_FILES:
                    bundle.writestr(name, (ROOT / "web" / name).read_bytes())
                bundle.writestr("READ-ME.txt", "SYNTHETIC TEST FULFILLMENT — NOT A PURCHASE OR REVENUE.\n"
                    "Run locally: python -m http.server 8000 --bind 127.0.0.1\n"
                    "Open http://127.0.0.1:8000/ . See the included prototype readiness notice.\n")
            with zipfile.ZipFile(temporary) as bundle:
                if bundle.testzip() is not None:
                    raise RuntimeError("Fulfillment ZIP is corrupt")
            temporary.replace(artifact)
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.store.connection.execute("UPDATE test_orders SET status='test_fulfilled',artifact_hash=? WHERE id=?", (digest, order_id))
            self.store._append("test_order_fulfilled", {"order_id": order_id, "artifact_sha256": digest, "is_revenue": False})
            return artifact


def reconcile_test_transactions(transactions: list[dict], operating_costs: dict[str, int] | None = None) -> dict:
    """Integer-minor-unit accounting exercise, never verified external revenue.

    This deliberately accepts only explicitly labeled test inputs and a small
    subset of transaction types. It is not a complete Stripe ledger importer.
    """
    if len(transactions) > 1000:
        raise ValueError("Reconciliation input limit exceeded")
    totals, seen = {}, set()
    for item in transactions:
        if item.get("livemode") is not False or item.get("status") != "available":
            raise ValueError("Only explicitly labeled available test transactions are supported")
        identity, currency = item.get("id"), item.get("currency")
        if not isinstance(identity, str) or not identity.startswith("txn_") or identity in seen:
            raise ValueError("Missing or duplicate transaction reference")
        if not isinstance(currency, str) or not re.fullmatch(r"[a-z]{3}", currency):
            raise ValueError("Invalid currency")
        amount, fee = item.get("amount"), item.get("fee")
        if type(amount) is not int or abs(amount) > 10**12 or fee is not None and (type(fee) is not int or abs(fee) > 10**12):
            raise ValueError("Invalid integer monetary amount")
        kind = item.get("type")
        if kind not in {"charge", "refund"} or (kind == "charge" and amount < 0) or (kind == "refund" and amount > 0):
            raise ValueError("Unsupported transaction type or sign; transfers are never revenue")
        seen.add(identity)
        total = totals.setdefault(currency, {"gross_captured_minor": 0, "refunds_minor": 0,
            "known_fees_minor": 0, "fees_complete": True, "operating_cost_minor": 0})
        total["gross_captured_minor" if kind == "charge" else "refunds_minor"] += amount if kind == "charge" else -amount
        if fee is None:
            total["fees_complete"] = False
        else:
            total["known_fees_minor"] += fee
    for currency, cost in (operating_costs or {}).items():
        if currency not in totals or type(cost) is not int or not 0 <= cost <= 10**12:
            raise ValueError("Invalid operating cost or unknown currency")
        totals[currency]["operating_cost_minor"] = cost
    for total in totals.values():
        net = total["gross_captured_minor"] - total["refunds_minor"] - total["known_fees_minor"] if total["fees_complete"] else None
        total["net_after_processor_costs_minor"] = net
        total["contribution_minor"] = None if net is None else net - total["operating_cost_minor"]
    return {"mode": "synthetic_test_only", "is_revenue": False, "external_evidence_verified": False,
            "currencies": totals, "taxes_and_disputes_reconciled": False}
