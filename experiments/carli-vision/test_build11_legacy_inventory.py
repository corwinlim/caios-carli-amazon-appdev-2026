"""Build 11 inventory regression tests; no production data."""
import tempfile
import unittest
from pathlib import Path
from build11_legacy_inventory import inventory
from build15_workflow import ReviewWorkflow, _bound_approval_payload

class Build11InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def test_missing_db_does_not_create(self):
        result=inventory(self.root)
        self.assertFalse(result["databases_present"]["audit"])
        self.assertFalse((self.root/"audit.sqlite").exists())
        self.assertFalse((self.root/"approval.sqlite").exists())
    def test_pending_is_never_imported(self):
        w=ReviewWorkflow(self.root,clock=lambda:100)
        w.prepare("owner","record_observation",{"synthetic":True},"a"*64,"op11")
        result=inventory(self.root)
        self.assertEqual(result["operations"][0]["classification"],"manual_review_required")
        self.assertFalse(result["operations"][0]["authorized_for_new_engine"])
        self.assertFalse(result["safe_to_dispatch"])
    def test_consumed_legacy_still_requires_review(self):
        w=ReviewWorkflow(self.root,clock=lambda:100)
        p={"synthetic":True}
        prepared=w.prepare("owner","record_observation",p,"a"*64,"op11")
        w.approvals.approve(prepared["approval_token"],"owner","record_observation",
                            _bound_approval_payload("op11",p))
        result=inventory(self.root)
        self.assertEqual(result["approval_state_counts"]["consumed"],1)
        self.assertEqual(result["operations"][0]["classification"],"manual_review_required")
    def test_ready_legacy_is_not_new_authorization(self):
        w=ReviewWorkflow(self.root,clock=lambda:100)
        p={"synthetic":True}
        prepared=w.prepare("owner","record_observation",p,"a"*64,"op11")
        w.approve_dry_run("op11",prepared["approval_token"],"owner",p)
        result=inventory(self.root)
        self.assertEqual(result["operations"][0]["legacy_state"],"ready")
        self.assertFalse(result["operations"][0]["safe_to_dispatch"])
    def test_repeated_read_does_not_mutate(self):
        w=ReviewWorkflow(self.root,clock=lambda:100)
        w.prepare("owner","record_observation",{"synthetic":True},"a"*64,"op11")
        before=[(p,p.read_bytes()) for p in (self.root/"audit.sqlite",self.root/"approval.sqlite")]
        self.assertEqual(inventory(self.root),inventory(self.root))
        for p,data in before:
            self.assertEqual(p.read_bytes(),data)
if __name__=="__main__":
    unittest.main()
