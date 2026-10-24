import unittest
import cv2
import numpy as np
from motion import motion_metrics


class MotionTests(unittest.TestCase):
    def make_frame(self, cx):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        if cx is not None:
            cv2.circle(frame, (cx, 60), 12, (255, 255, 255), -1)
        return frame

    def test_moving_circle_detected(self):
        result = motion_metrics([self.make_frame(x) for x in (35, 45, 55, 65, 75)], (10, 20, 130, 80))
        self.assertGreater(result["motion_frames"], 0)
        self.assertFalse(result["feeding_confirmed"])

    def test_static_circle_no_motion(self):
        result = motion_metrics([self.make_frame(40) for _ in range(5)], (10, 20, 130, 80))
        self.assertEqual(result["motion_frames"], 0)

    def test_outside_roi_no_motion(self):
        result = motion_metrics([self.make_frame(x) for x in (35, 45, 55)], (110, 0, 40, 30))
        self.assertEqual(result["motion_frames"], 0)

    def test_invalid_roi(self):
        with self.assertRaises(ValueError):
            motion_metrics([self.make_frame(35)], (0, 0, 500, 80))

    def test_empty(self):
        self.assertEqual(motion_metrics([], (10, 20, 130, 80))["frame_count"], 0)


if __name__ == "__main__":
    unittest.main()
