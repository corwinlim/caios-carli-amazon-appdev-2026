import unittest
from approval_gate import ApprovalGate

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.now = 100
        self.gate = ApprovalGate(clock=lambda: self.now)
        self.payload = {"kind": "roi_motion", "count": 83}
        self.token = self.gate.prepare("synthetic-owner", "record_observation", self.payload)

    def test_exact_approval_once(self):
        self.assertEqual(self.gate.approve(self.token, "synthetic-owner", "record_observation", self.payload)["status"], "approved_once")
        with self.assertRaises(PermissionError):
            self.gate.approve(self.token, "synthetic-owner", "record_observation", self.payload)

    def test_other_owner_denied(self):
        with self.assertRaises(PermissionError):
            self.gate.approve(self.token, "intruder", "record_observation", self.payload)

    def test_payload_tamper_denied(self):
        with self.assertRaises(PermissionError):
            self.gate.approve(self.token, "synthetic-owner", "record_observation", {"count": 84, "kind": "roi_motion"})

    def test_action_change_denied(self):
        with self.assertRaises(PermissionError):
            self.gate.approve(self.token, "synthetic-owner", "delete_observation", self.payload)

    def test_expiry_denied(self):
        self.now = 160
        with self.assertRaises(PermissionError):
            self.gate.approve(self.token, "synthetic-owner", "record_observation", self.payload)

    def test_rejection_denied(self):
        self.gate.reject(self.token, "synthetic-owner")
        with self.assertRaises(PermissionError):
            self.gate.approve(self.token, "synthetic-owner", "record_observation", self.payload)

    def test_missing_token_denied(self):
        with self.assertRaises(PermissionError):
            self.gate.approve("fake", "synthetic-owner", "record_observation", self.payload)

    def test_canonical_key_order(self):
        self.assertEqual(self.gate.approve(self.token, "synthetic-owner", "record_observation", {"count": 83, "kind": "roi_motion"})["status"], "approved_once")

    def test_invalid_ttl(self):
        with self.assertRaises(ValueError):
            self.gate.prepare("synthetic-owner", "record_observation", {}, 0)

if __name__ == "__main__":
    unittest.main()
