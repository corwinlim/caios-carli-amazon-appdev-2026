"""Encoded synthetic video tests: measure pixels rather than injected policy flags."""
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from run_video import run


class VideoQualityRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def clip(self, mode):
        path = self.root / (mode + '.avi')
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 10, (160, 120))
        self.assertTrue(writer.isOpened())
        y, x = np.indices((120, 160))
        base = np.where((x//4 + y//4) % 2, 190, 70).astype(np.uint8)
        try:
            for i in range(20):
                gray = base.copy()
                if mode == 'moving':
                    gray[30:60, 10+i*3:40+i*3] = 250
                elif mode == 'dark':
                    gray[:] = 0
                elif mode == 'blurred':
                    gray = cv2.GaussianBlur(gray, (31,31), 12)
                elif mode == 'overexposed':
                    gray[:] = 255
                elif mode == 'late_dark' and i >= 10:
                    gray[:] = 0
                writer.write(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
        finally:
            writer.release()
        return path

    def test_black_video_requests_recapture(self):
        result = run(self.clip('dark'), (0,0,160,120))
        self.assertEqual(result['decision']['next_action'], 'request_better_video')

    def test_blurred_video_requests_recapture(self):
        result = run(self.clip('blurred'), (0,0,160,120))
        self.assertEqual(result['decision']['next_action'], 'request_better_video')

    def test_overexposed_video_requests_recapture(self):
        result = run(self.clip('overexposed'), (0,0,160,120))
        self.assertEqual(result['decision']['next_action'], 'request_better_video')

    def test_quality_checked_beyond_first_frame(self):
        result = run(self.clip('late_dark'), (0,0,160,120))
        self.assertEqual(result['decision']['next_action'], 'request_better_video')

    def test_moving_pixels_request_review_without_feeding_claim(self):
        result = run(self.clip('moving'), (0,0,160,120))
        self.assertEqual(result['decision']['next_action'], 'request_owner_review')
        self.assertFalse(result['decision']['feeding_confirmed'])
        self.assertFalse(result['decision']['mutating_tool_invoked'])

    def test_static_clear_video_continues_observation(self):
        result = run(self.clip('static'), (0,0,160,120))
        self.assertEqual(result['decision']['next_action'], 'continue_observation')

    def test_all_branches_carry_measured_evidence_trace(self):
        for mode in ('dark','blurred','moving','static'):
            with self.subTest(mode=mode):
                result = run(self.clip(mode), (0,0,160,120))
                self.assertIn('quality', result)
                self.assertGreater(len(result.get('trace', [])), 1)
                self.assertEqual(result['trace'][-1]['action'], result['decision']['next_action'])
                self.assertEqual(len(result['video_sha256']), 64)

    def test_invalid_roi_is_rejected(self):
        with self.assertRaises(ValueError):
            run(self.clip('static'), (0,0,1000,1000))


if __name__ == '__main__': unittest.main()
