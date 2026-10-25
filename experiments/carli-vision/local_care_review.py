"""P0-A Build6: single supported offline application facade.

This facade requires a persistent local grant store and verified test token.
Legacy modules remain importable: this is not a process security boundary.
No network/MCP calls, no production authentication.
"""
from pathlib import Path
from authorized_review_workflow import AuthorizedReviewWorkflow
from pet_grant_store import PetGrantStore

class LocalCareReview:
    def __init__(self, directory, *, secret, clock=None, token_clock=None,
                 revoked_subjects=()):
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        self._grants = PetGrantStore(root / "pet_grants.sqlite")
        self._review = AuthorizedReviewWorkflow(
            root / "review", secret=secret,
            pet_access_check=self._grants.check,
            clock=clock, token_clock=token_clock,
            revoked_subjects=revoked_subjects)

    def prepare(self, *, identity_token, pet_id, payload,
                evidence_sha256, operation_id):
        return self._review.prepare(
            identity_token=identity_token, pet_id=pet_id,
            action="record_observation", payload=payload,
            evidence_sha256=evidence_sha256, operation_id=operation_id)

    def approve_dry_run(self, *, identity_token, pet_id, operation_id,
                        approval_token, payload):
        return self._review.approve_dry_run(
            identity_token=identity_token, pet_id=pet_id,
            operation_id=operation_id, approval_token=approval_token,
            payload=payload)
