"""Build10 isolated atomic synthetic approval and audit. No MCP dispatch."""
import hashlib
import hmac
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from audit_ledger import sha

class AtomicReview:
    def __init__(self, path, clock=None):
        self.path = str(path)
        self.clock = clock or time.time
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS atomic_operations(
                operation_id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                payload_hash TEXT NOT NULL, evidence_hash TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE, expires REAL NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('pending','ready')))""")
            db.execute("""CREATE TABLE IF NOT EXISTS atomic_events(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL, event TEXT NOT NULL,
                prior_hash TEXT NOT NULL, event_hash TEXT NOT NULL)""")

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute("PRAGMA busy_timeout=10000")
            with db:
                yield db
        finally:
            db.close()

    def _event(self, db, operation_id, event):
        row = db.execute("SELECT event_hash FROM atomic_events ORDER BY seq DESC LIMIT 1").fetchone()
        prior = row[0] if row else "GENESIS"
        digest = sha({"operation_id":operation_id,"event":event,"prior_hash":prior})
        db.execute("INSERT INTO atomic_events(operation_id,event,prior_hash,event_hash) VALUES(?,?,?,?)",
                   (operation_id,event,prior,digest))

    def prepare(self, operation_id, owner, payload, evidence_hash, ttl=60):
        if not isinstance(operation_id,str) or not operation_id or not isinstance(owner,str) or not owner:
            raise ValueError("operation/owner required")
        if not isinstance(payload,dict):
            raise ValueError("payload object required")
        if not isinstance(evidence_hash,str) or len(evidence_hash)!=64 or any(c not in "0123456789abcdef" for c in evidence_hash):
            raise ValueError("lowercase evidence sha256 required")
        if isinstance(ttl,bool) or not isinstance(ttl,(int,float)) or not 0<ttl<=300:
            raise ValueError("invalid ttl")
        token=secrets.token_urlsafe(32)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO atomic_operations VALUES(?,?,?,?,?,?,?)",
                       (operation_id,owner,sha(payload),evidence_hash,
                        hashlib.sha256(token.encode()).hexdigest(),self.clock()+ttl,"pending"))
            self._event(db,operation_id,"prepared")
        return {"operation_id":operation_id,"approval_token":token,"status":"pending_owner_review",
                "network_called":False}

    def approve_dry_run(self, operation_id, token, owner, payload, fault=None):
        if not all(isinstance(v,str) and v for v in (operation_id,token,owner)):
            raise PermissionError("invalid identity")
        if not isinstance(payload,dict):
            raise PermissionError("invalid payload")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("""SELECT owner,payload_hash,token_hash,expires,state,evidence_hash
                              FROM atomic_operations WHERE operation_id=?""",(operation_id,)).fetchone()
            if (row is None or row[4]!="pending" or self.clock()>=row[3]
                or not hmac.compare_digest(row[0],owner)
                or not hmac.compare_digest(row[1],sha(payload))
                or not hmac.compare_digest(row[2],hashlib.sha256(token.encode()).hexdigest())):
                raise PermissionError("approval denied")
            if fault=="before_update":
                raise RuntimeError("synthetic crash before update")
            changed=db.execute("UPDATE atomic_operations SET state='ready' WHERE operation_id=? AND state='pending'",
                               (operation_id,)).rowcount
            if changed!=1:
                raise PermissionError("stale operation")
            if fault=="after_update":
                raise RuntimeError("synthetic crash after update")
            self._event(db,operation_id,"approved_synthetic")
            if fault=="after_event":
                raise RuntimeError("synthetic crash after event")
        return {"operation_id":operation_id,"status":"approved_once","would_call":"record_observation",
                "executed":False,"network_called":False}

    def inspect(self, operation_id):
        with self._db() as db:
            row=db.execute("SELECT state FROM atomic_operations WHERE operation_id=?",(operation_id,)).fetchone()
        return {"operation_id":operation_id,"status":row[0] if row else "unknown_operation",
                "safe_to_dispatch":False,"network_called":False}

    def verify(self):
        with self._db() as db:
            rows=db.execute("SELECT operation_id,event,prior_hash,event_hash FROM atomic_events ORDER BY seq").fetchall()
        prior="GENESIS"
        for op,event,stored,actual in rows:
            if stored!=prior or actual!=sha({"operation_id":op,"event":event,"prior_hash":prior}):
                return False
            prior=actual
        return True
