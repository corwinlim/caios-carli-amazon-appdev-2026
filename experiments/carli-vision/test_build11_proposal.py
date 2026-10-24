import hashlib
import json
import unittest
from build11_proposal import create_proposal


def fixture():
    return {
        "schema": "carli-vision-local-proposal/1",
        "video_sha256": "a" * 64,
        "motion": {"frame_count": 150, "motion_frames": 83, "feeding_confirmed": False},
        "decision": {"mutating_tool_invoked": False, "owner_confirmation": "pending"},
    }


class Build11Tests(unittest.TestCase):
    def test_read_only_proposal(self):
        obj = fixture()
        raw = json.dumps(obj).encode()
        result = create_proposal(obj, raw)
        self.assertEqual(result["evidence_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertFalse(result["approved"])
        self.assertFalse(result["feeding_confirmed"])
        self.assertFalse(result["mcp_tool_invoked"])
        self.assertIsNone(result["proposed_mutation"])
        self.assertIsNone(result["confirmation_token"])

    def test_rejects_feeding_claim(self):
        obj = fixture()
        obj["motion"]["feeding_confirmed"] = True
        with self.assertRaises(ValueError):
            create_proposal(obj, b"{}")

    def test_rejects_mutation(self):
        obj = fixture()
        obj["decision"]["mutating_tool_invoked"] = True
        with self.assertRaises(ValueError):
            create_proposal(obj, b"{}")

    def test_rejects_bad_counts(self):
        obj = fixture()
        obj["motion"]["motion_frames"] = 151
        with self.assertRaises(ValueError):
            create_proposal(obj, b"{}")

    def test_rejects_preapproved(self):
        obj = fixture()
        obj["decision"]["owner_confirmation"] = "approved"
        with self.assertRaises(ValueError):
            create_proposal(obj, b"{}")


if __name__ == "__main__":
    unittest.main()
