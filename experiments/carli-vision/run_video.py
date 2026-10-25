"""Run post-deadline OpenCV ROI observation on a local video.

Never performs owner approval, feeding confirmation, AWS calls, or MCP mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import cv2
from motion import motion_metrics
from vision_policy import Signal, propose


def run(video: Path, roi: tuple[int, int, int, int]) -> dict:
    if cv2.__version__.split('.')[0] != '5':
        raise RuntimeError('OpenCV 5 required')
    if not video.is_file():
        raise FileNotFoundError(video)
    if video.stat().st_size > 50 * 1024 * 1024:
        raise ValueError('video exceeds 50 MiB')
    if len(roi) != 4 or any(type(v) is not int for v in roi):
        raise ValueError('ROI must contain four integers')
    x, y, w, h = roi
    if min(x, y) < 0 or min(w, h) <= 0:
        raise ValueError('invalid ROI')
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        capture.release()
        raise ValueError("video cannot be opened")
    fps = capture.get(cv2.CAP_PROP_FPS)
    samples = []
    shape = None
    def decoded_frames():
        nonlocal shape
        while True:
            ok, frame = capture.read()
            if not ok:
                return
            fh, fw = frame.shape[:2]
            if shape is None:
                shape = (fh, fw)
            if (fh, fw) != shape or fh * fw > 1920 * 1080:
                raise ValueError('unsupported video dimensions')
            if x + w > fw or y + h > fh:
                raise ValueError('ROI outside frame')
            if len(samples) >= 7200 or len(samples) / fps >= 60:
                raise ValueError('video exceeds 60 seconds or 7200 frames')
            gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
            brightness = float(gray.mean())
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            samples.append({'time_s': len(samples) / fps,
                            'brightness': brightness, 'sharpness': sharpness,
                            'usable': 35 <= brightness <= 240 and sharpness >= 25})
            yield frame
    try:
        if not math.isfinite(fps) or not 0 < fps <= 120:
            raise ValueError('invalid or unsupported frame rate')
        metrics = motion_metrics(decoded_frames(), roi)
    finally:
        capture.release()
    if not samples:
        raise ValueError("no decoded frames")
    usable_fraction = sum(s['usable'] for s in samples) / len(samples)
    quality = {'threshold_version': 'roi-prototype-1',
               'usable_fraction': usable_fraction,
               'quality_ok': usable_fraction >= .8,
               'thresholds': {'brightness_min': 35, 'brightness_max': 240,
                              'sharpness_min': 25, 'usable_fraction_min': .8},
               'samples': samples}
    signal = Signal(
        quality_ok=quality['quality_ok'],
        roi_valid=True,
        motion_frames=metrics["motion_frames"],
        frame_count=metrics["frame_count"],
        identity_verified=False,
        bowl_near=False,  # no detector exists
    )
    decision = propose(signal)
    result = {
        "schema": "carli-vision-local-proposal/1",
        "source": "synthetic_or_explicitly_consented_video",
        "opencv_version": cv2.__version__,
        "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "roi": list(roi),
        "motion": metrics,
        "quality": quality,
        "decision": decision,
        "trace": [
            {'step': 'opencv_roi_measurements', 'frame_count': metrics['frame_count'],
             'motion_frames': metrics['motion_frames'], 'usable_fraction': usable_fraction},
            {'step': 'deterministic_review_routing', 'action': decision['next_action'],
             'reason': decision['observation'], 'feeding_confirmed': False,
             'mutating_tool_invoked': False},
        ],
        "limitations": [
            "No pet detection or identity verification",
            "No feeding classification",
            "Quality thresholds are prototype heuristics, not real-world validation",
            "Pixel movement is not pet identity, contact or eating",
            "No AWS execution",
            "No MCP mutation or owner approval",
        ],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X", "Y", "W", "H"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.video, tuple(args.roi))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "motion_frames": result["motion"]["motion_frames"], "feeding_confirmed": False}))


if __name__ == "__main__":
    main()
