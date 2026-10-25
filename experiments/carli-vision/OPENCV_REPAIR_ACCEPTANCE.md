# OpenCV quality and receipt repair — 2026-10-26

Scope: isolated local prototype repair. No AWS runtime or competition submission is certified by this change.

## Changes

- Receipt verifier reads real LF/CRLF completion lines, rejects failed/empty runs and escaped or unrelated OK strings. Checksum matching remains an accidental-change check, not cryptographic authenticity.
- Video processing measures ROI brightness and Laplacian sharpness on every frame, conservatively abstaining when fewer than 80% of frames meet prototype thresholds.
- Clear pixel movement requests owner review; clear static input continues observation; inadequate quality requests a better video. A trace records measured values and the resulting action.
- Video processing streams frames rather than retaining the entire decoded clip. Limits: 50 MiB, 60 seconds, 7200 frames, 1080p and 120 fps.
- Python dependencies are pinned and a dedicated CI workflow runs the Python suite.

## Run

From `experiments/carli-vision`, using Python 3.12:

```bash
python -m pip install -r requirements.txt
python -W error::ResourceWarning -m unittest discover -s . -p 'test_*.py' -v
python run_video.py --video YOUR_CONSENTED_VIDEO.mp4 --roi 0 0 160 120 --out evidence/video-result.json
```

On Windows, use the same commands with your virtual environment's Python executable. Choose ROI coordinates within the actual input dimensions. Use synthetic or explicitly consented video. No camera or cloud connection is opened.

Fresh local result at this change: 154 tests passed, including encoded dark/blurred/overexposed/mixed-quality/clear moving/clear static clips. These are synthetic correctness fixtures, not animal-behaviour validation. GitHub CI status must be checked independently after publication.

## Interpretation and remaining gates

Quality thresholds are hand-selected prototype heuristics and need calibration on labelled cat/dog clips. Low texture can be rejected conservatively. Camera movement, lighting changes and compression may trigger review. No pet, bowl, identity, contact or occlusion detector is implemented here. Pixel movement is never eating, and absence of motion is never refusal to eat. All decisions preserve feeding_confirmed=false and mutating_tool_invoked=false.

The local event trace demonstrates visual-result-dependent routing; it does not establish the full Agentic Vision award integration, live owner approval, AWS calls or persisted care write-back. Existing signed demo-identity/grant and approval-dry-run modules are unchanged. The quality gate does not authenticate the baby or parent.

AWS integration evidence, consented real-animal evaluation, complete OpenCV report/diagram, working judge demo, video and Devpost receipt remain outstanding. Do not copy Nebius or Amazon AppDev submission fields into this OpenCV entry. No production/main changes or Devpost submission are part of this repair.
