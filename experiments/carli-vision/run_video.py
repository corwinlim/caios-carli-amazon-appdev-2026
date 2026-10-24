"""Run post-deadline OpenCV ROI observation on a local video.

Never performs owner approval, feeding confirmation, AWS calls, or MCP mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import cv2
from motion import motion_metrics
from vision_policy import Signal, propose


def run(video: Path, roi: tuple[int, int, int, int]) -> dict:
    if not video.is_file():
        raise FileNotFoundError(video)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        capture.release()
        raise ValueError("video cannot be opened")
    frames = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        capture.release()
    if not frames:
        raise ValueError("no decoded frames")
    metrics = motion_metrics(frames, roi)
    signal = Signal(
        quality_ok=True,  # only decodability; NOT real video quality assessment
        roi_valid=True,
        motion_frames=metrics["motion_frames"],
        frame_count=metrics["frame_count"],
        identity_verified=False,
        bowl_near=False,  # no detector exists
    )
    result = {
        "schema": "carli-vision-local-proposal/1",
        "source": "synthetic_or_explicitly_consented_video",
        "opencv_version": cv2.__version__,
        "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "roi": list(roi),
        "motion": metrics,
        "decision": propose(signal),
        "limitations": [
            "No pet detection or identity verification",
            "No feeding classification",
            "quality_ok only means video decoded",
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
