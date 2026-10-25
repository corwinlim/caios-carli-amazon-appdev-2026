import tempfile
import unittest
from pathlib import Path
from pet_grant_store import PetGrantStore
from authorized_review_workflow import AuthorizedReviewWorkflow
from trusted_identity import mint_test_token

KEY=b"build5-test-secret-not-for-production"
NOW=10000

class PetGrantStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"grants.sqlite"
        self.store=PetGrantStore(self.path)
    def test_default_deny(self):
        self.assertFalse(self.store.check("owner","pet","care:propose"))
    def test_grant(self):
        self.store.set_grant_for_test("owner","pet","care:propose",True)
        self.assertTrue(self.store.check("owner","pet","care:propose"))
    def test_revoke(self):
        self.store.set_grant_for_test("owner","pet","care:propose",True)
        self.store.set_grant_for_test("owner","pet","care:propose",False)
        self.assertFalse(self.store.check("owner","pet","care:propose"))
    def test_other_owner_denied(self):
        self.store.set_grant_for_test("owner","pet","care:propose",True)
        self.assertFalse(self.store.check("other","pet","care:propose"))
    def test_other_pet_denied(self):
        self.store.set_grant_for_test("owner","pet","care:propose",True)
        self.assertFalse(self.store.check("owner","other","care:propose"))
    def test_scope_isolation(self):
        self.store.set_grant_for_test("owner","pet","care:propose",True)
        self.assertFalse(self.store.check("owner","pet","care:approve"))
    def test_persists_restart(self):
        self.store.set_grant_for_test("owner","pet","care:propose",True)
        self.assertTrue(PetGrantStore(self.path).check("owner","pet","care:propose"))
    def test_invalid_grant_rejected(self):
        with self.assertRaises(ValueError):
            self.store.set_grant_for_test("","pet","care:propose",True)
    def test_bad_active_rejected(self):
        with self.assertRaises(ValueError):
            self.store.set_grant_for_test("owner","pet","care:propose",1)
    def test_integrated_revoke_between_steps(self):
        self.store.set_grant_for_test("owner","pika","care:propose",True)
        self.store.set_grant_for_test("owner","pika","care:approve",True)
        workflow=AuthorizedReviewWorkflow(Path(self.tmp.name)/"workflow",
            secret=KEY, pet_access_check=self.store.check,
            clock=lambda:NOW, token_clock=NOW)
        token=mint_test_token(KEY,subject="owner",pet_ids=["pika"],
            scopes=["care:propose","care:approve"],
            issued_at=NOW-10,expires_at=NOW+60)
        payload={"pet_id":"pika","observation":"synthetic"}
        pending=workflow.prepare(identity_token=token,pet_id="pika",
            action="record_observation",payload=payload,
            evidence_sha256="a"*64,operation_id="op1")
        self.store.set_grant_for_test("owner","pika","care:approve",False)
        with self.assertRaises(PermissionError):
            workflow.approve_dry_run(identity_token=token,pet_id="pika",
                operation_id="op1",approval_token=pending["approval_token"],
                payload=payload)

if __name__=="__main__":
    unittest.main()
