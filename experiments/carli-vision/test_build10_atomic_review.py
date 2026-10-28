"""Build10 atomicity and fail-closed regression tests."""
import tempfile
import unittest
from pathlib import Path
from build10_atomic_review import AtomicReview

class AtomicReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"atomic.sqlite"
        self.w=AtomicReview(self.path,clock=lambda:100)
        self.payload={"kind":"synthetic","frames":83}
        self.first=self.w.prepare("op-a","owner",self.payload,"a"*64)
    def test_approve_once(self):
        result=self.w.approve_dry_run("op-a",self.first["approval_token"],"owner",self.payload)
        self.assertFalse(result["network_called"])
        self.assertEqual(self.w.inspect("op-a")["status"],"ready")
        self.assertTrue(self.w.verify())
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-a",self.first["approval_token"],"owner",self.payload)
    def test_cross_operation_token_denied(self):
        self.w.prepare("op-b","owner",self.payload,"a"*64)
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-b",self.first["approval_token"],"owner",self.payload)
        self.assertEqual(self.w.inspect("op-b")["status"],"pending")
    def test_wrong_owner_denied(self):
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-a",self.first["approval_token"],"other",self.payload)
    def test_tamper_denied(self):
        with self.assertRaises(PermissionError):
            self.w.approve_dry_run("op-a",self.first["approval_token"],"owner",{"frames":84})
    def test_crash_points_rollback(self):
        for fault in ("before_update","after_update","after_event"):
            with self.subTest(fault=fault):
                with self.assertRaises(RuntimeError):
                    self.w.approve_dry_run("op-a",self.first["approval_token"],"owner",self.payload,fault=fault)
                restarted=AtomicReview(self.path,clock=lambda:100)
                self.assertEqual(restarted.inspect("op-a")["status"],"pending")
                self.assertTrue(restarted.verify())
        self.w.approve_dry_run("op-a",self.first["approval_token"],"owner",self.payload)
        self.assertEqual(AtomicReview(self.path,clock=lambda:100).inspect("op-a")["status"],"ready")
    def test_expiry_denied(self):
        late=AtomicReview(self.path,clock=lambda:1000)
        with self.assertRaises(PermissionError):
            late.approve_dry_run("op-a",self.first["approval_token"],"owner",self.payload)
    def test_duplicate_operation_denied(self):
        with self.assertRaises(Exception):
            self.w.prepare("op-a","owner",self.payload,"a"*64)
    def test_no_dispatch_even_ready(self):
        self.w.approve_dry_run("op-a",self.first["approval_token"],"owner",self.payload)
        self.assertFalse(self.w.inspect("op-a")["safe_to_dispatch"])
if __name__=="__main__":
    unittest.main()
