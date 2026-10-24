"""Synthetic-only OpenCV ROI motion estimator. No feeding inference."""
import cv2
import numpy as np


def motion_metrics(frames, roi, pixel_threshold=18, changed_fraction_threshold=0.005):
    """Count frames with changed ROI pixels, not ROI average brightness.

    Each frame must have the same ROI bounds. No pet identification is performed.
    """
    x, y, w, h = roi
    if w <= 0 or h <= 0 or x < 0 or y < 0:
        raise ValueError("invalid ROI")
    prev = None
    motion_frames = 0
    total = 0
    fractions = []
    for frame in frames:
        if frame is None or frame.ndim not in (2, 3):
            raise ValueError("invalid frame")
        fh, fw = frame.shape[:2]
        if x + w > fw or y + h > fh:
            raise ValueError("ROI outside frame")
        crop = frame[y:y+h, x:x+w]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        if prev is not None:
            delta = cv2.absdiff(gray, prev)
            fraction = float(np.count_nonzero(delta >= pixel_threshold)) / delta.size
            fractions.append(fraction)
            if fraction >= changed_fraction_threshold:
                motion_frames += 1
        prev = gray
        total += 1
    return {
        "frame_count": total,
        "motion_frames": motion_frames,
        "max_changed_fraction": max(fractions, default=0.0),
        "feeding_confirmed": False,
        "interpretation": "ROI pixel change only; not pet identity or eating",
    }
