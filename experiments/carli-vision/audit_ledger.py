"""Build 14: isolated SQLite transactional audit and recovery model.

Synthetic identity only. Never calls MCP. Hash chain is tamper-evident only
against accidental edits, not a trusted external append-only ledger.
"""
import hashlib
import json
import sqlite3
import time
import uuid

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)

def sha(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

class AuditLedger:
    def __init__(self, path, clock=None):
        self.path = str(path)
        self.clock = clock or time.time
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS operations(
                operation_id TEXT PRIMARY KEY, evidence_hash TEXT NOT NULL,
                payload_hash TEXT NOT NULL, state TEXT NOT NULL
                CHECK(state IN ('pending','rejected','ready','dispatched_unknown','resolved_manual'))
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS audit_events(
                seq INTEGER PRIMARY KEY AUTOINCREMENT, operation_id TEXT NOT NULL,
                event TEXT NOT NULL, detail TEXT NOT NULL, prior_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL)""")

    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _append(self, db, operation_id, event, detail):
        previous = db.execute("SELECT event_hash FROM audit_events ORDER BY seq DESC LIMIT 1").fetchone()
        prior = previous[0] if previous else "GENESIS"
        record = {"operation_id":operation_id,"event":event,"detail":detail,"prior_hash":prior}
        db.execute("INSERT INTO audit_events(operation_id,event,detail,prior_hash,event_hash) VALUES(?,?,?,?,?)",
                   (operation_id,event,canonical(detail),prior,sha(record)))

    def prepare(self, evidence_hash, payload, operation_id=None):
        if not isinstance(evidence_hash,str) or len(evidence_hash)!=64 or any(c not in "0123456789abcdef" for c in evidence_hash):
            raise ValueError("lowercase SHA256 required")
        if not isinstance(payload,dict): raise ValueError("payload object required")
        operation_id = operation_id or str(uuid.uuid4())
        with self.db() as db:
            existing = db.execute("SELECT evidence_hash,payload_hash FROM operations WHERE operation_id=?",(operation_id,)).fetchone()
            if existing:
                if existing != (evidence_hash,sha(payload)): raise ValueError("operation ID collision")
                return operation_id
            db.execute("INSERT INTO operations VALUES(?,?,?,?)",(operation_id,evidence_hash,sha(payload),"pending"))
            self._append(db,operation_id,"prepared",{"evidence_hash":evidence_hash,"payload_hash":sha(payload)})
        return operation_id

    def transition(self, operation_id, expected, new_state, event):
        allowed={("pending","ready"),("pending","rejected"),("ready","dispatched_unknown"),("dispatched_unknown","resolved_manual")}
        if (expected,new_state) not in allowed: raise ValueError("invalid transition")
        with self.db() as db:
            changed=db.execute("UPDATE operations SET state=? WHERE operation_id=? AND state=?",
                               (new_state,operation_id,expected)).rowcount
            if changed != 1: raise PermissionError("stale or duplicate transition")
            self._append(db,operation_id,event,{"from":expected,"to":new_state})
        return new_state

    def dry_run(self, operation_id):
        with self.db() as db:
            row=db.execute("SELECT state,evidence_hash,payload_hash FROM operations WHERE operation_id=?",(operation_id,)).fetchone()
        if row is None or row[0]!="ready": raise PermissionError("not ready")
        return {"operation_id":operation_id,"evidence_hash":row[1],"payload_hash":row[2],
                "would_call":"record_observation","executed":False,"network_called":False}

    def verify(self):
        with self.db() as db:
            rows=db.execute("SELECT operation_id,event,detail,prior_hash,event_hash FROM audit_events ORDER BY seq").fetchall()
        prior="GENESIS"
        for operation_id,event,detail,stored_prior,event_hash in rows:
            if stored_prior != prior: return False
            try: detail_obj=json.loads(detail)
            except (ValueError,TypeError): return False
            if sha({"operation_id":operation_id,"event":event,"detail":detail_obj,"prior_hash":prior}) != event_hash:
                return False
            prior=event_hash
        return True

    def unresolved(self):
        with self.db() as db:
            return db.execute("SELECT operation_id,state FROM operations WHERE state='dispatched_unknown' ORDER BY operation_id").fetchall()
