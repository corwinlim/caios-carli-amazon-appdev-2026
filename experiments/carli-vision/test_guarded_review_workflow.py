import tempfile
import unittest
from pathlib import Path
from guarded_review_workflow import GuardedReviewWorkflow
from trusted_identity import mint_test_token, IdentityDenied
from audit_ledger import sha

KEY = b"local-test-only-secret-not-for-production"
NOW = 10000

class GuardedReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workflow = GuardedReviewWorkflow(self.temp.name, secret=KEY,
                                               token_clock=NOW, clock=lambda: NOW)
        self.payload = {"pet_id": "pika", "observation": "synthetic only"}
        self.token = self.identity("owner-a", ["pika"])

    def identity(self, subject, pets, scopes=("care:propose",), expires=NOW+60):
        return mint_test_token(KEY, subject=subject, pet_ids=pets,
                               scopes=list(scopes), issued_at=NOW-60, expires_at=expires)

    def prepare(self, **kwargs):
        args = dict(identity_token=self.token, pet_id="pika",
                    action="record_observation", payload=self.payload,
                    evidence_sha256="a" * 64, operation_id="op1")
        args.update(kwargs)
        return self.workflow.prepare(**args)

    def test_valid_prepare_and_approve_is_dry_run(self):
        pending = self.prepare()
        result = self.workflow.approve_dry_run(
            identity_token=self.token, pet_id="pika",
            operation_id="op1", approval_token=pending["approval_token"],
            payload=self.payload)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["executed"])

    def test_no_token_denied_before_prepare(self):
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token="")

    def test_cross_pet_denied(self):
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token=self.identity("owner-a", ["other"]))

    def test_payload_pet_mismatch_denied(self):
        with self.assertRaises(PermissionError):
            self.prepare(payload={"pet_id": "other"})

    def test_expired_identity_denied(self):
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token=self.identity("owner-a", ["pika"], expires=NOW))

    def test_missing_scope_denied(self):
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token=self.identity("owner-a", ["pika"], scopes=[]))

    def test_other_owner_cannot_approve(self):
        pending = self.prepare()
        with self.assertRaises(PermissionError):
            self.workflow.approve_dry_run(
                identity_token=self.identity("owner-b", ["pika"]),
                pet_id="pika", operation_id="op1",
                approval_token=pending["approval_token"], payload=self.payload)

    def test_tampered_payload_cannot_approve(self):
        pending = self.prepare()
        with self.assertRaises(PermissionError):
            self.workflow.approve_dry_run(
                identity_token=self.token, pet_id="pika", operation_id="op1",
                approval_token=pending["approval_token"],
                payload={"pet_id": "pika", "observation": "altered"})

    def test_revoked_owner_denied(self):
        guarded = GuardedReviewWorkflow(self.temp.name, secret=KEY,
                                         token_clock=NOW, clock=lambda: NOW,
                                         revoked_subjects={"owner-a"})
        with self.assertRaises(IdentityDenied):
            guarded.prepare(identity_token=self.token, pet_id="pika",
                            action="record_observation", payload=self.payload,
                            evidence_sha256="a" * 64, operation_id="op1")

    def test_invalid_secret_denied(self):
        with self.assertRaises(ValueError):
            GuardedReviewWorkflow(self.temp.name, secret=b"short")

if __name__ == "__main__":
    unittest.main()
