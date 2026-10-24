"""Synthetic in-memory single-use approval gate; NOT production authentication."""
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import time

def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)

@dataclass
class Record:
    owner: str
    action: str
    digest: str
    expires: float
    state: str = "pending"

class ApprovalGate:
    def __init__(self, clock=None):
        self.clock = clock or time.monotonic
        self._records = {}

    def prepare(self, owner: str, action: str, payload: dict, ttl: int = 60) -> str:
        if not owner or not action or not isinstance(payload, dict) or not 0 < ttl <= 300:
            raise ValueError("invalid proposal")
        token = secrets.token_urlsafe(32)
        self._records[token] = Record(owner, action, hashlib.sha256(canonical(payload).encode()).hexdigest(), self.clock() + ttl)
        return token

    def reject(self, token: str, authenticated_owner: str) -> None:
        rec = self._require(token, authenticated_owner)
        if rec.state != "pending":
            raise PermissionError("proposal no longer pending")
        rec.state = "rejected"

    def approve(self, token: str, authenticated_owner: str, action: str, payload: dict) -> dict:
        rec = self._require(token, authenticated_owner)
        if rec.state != "pending":
            raise PermissionError("proposal no longer pending")
        digest = hashlib.sha256(canonical(payload).encode()).hexdigest()
        if rec.action != action or not hmac.compare_digest(rec.digest, digest):
            raise PermissionError("action or payload mismatch")
        rec.state = "consumed"
        return {"status": "approved_once", "action": action, "payload": payload, "owner": authenticated_owner}

    def _require(self, token, owner):
        rec = self._records.get(token)
        if rec is None or not owner or not hmac.compare_digest(rec.owner, owner):
            raise PermissionError("unauthorized")
        if self.clock() >= rec.expires:
            rec.state = "expired"
            raise PermissionError("expired")
        return rec
