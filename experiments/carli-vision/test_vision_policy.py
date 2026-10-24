"""Synthetic unit tests; no camera, AWS or MCP integration required."""
import unittest
from vision_policy import Signal, propose


class VisionPolicyTests(unittest.TestCase):
    def test_never_confirms_feeding(self):
        for signal in (
            Signal(True, True, bowl_near=True, identity_verified=True, motion_frames=50),
            Signal(True, True),
            Signal(False, True),
            Signal(True, False),
            Signal(True, True, occluded=True),
            Signal(True, True, multiple_pets=True),
        ):
            with self.subTest(signal=signal):
                result = propose(signal)
                self.assertFalse(result["feeding_confirmed"])
                self.assertFalse(result["mutating_tool_invoked"])
                self.assertEqual(result["owner_confirmation"], "pending")

    def test_bowl_proximity_needs_owner(self):
        self.assertEqual(
            propose(Signal(True, True, bowl_near=True))["next_action"],
            "request_owner_confirmation",
        )

    def test_bad_quality_abstains(self):
        self.assertEqual(
            propose(Signal(False, True))["next_action"], "request_better_video"
        )

    def test_multiple_pets_abstains(self):
        self.assertEqual(
            propose(Signal(True, True, multiple_pets=True))["next_action"],
            "request_owner_identification",
        )

    def test_occlusion_abstains(self):
        self.assertEqual(
            propose(Signal(True, True, occluded=True))["next_action"],
            "request_more_evidence",
        )


if __name__ == "__main__":
    unittest.main()
