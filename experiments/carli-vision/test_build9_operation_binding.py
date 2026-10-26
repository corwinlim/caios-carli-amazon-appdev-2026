"""Build9: approval token cannot be used for a different operation."""
import tempfile
import unittest
from pathlib import Path
from build15_workflow import ReviewWorkflow

class OperationBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.w=ReviewWorkflow(Path(self.tmp.name),clock=lambda:100)
        self.payload={"pet_id":"pika","note":"synthetic"}
    def test_cross_operation_same_payload_denied(self):
        first=self.w.prepare("owner","record_observation",self.payload,"a"*64,"op-a")
        self.w.prepare("owner","record_observation",self.payload,"a"*64,"op-b")
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-b",first["approval_token"],"owner",self.payload)
        self.assertTrue(self.w.audit.verify())
        with self.w.audit.db() as db:
            states=db.execute("SELECT operation_id,state FROM operations ORDER BY operation_id").fetchall()
        self.assertEqual(states,[("op-a","pending"),("op-b","pending")])
        result=self.w.approve_dry_run("op-a",first["approval_token"],"owner",self.payload)
        self.assertFalse(result["network_called"])
    def test_restart_binding_persists(self):
        first=self.w.prepare("owner","record_observation",self.payload,"a"*64,"op-a")
        self.w.prepare("owner","record_observation",self.payload,"a"*64,"op-b")
        restarted=ReviewWorkflow(Path(self.tmp.name),clock=lambda:100)
        with self.assertRaises(PermissionError):
            restarted.approve_dry_run("op-b",first["approval_token"],"owner",self.payload)
    def test_empty_operation_id_denied(self):
        with self.assertRaises(ValueError):
            self.w.prepare("owner","record_observation",self.payload,"a"*64,"")
if __name__=="__main__":
    unittest.main()
