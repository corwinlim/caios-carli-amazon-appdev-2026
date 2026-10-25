"""Build8: receipt integrity and simulated cross-database interruption."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from build8_verify_evidence import verify
from build15_workflow import ReviewWorkflow
from audit_ledger import sha

class EvidenceVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.logs={"boundary":"CARLi P0-A BUILD4 STATIC BOUNDARY: PASS\n",
                   "unittest":"----------------------------------------------------------------------\nRan 132 tests in 1.000s\n\nOK\n"}
        for name,body in self.logs.items():
            (self.root/(name+".log")).write_text(body,encoding="utf-8")
        self.data={"schema":"carli-p0a-build7-evidence/1",
                   "mode":"synthetic_offline_only","production_approved":False,
                   "gate_passed":True,"git_commit":"a"*40,
                   "steps":[{"name":n,"exit_code":0,"log_file":n+".log",
                             "log_sha256":hashlib.sha256((self.root/(n+".log")).read_bytes()).hexdigest()}
                            for n in ("boundary","unittest")]}
        self.seal()
    def seal(self):
        raw=json.dumps(self.data).encode()
        (self.root/"BUILD7_EVIDENCE.json").write_bytes(raw)
        (self.root/"BUILD7_EVIDENCE.json.sha256").write_text(
            hashlib.sha256(raw).hexdigest()+"  BUILD7_EVIDENCE.json\n",encoding="utf-8")
    def test_valid_receipt(self):
        self.assertTrue(verify(self.root)[0])
    def replace_log(self, body):
        path = self.root / 'unittest.log'
        path.write_bytes(body.encode())
        self.data['steps'][1]['log_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.seal()
    def test_windows_line_endings_accepted(self):
        self.replace_log('Ran 132 tests in 1.000s\r\n\r\nOK\r\n')
        self.assertTrue(verify(self.root)[0])
    def test_literal_escaped_newline_not_accepted(self):
        self.replace_log(r'Ran 132 tests in 1.000s\nOK')
        self.assertFalse(verify(self.root)[0])
    def test_failed_run_cannot_append_fake_ok(self):
        self.replace_log('Ran 132 tests in 1.000s\nFAILED (failures=1)\nOK\n')
        self.assertFalse(verify(self.root)[0])
    def test_zero_tests_not_a_pass(self):
        self.replace_log('Ran 0 tests in 0.000s\n\nOK\n')
        self.assertFalse(verify(self.root)[0])
    def test_unrelated_ok_text_not_a_pass(self):
        self.replace_log('Ran 132 tests in 1.000s\n\\nOK in a quoted message\n')
        self.assertFalse(verify(self.root)[0])
    def test_tampered_log_rejected(self):
        (self.root/"unittest.log").write_text("FAIL",encoding="utf-8")
        self.assertFalse(verify(self.root)[0])
    def test_tampered_receipt_rejected(self):
        (self.root/"BUILD7_EVIDENCE.json").write_text("{}",encoding="utf-8")
        self.assertFalse(verify(self.root)[0])
    def test_missing_checksum_rejected(self):
        (self.root/"BUILD7_EVIDENCE.json.sha256").unlink()
        self.assertFalse(verify(self.root)[0])
    def test_forged_pass_with_nonzero_exit_rejected(self):
        self.data["steps"][1]["exit_code"]=1
        self.seal()
        self.assertFalse(verify(self.root)[0])
    def test_missing_log_rejected(self):
        (self.root/"boundary.log").unlink()
        self.assertFalse(verify(self.root)[0])
    def test_production_mode_rejected(self):
        self.data["production_approved"]=True
        self.seal()
        self.assertFalse(verify(self.root)[0])

class CrashWindowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workflow=ReviewWorkflow(Path(self.tmp.name),clock=lambda:10000)
        self.payload={"pet_id":"pika","note":"synthetic"}
    def test_after_approval_consumed_before_audit_fails_closed(self):
        pending=self.workflow.prepare("owner","record_observation",self.payload,"a"*64,"op1")
        with patch.object(self.workflow.audit,"transition",side_effect=RuntimeError("synthetic crash")):
            with self.assertRaises(RuntimeError):
                self.workflow.approve_dry_run("op1",pending["approval_token"],"owner",self.payload)
        with self.workflow.audit.db() as db:
            state=db.execute("SELECT state FROM operations WHERE operation_id='op1'").fetchone()[0]
        self.assertEqual(state,"pending")
        with self.assertRaises(PermissionError):
            self.workflow.approve_dry_run("op1",pending["approval_token"],"owner",self.payload)
        self.assertTrue(self.workflow.audit.verify())
    def test_prepared_operation_cannot_dry_run(self):
        self.workflow.prepare("owner","record_observation",self.payload,"a"*64,"op1")
        with self.assertRaises(PermissionError):
            self.workflow.audit.dry_run("op1")

if __name__=="__main__":
    unittest.main()
