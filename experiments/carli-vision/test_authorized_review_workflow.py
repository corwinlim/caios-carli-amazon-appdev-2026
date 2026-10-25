import tempfile
import unittest
from authorized_review_workflow import AuthorizedReviewWorkflow
from trusted_identity import mint_test_token, IdentityDenied

KEY=b"build3-offline-only-secret-key"
NOW=10000

class AuthorizedReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.allowed=True
        self.calls=[]
        def access(owner, pet, scope):
            self.calls.append((owner, pet, scope))
            return self.allowed
        self.access=access
        self.workflow=AuthorizedReviewWorkflow(
            self.tmp.name, secret=KEY, pet_access_check=access,
            clock=lambda:NOW, token_clock=NOW)
        self.payload={"pet_id":"pika","note":"synthetic"}
        self.token=self.mint()
    def mint(self, scopes=("care:propose","care:approve"), subject="owner-a"):
        return mint_test_token(KEY, subject=subject, pet_ids=["pika"],
            scopes=list(scopes), issued_at=NOW-10, expires_at=NOW+60)
    def prepare(self, **changes):
        args=dict(identity_token=self.token, pet_id="pika",
            action="record_observation", payload=self.payload,
            evidence_sha256="a"*64, operation_id="op1")
        args.update(changes)
        return self.workflow.prepare(**args)
    def approve(self, pending, **changes):
        args=dict(identity_token=self.token, pet_id="pika",
            operation_id="op1", approval_token=pending["approval_token"],
            payload=self.payload)
        args.update(changes)
        return self.workflow.approve_dry_run(**args)
    def test_valid_separate_scope_checks(self):
        p=self.prepare()
        result=self.approve(p)
        self.assertFalse(result["executed"])
        self.assertEqual([c[2] for c in self.calls],
                         ["care:propose","care:approve"])
    def test_access_revoked_between_prepare_and_approve(self):
        p=self.prepare()
        self.allowed=False
        with self.assertRaises(PermissionError): self.approve(p)
    def test_nonboolean_truthy_denied(self):
        self.allowed=1
        with self.assertRaises(PermissionError): self.prepare()
    def test_access_backend_error_denied(self):
        def broken(*args): raise OSError("offline")
        self.workflow._access=broken
        with self.assertRaises(PermissionError): self.prepare()
    def test_propose_scope_cannot_approve(self):
        p=self.prepare()
        with self.assertRaises(IdentityDenied):
            self.approve(p, identity_token=self.mint(scopes=["care:propose"]))
    def test_approve_scope_cannot_prepare(self):
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token=self.mint(scopes=["care:approve"]))
    def test_wrong_owner_denied(self):
        p=self.prepare()
        with self.assertRaises(PermissionError):
            self.approve(p, identity_token=self.mint(subject="other"))
    def test_pet_payload_mismatch_denied(self):
        with self.assertRaises(PermissionError):
            self.prepare(payload={"pet_id":"other"})
    def test_access_check_required(self):
        with self.assertRaises(ValueError):
            AuthorizedReviewWorkflow(self.tmp.name,secret=KEY,
                                     pet_access_check=None)
if __name__=="__main__": unittest.main()
