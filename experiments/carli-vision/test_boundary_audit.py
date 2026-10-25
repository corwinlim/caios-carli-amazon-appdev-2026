import tempfile
import unittest
from pathlib import Path
from boundary_audit import inspect_source, inspect_tree

class BoundaryAuditTests(unittest.TestCase):
    def test_current_tree(self):
        self.assertEqual(inspect_tree(), [])
    def test_new_module_direct_legacy_import_denied(self):
        self.assertTrue(inspect_source("new_api.py", "from build15_workflow import ReviewWorkflow"))
    def test_new_module_alias_import_denied(self):
        self.assertTrue(inspect_source("new_api.py", "import persistent_approval as p"))
    def test_guarded_adapter_new_import_denied(self):
        self.assertTrue(inspect_source("new_api.py", "from guarded_review_workflow import GuardedReviewWorkflow"))
    def test_explicit_readonly_recovery_exception(self):
        self.assertEqual(inspect_source("build16_recovery.py", "from build15_workflow import ReviewWorkflow"), [])
    def test_authorized_adapter_exception(self):
        self.assertEqual(inspect_source("authorized_review_workflow.py", "from build15_workflow import ReviewWorkflow"), [])
    def test_non_test_file_scan_detects_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "new_handler.py").write_text("from persistent_approval import PersistentApproval\n", encoding="utf-8")
            self.assertTrue(inspect_tree(tmp))
    def test_test_file_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_old.py").write_text("from build15_workflow import ReviewWorkflow\n", encoding="utf-8")
            self.assertEqual(inspect_tree(tmp), [])

if __name__ == "__main__":
    unittest.main()
