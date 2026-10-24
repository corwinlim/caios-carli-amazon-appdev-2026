import tempfile, unittest
from pathlib import Path
from build15_workflow import ReviewWorkflow

class Build15Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.w=ReviewWorkflow(self.root,clock=lambda:100)
        self.payload={"kind":"roi_motion","frames":83}
        self.evidence="a"*64
        self.prepared=self.w.prepare("synthetic-owner","record_observation",self.payload,self.evidence,"op-1")

    def test_pending_denies_dry_run(self):
        with self.assertRaises(PermissionError): self.w.audit.dry_run("op-1")

    def test_approved_dry_run_never_calls_network(self):
        r=self.w.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",self.payload)
        self.assertFalse(r["executed"])
        self.assertFalse(r["network_called"])
        self.assertEqual(r["owner_approval"],"approved_once")

    def test_replay_denied(self):
        self.w.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",self.payload)
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",self.payload)

    def test_wrong_owner_denied(self):
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-1",self.prepared["approval_token"],"other",self.payload)

    def test_payload_tamper_denied(self):
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",{"frames":84})

    def test_restart_and_replay(self):
        self.w.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",self.payload)
        restarted=ReviewWorkflow(self.root,clock=lambda:100)
        self.assertTrue(restarted.audit.verify())
        with self.assertRaises(PermissionError):
            restarted.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",self.payload)

    def test_uncertain_state_is_not_retryable(self):
        self.w.approve_dry_run("op-1",self.prepared["approval_token"],"synthetic-owner",self.payload)
        self.w.mark_uncertain_without_network("op-1")
        restarted=ReviewWorkflow(self.root,clock=lambda:100)
        self.assertEqual(restarted.audit.unresolved(),[("op-1","dispatched_unknown")])
        with self.assertRaises(PermissionError): restarted.audit.dry_run("op-1")

    def test_nonallowlisted_action_denied(self):
        with self.assertRaises(PermissionError):
            self.w.prepare("synthetic-owner","delete_observation",{},self.evidence,"op-2")

if __name__=="__main__": unittest.main()
