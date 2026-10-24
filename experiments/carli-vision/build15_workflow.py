"""Build 15: isolated orchestration of SQLite approval and audit, no MCP network calls.

WARNING: approval and audit live in different SQLite transactions; a crash
between them requires manual reconciliation. No exactly-once guarantee.
"""
import hashlib
from pathlib import Path
from persistent_approval import PersistentApproval
from audit_ledger import AuditLedger

class ReviewWorkflow:
    def __init__(self, directory, clock=None):
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        self.approvals = PersistentApproval(root / "approval.sqlite", clock=clock)
        self.audit = AuditLedger(root / "audit.sqlite", clock=clock)

    def prepare(self, owner, action, payload, evidence_sha256, operation_id):
        if action != "record_observation":
            raise PermissionError("only record_observation is allowed")
        # Register operation before issuing approval token. If interrupted,
        # pending operation remains inert and requires a fresh operator review.
        self.audit.prepare(evidence_sha256, payload, operation_id)
        token = self.approvals.prepare(owner, action, payload)
        return {"operation_id":operation_id, "approval_token":token,
                "status":"pending_owner_review", "mcp_tool_invoked":False}

    def approve_dry_run(self, operation_id, token, authenticated_owner, payload):
        # Do not permit replay if operation was previously moved out of pending.
        with self.audit.db() as db:
            row = db.execute("SELECT state,payload_hash FROM operations WHERE operation_id=?",(operation_id,)).fetchone()
        if row is None or row[0] != "pending":
            raise PermissionError("operation is not pending")
        from audit_ledger import sha
        if row[1] != sha(payload):
            raise PermissionError("operation payload mismatch")
        approval = self.approvals.approve(token,authenticated_owner,"record_observation",payload)
        # Failure here leaves consumed approval + pending audit. Fail closed.
        self.audit.transition(operation_id,"pending","ready","approved_synthetic")
        result = self.audit.dry_run(operation_id)
        result["owner_approval"] = approval["status"]
        return result

    def mark_uncertain_without_network(self, operation_id):
        # Only a synthetic fault-injection marker; NEVER executes MCP.
        return self.audit.transition(operation_id,"ready","dispatched_unknown","simulated_dispatch_uncertain")
