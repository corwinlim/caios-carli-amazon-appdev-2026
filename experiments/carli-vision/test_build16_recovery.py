import json
import tempfile
import unittest
from pathlib import Path
from build15_workflow import ReviewWorkflow
from build16_recovery import inspect_operation, write_evidence

class Build16Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.workflow=ReviewWorkflow(self.root,clock=lambda:100)
        self.payload={"kind":"roi_motion","frames":83}
        self.prepared=self.workflow.prepare("synthetic-owner","record_observation",self.payload,"a"*64,"op16")

    def test_consumed_but_audit_pending_is_manual(self):
        self.workflow.approvals.approve(self.prepared["approval_token"],"synthetic-owner","record_observation",self.payload)
        result=inspect_operation(self.root,"op16")
        self.assertEqual(result["status"],"manual_reconciliation_required")
        self.assertFalse(result["safe_to_dispatch"])

    def test_unknown_dispatch_never_safe(self):
        self.workflow.approve_dry_run("op16",self.prepared["approval_token"],"synthetic-owner",self.payload)
        self.workflow.mark_uncertain_without_network("op16")
        self.assertEqual(inspect_operation(self.root,"op16")["status"],"dispatch_outcome_unknown")
        self.assertFalse(inspect_operation(self.root,"op16")["safe_to_dispatch"])

    def test_ready_remains_dry_run_only(self):
        self.workflow.approve_dry_run("op16",self.prepared["approval_token"],"synthetic-owner",self.payload)
        result=inspect_operation(self.root,"op16")
        self.assertEqual(result["status"],"approved_dry_run_only")
        self.assertFalse(result["network_called"])

    def test_pending_no_execution(self):
        self.assertFalse(inspect_operation(self.root,"op16")["safe_to_dispatch"])

    def test_unknown_operation_denied(self):
        self.assertEqual(inspect_operation(self.root,"absent")["status"],"unknown_operation")

    def test_report_and_hash(self):
        path=self.root/"evidence"/"build16.json"
        report=write_evidence(self.root,path,60,True)
        self.assertTrue(path.exists())
        self.assertEqual(report["schema"],"carli-build16-evidence/1")
        import hashlib
        self.assertEqual(path.with_suffix(".json.sha256").read_text().split()[0],
                         hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=="__main__": unittest.main()
