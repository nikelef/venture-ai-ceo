"""Local append-only, hash-chained audit and execution limits.

This detects edits within the retained chain. It is not an externally anchored,
immutable ledger: a machine administrator can replace the whole database.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ai_ceo.policy import PolicyDenied


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "research.sqlite3"
        self.connection = sqlite3.connect(self.path, timeout=10)
        self.connection.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS events (
              seq INTEGER PRIMARY KEY, created_at TEXT NOT NULL,
              kind TEXT NOT NULL, payload TEXT NOT NULL,
              previous_hash TEXT NOT NULL, digest TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
              BEGIN SELECT RAISE(ABORT, 'audit is append only'); END;
            CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
              BEGIN SELECT RAISE(ABORT, 'audit is append only'); END;
            CREATE TABLE IF NOT EXISTS runs (
              id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.connection.close()

    def _append(self, kind: str, payload: dict) -> str:
        last = self.connection.execute("SELECT digest FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0" * 64
        timestamp, body = utcnow(), canonical(payload)
        digest = hashlib.sha256(canonical([timestamp, kind, body, previous]).encode()).hexdigest()
        self.connection.execute("INSERT INTO events(created_at,kind,payload,previous_hash,digest) VALUES(?,?,?,?,?)",
                                (timestamp, kind, body, previous, digest))
        return digest

    def append(self, kind: str, payload: dict) -> str:
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            return self._append(kind, payload)

    def verify(self) -> int:
        previous, count = "0" * 64, 0
        for timestamp, kind, body, old, digest in self.connection.execute(
            "SELECT created_at,kind,payload,previous_hash,digest FROM events ORDER BY seq"
        ):
            calculated = hashlib.sha256(canonical([timestamp, kind, body, previous]).encode()).hexdigest()
            if old != previous or digest != calculated:
                raise PolicyDenied("Audit chain integrity check failed")
            previous, count = digest, count + 1
        return count

    def start_run(self, max_per_day: int, max_failures: int) -> str:
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            self.verify()
            now = utcnow()
            count = self.connection.execute("SELECT COUNT(*) FROM runs WHERE created_at LIKE ?",
                                            (now[:10] + "%",)).fetchone()[0]
            recent = self.connection.execute("SELECT status FROM runs ORDER BY rowid DESC LIMIT ?",
                                             (max_failures,)).fetchall()
            if count >= max_per_day:
                raise PolicyDenied("Daily execution ceiling reached")
            if any(row[0] == "running" for row in recent):
                raise PolicyDenied("Another run is active or needs crash recovery review")
            if len(recent) == max_failures and all(row[0] == "failed" for row in recent):
                raise PolicyDenied("Failure circuit breaker is open")
            run_id = uuid.uuid4().hex
            self.connection.execute("INSERT INTO runs VALUES(?,?,?)", (run_id, now, "running"))
            self._append("run_started", {"run_id": run_id, "authorized_outlay_eur": "0"})
            return run_id

    def finish_run(self, run_id: str, *, success: bool, evidence: dict) -> str:
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            status = "complete" if success else "failed"
            updated = self.connection.execute("UPDATE runs SET status=? WHERE id=? AND status='running'",
                                              (status, run_id)).rowcount
            if updated != 1:
                raise PolicyDenied("Run cannot be finalized twice")
            return self._append("run_" + status, {"run_id": run_id, **evidence})

    def backup(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.resolve() == self.path.resolve():
            raise ValueError("Backup must be a separate file")
        with closing(sqlite3.connect(destination)) as backup:
            self.connection.backup(backup)
            if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
