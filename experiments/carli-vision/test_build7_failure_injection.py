"""Build7: offline fail-closed fault injection. No MCP or network."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from local_care_review import LocalCareReview
from pet_grant_store import PetGrantStore
from trusted_identity import mint_test_token

KEY=b"build7-offline-test-secret-32-bytes"
NOW=10000

class FailureInjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.app=LocalCareReview(self.root,secret=KEY,clock=lambda:NOW,token_clock=NOW)
        self.store=PetGrantStore(self.root/"pet_grants.sqlite")
        self.payload={"pet_id":"pika","note":"synthetic"}
        self.token=mint_test_token(KEY,subject="owner",pet_ids=["pika"],
            scopes=["care:propose","care:approve"],issued_at=NOW-1,expires_at=NOW+60)
    def grant(self):
        for scope in ("care:propose","care:approve"):
            self.store.set_grant_for_test("owner","pika",scope,True)
    def prepare(self,operation="op1"):
        return self.app.prepare(identity_token=self.token,pet_id="pika",
            payload=self.payload,evidence_sha256="a"*64,operation_id=operation)
    def approve(self,pending,operation="op1"):
        return self.app.approve_dry_run(identity_token=self.token,pet_id="pika",
            operation_id=operation,approval_token=pending["approval_token"],
            payload=self.payload)
    def test_database_connect_failure_denies_prepare(self):
        self.grant()
        with patch("pet_grant_store.sqlite3.connect",side_effect=sqlite3.OperationalError("synthetic outage")):
            with self.assertRaises(PermissionError): self.prepare()
    def test_database_connect_failure_denies_approve(self):
        self.grant()
        pending=self.prepare()
        with patch("pet_grant_store.sqlite3.connect",side_effect=sqlite3.OperationalError("synthetic outage")):
            with self.assertRaises(PermissionError): self.approve(pending)
    def test_missing_grant_table_denies(self):
        self.grant()
        with sqlite3.connect(self.store.path) as db:
            db.execute("DROP TABLE pet_grants")
        with self.assertRaises(PermissionError): self.prepare()
    def test_revoke_after_prepare_denies_approve(self):
        self.grant()
        pending=self.prepare()
        self.store.set_grant_for_test("owner","pika","care:approve",False)
        with self.assertRaises(PermissionError): self.approve(pending)
    def test_revoke_persists_restart(self):
        self.grant()
        self.store.set_grant_for_test("owner","pika","care:approve",False)
        self.assertFalse(PetGrantStore(self.store.path).check("owner","pika","care:approve"))
    def test_duplicate_approval_rejected(self):
        self.grant()
        pending=self.prepare()
        result=self.approve(pending)
        self.assertFalse(result["network_called"])
        with self.assertRaises(PermissionError): self.approve(pending)
    def test_rejected_does_not_consume_approval(self):
        self.grant()
        pending=self.prepare()
        self.store.set_grant_for_test("owner","pika","care:approve",False)
        with self.assertRaises(PermissionError): self.approve(pending)
        self.store.set_grant_for_test("owner","pika","care:approve",True)
        result=self.approve(pending)
        self.assertFalse(result["executed"])
    def test_other_owner_cannot_approve(self):
        self.grant()
        pending=self.prepare()
        other=mint_test_token(KEY,subject="other",pet_ids=["pika"],
            scopes=["care:approve"],issued_at=NOW-1,expires_at=NOW+60)
        with self.assertRaises(PermissionError):
            self.app.approve_dry_run(identity_token=other,pet_id="pika",
                operation_id="op1",approval_token=pending["approval_token"],
                payload=self.payload)

if __name__=="__main__":
    unittest.main()
