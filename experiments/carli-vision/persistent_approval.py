"""Build13 isolated SQLite approval gate; synthetic identity, no MCP execution."""
import hashlib, hmac, json, secrets, sqlite3, time
from contextlib import contextmanager

def digest(payload):
    if not isinstance(payload, dict): raise ValueError("object payload required")
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), allow_nan=False).encode()).hexdigest()

class PersistentApproval:
    def __init__(self, path, clock=None):
        self.path = str(path)
        self.clock = clock or time.time
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS approvals (
                token_hash TEXT PRIMARY KEY, owner TEXT NOT NULL, action TEXT NOT NULL,
                payload_hash TEXT NOT NULL, expires REAL NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('pending','consumed','rejected'))
            )""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=10000")
            yield db
        finally:
            db.close()

    def prepare(self, owner, action, payload, ttl=60):
        if not isinstance(owner,str) or not owner or not isinstance(action,str) or not action:
            raise ValueError("owner/action required")
        if isinstance(ttl,bool) or not isinstance(ttl,(int,float)) or not 0 < ttl <= 300:
            raise ValueError("ttl out of range")
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?)",
                       (hashlib.sha256(token.encode()).hexdigest(),owner,action,digest(payload),self.clock()+ttl,"pending"))
        return token

    def finalize(self, token, owner, action=None, payload=None, reject=False):
        if not isinstance(token,str) or not isinstance(owner,str) or not owner:
            raise PermissionError("unauthorized")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT owner,action,payload_hash,expires,state FROM approvals WHERE token_hash=?",(token_hash,)).fetchone()
                if row is None or not hmac.compare_digest(row[0],owner): raise PermissionError("unauthorized")
                if row[4] != "pending": raise PermissionError("already finalized")
                if self.clock() >= row[3]: raise PermissionError("expired")
                if not reject and (row[1] != action or not hmac.compare_digest(row[2],digest(payload))):
                    raise PermissionError("action/payload mismatch")
                changed = db.execute("UPDATE approvals SET state=? WHERE token_hash=? AND state='pending'",
                                     ("rejected" if reject else "consumed",token_hash)).rowcount
                if changed != 1: raise PermissionError("already finalized")
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return {"status":"rejected" if reject else "approved_once","owner":owner,
                "action":None if reject else action,"payload":None if reject else payload,"mcp_tool_invoked":False}

    def approve(self,token,authenticated_owner,action,payload):
        return self.finalize(token,authenticated_owner,action,payload)

    def reject(self,token,authenticated_owner):
        return self.finalize(token,authenticated_owner,reject=True)

def mcp_dry_run(result):
    if result.get("status") != "approved_once" or result.get("mcp_tool_invoked") is not False:
        raise PermissionError("approval required")
    if result.get("action") != "record_observation":
        raise PermissionError("action not allowlisted")
    return {"schema":"carli-mcp-dry-run/1","would_call":"record_observation",
            "payload":result["payload"],"executed":False,"network_called":False}
