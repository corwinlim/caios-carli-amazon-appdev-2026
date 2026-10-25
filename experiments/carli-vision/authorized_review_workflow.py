"""P0-A Build3: fail-closed authorization boundary for offline workflow.

Authoritative pet access must be checked on EACH operation. This is a demo
integration boundary, not a production identity provider or complete isolation
from direct imports of legacy ReviewWorkflow.
"""
from build15_workflow import ReviewWorkflow
from trusted_identity import verify_owner_token

class AuthorizedReviewWorkflow:
    def __init__(self, directory, *, secret, pet_access_check, clock=None,
                 token_clock=None, revoked_subjects=()):
        if not isinstance(secret, bytes) or len(secret) < 16:
            raise ValueError("invalid demo secret")
        if not callable(pet_access_check):
            raise ValueError("authoritative pet access check required")
        self._workflow = ReviewWorkflow(directory, clock=clock)
        self._secret = secret
        self._access = pet_access_check
        self._token_clock = token_clock
        self._revoked = revoked_subjects

    def _owner(self, token, pet_id, scope):
        if not isinstance(pet_id, str) or not pet_id:
            raise PermissionError("invalid pet")
        identity = verify_owner_token(
            token, secret=self._secret, pet_id=pet_id, scope=scope,
            now=self._token_clock, revoked_subjects=self._revoked)
        owner = identity["verified_owner_id"]
        # Any unavailable backend, exception, or non-True response denies.
        try:
            allowed = self._access(owner, pet_id, scope)
        except Exception:
            raise PermissionError("pet authorization unavailable") from None
        if allowed is not True:
            raise PermissionError("pet authorization denied")
        return owner

    @staticmethod
    def _payload(payload, pet_id):
        if not isinstance(payload, dict) or payload.get("pet_id") != pet_id:
            raise PermissionError("payload pet mismatch")

    def prepare(self, *, identity_token, pet_id, action, payload,
                evidence_sha256, operation_id):
        self._payload(payload, pet_id)
        owner = self._owner(identity_token, pet_id, "care:propose")
        return self._workflow.prepare(owner, action, payload, evidence_sha256, operation_id)

    def approve_dry_run(self, *, identity_token, pet_id, operation_id,
                        approval_token, payload):
        self._payload(payload, pet_id)
        owner = self._owner(identity_token, pet_id, "care:approve")
        return self._workflow.approve_dry_run(
            operation_id, approval_token, owner, payload)
