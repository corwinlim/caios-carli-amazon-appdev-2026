import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from build17_evidence_review import verify

class Build17EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.path=self.root/"build16_evidence.json"
        self.commit="06b2a2dbb2d443419c0e5d33462601fb79dd6e2e"
        self.data={"schema":"carli-build16-evidence/1","mode":"synthetic_local_only",
                   "real_mcp_invoked":False,"git_commit":self.commit,
                   "test_count":60,"tests_passed":True}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data),encoding="utf-8")
        self.digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.path.with_suffix(".json.sha256").write_text(self.digest+"  "+self.path.name+"\n")

    def check(self, digest=None):
        with patch("build17_evidence_review.git_head",return_value="new-build17-commit"):
            return verify(self.path,self.root,digest or self.digest,self.commit)

    def test_valid(self):
        self.assertEqual(self.check()["status"],"PASS")

    def test_hash_mismatch(self):
        self.assertIn("evidence_hash_mismatch",self.check("0"*64)["failures"])

    def test_sidecar_mismatch(self):
        self.path.with_suffix(".json.sha256").write_text("bad  build16_evidence.json")
        self.assertIn("sidecar_mismatch",self.check()["failures"])

    def test_commit_mismatch(self):
        self.data["git_commit"]="incorrect"
        self.save()
        self.assertIn("evidence_commit_mismatch",self.check()["failures"])

    def test_safety_mismatch(self):
        self.data["real_mcp_invoked"]=True
        self.save()
        self.assertIn("safety_boundary_mismatch",self.check()["failures"])

    def test_missing_file(self):
        self.path.unlink()
        self.assertIn("evidence_missing",self.check()["failures"])

if __name__=="__main__": unittest.main()
