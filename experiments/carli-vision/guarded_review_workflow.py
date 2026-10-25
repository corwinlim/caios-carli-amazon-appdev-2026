"""P0-A Build2: guarded offline adapter around the existing ReviewWorkflow.

Only use this adapter in the demo. Direct ReviewWorkflow calls remain unguarded.
Not a production identity provider, no live MCP calls.
"""
from build15_workflow import ReviewWorkflow
from trusted_identity import verify_owner_token

class GuardedReviewWorkflow:
    def __init__(self, directory, *, secret, clock=None, token_clock=None,
                 revoked_subjects=()):
        if not isinstance(secret, bytes) or len(secret) < 16:
            raise ValueError("demo secret must be at least 16 bytes")
        self._workflow = ReviewWorkflow(directory, clock=clock)
        self._secret = secret
        self._token_clock = token_clock
        self._revoked_subjects = revoked_subjects

    def _identity(self, identity_token, pet_id):
        if not isinstance(pet_id, str) or not pet_id:
            raise PermissionError("pet_id required")
        return verify_owner_token(
            identity_token, secret=self._secret, pet_id=pet_id,
            scope="care:propose", now=self._token_clock,
            revoked_subjects=self._revoked_subjects,
        )["verified_owner_id"]

    def prepare(self, *, identity_token, pet_id, action, payload,
                evidence_sha256, operation_id):
        owner = self._identity(identity_token, pet_id)
        if not isinstance(payload, dict) or payload.get("pet_id") != pet_id:
            raise PermissionError("payload pet_id mismatch")
        return self._workflow.prepare(owner, action, payload, evidence_sha256, operation_id)

    def approve_dry_run(self, *, identity_token, pet_id, operation_id,
                        approval_token, payload):
        owner = self._identity(identity_token, pet_id)
        if not isinstance(payload, dict) or payload.get("pet_id") != pet_id:
            raise PermissionError("payload pet_id mismatch")
        return self._workflow.approve_dry_run(
            operation_id, approval_token, owner, payload
        )
