import tempfile
import unittest
from pathlib import Path
from local_care_review import LocalCareReview
from pet_grant_store import PetGrantStore
from trusted_identity import mint_test_token, IdentityDenied

KEY=b"build6-offline-only-secret-32-bytes"
NOW=10000

class LocalCareReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.app=LocalCareReview(self.root,secret=KEY,clock=lambda:NOW,token_clock=NOW)
        self.store=PetGrantStore(self.root/"pet_grants.sqlite")
        self.payload={"pet_id":"pika","note":"synthetic"}
        self.token=self.mint()
    def mint(self, subject="owner-a", scopes=("care:propose","care:approve"),
             pets=("pika",), expires=NOW+60):
        return mint_test_token(KEY,subject=subject,pet_ids=list(pets),
            scopes=list(scopes),issued_at=NOW-10,expires_at=expires)
    def grants(self):
        for scope in ("care:propose","care:approve"):
            self.store.set_grant_for_test("owner-a","pika",scope,True)
    def prepare(self, **overrides):
        args=dict(identity_token=self.token,pet_id="pika",payload=self.payload,
            evidence_sha256="a"*64,operation_id="op1")
        args.update(overrides)
        return self.app.prepare(**args)
    def approve(self, prepared, **overrides):
        args=dict(identity_token=self.token,pet_id="pika",operation_id="op1",
            approval_token=prepared["approval_token"],payload=self.payload)
        args.update(overrides)
        return self.app.approve_dry_run(**args)
    def test_default_deny(self):
        with self.assertRaises(PermissionError): self.prepare()
    def test_valid_dry_run(self):
        self.grants()
        p=self.prepare()
        result=self.approve(p)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["executed"])
    def test_replay_denied(self):
        self.grants()
        p=self.prepare()
        self.approve(p)
        with self.assertRaises(PermissionError): self.approve(p)
    def test_revoked_between_steps(self):
        self.grants()
        p=self.prepare()
        self.store.set_grant_for_test("owner-a","pika","care:approve",False)
        with self.assertRaises(PermissionError): self.approve(p)
    def test_wrong_owner(self):
        self.grants()
        p=self.prepare()
        with self.assertRaises(PermissionError):
            self.approve(p,identity_token=self.mint(subject="owner-b"))
    def test_expired_token(self):
        self.grants()
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token=self.mint(expires=NOW))
    def test_wrong_pet(self):
        self.grants()
        with self.assertRaises(IdentityDenied):
            self.prepare(identity_token=self.mint(pets=("other",)))
    def test_missing_approve_scope(self):
        self.grants()
        p=self.prepare()
        with self.assertRaises(IdentityDenied):
            self.approve(p,identity_token=self.mint(scopes=("care:propose",)))
    def test_payload_tamper(self):
        self.grants()
        p=self.prepare()
        with self.assertRaises(PermissionError):
            self.approve(p,payload={"pet_id":"pika","note":"changed"})
    def test_restart_persistent_grants(self):
        self.grants()
        restarted=LocalCareReview(self.root,secret=KEY,
            clock=lambda:NOW,token_clock=NOW)
        p=restarted.prepare(identity_token=self.token,pet_id="pika",
            payload=self.payload,evidence_sha256="a"*64,operation_id="op1")
        self.assertEqual(p["status"],"pending_owner_review")

if __name__=="__main__":
    unittest.main()
