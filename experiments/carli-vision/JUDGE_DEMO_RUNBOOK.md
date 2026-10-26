# CARLi Eyes — local judge demo

Run from the actual `feat/opencv-judge-demo` branch. The app is a loopback-only prototype; a repository URL is not a public running endpoint.

## Windows

Extract the branch ZIP fully, open PowerShell in `experiments/carli-vision`, then:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start_judge_demo.ps1
```

Python 3.12 is required. The script installs pinned dependencies in `.venv`, runs the full suite, generates explicitly labelled synthetic clips, and starts the local server. It does not edit system execution policy, log in, deploy or change Devpost. Windows execution has not been independently run in the Linux build workspace.

Open the printed URL, normally http://127.0.0.1:8080, and paste the printed local demo token. Leave the terminal running. Use Ctrl+C to stop.

## Linux/macOS

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-aws.txt
python -W error::ResourceWarning -m unittest discover -s . -p 'test_*.py' -v
python generate_demo_clips.py
python review_demo.py
```

## Four-minute recording plan

1. 0:00–0:25 — Introduce the team and problem. Explicitly label the prototype and any generated clips.
2. 0:25–1:10 — Upload `SYNTHETIC-dark.avi`, use the full-frame ROI, click Review video. Show the request for clearer video and absence of an approval control.
3. 1:10–2:05 — Upload `SYNTHETIC-moving.avi`. Show sampled frames with timestamps, measured visual changes and the human-review request. Do not call them feeding/contact detections.
4. 2:05–2:50 — Enter a conservative note, save the local parent review, reload records and export JSON. Show feeding_confirmed=false and caios_written=false. This is local SQLite persistence, not production care write-back.
5. 2:50–3:20 — Upload `SYNTHETIC-static.avi`. Show continued observation instead of inferring refusal to eat.
6. 3:20–4:00 — Explain OpenCV, routing and the AWS boundary. **Only show AWS verification as successful after a genuine invocation passes.** Until then show the blocked status and state that the competition AWS gate is unresolved. This recording alone is not final submission certification.

Replace or supplement geometric fixtures with consented real cat/dog footage and manual labels before claiming pet-specific usefulness. A ≤5-minute public/unlisted video is still required; no video upload or live screen-share arrangement was performed by this code change.

## Optional AWS mode

After independently approved staging deployment and correct assumed-role credentials, set `CARLI_AWS_PROFILE`, `CARLI_AWS_ACCOUNT`, `CARLI_AWS_FUNCTION_ARN` (numeric version) and `CARLI_AWS_CODE_SHA256` in the server process. Then restart. The Verify AWS review button uses the same gated collector as `aws_vision_proof.py` and checks the exact current clip. Configuration does not equal verified execution. No cloud call occurs automatically on upload.

## Verification scope

Fresh local execution: 172 Python tests pass. Six new tests exercise real HTTP upload, encoded video analysis, SQLite save/export, repeated approval, unauthenticated access, dark-video rejection, blocked AWS, cross-origin rejection and malformed inputs. JavaScript syntax checks pass. Desktop/mobile rendered-browser validation remains outstanding because this executor's local server is separate from the connected user's computer; do not claim screenshots or browser interaction proof from HTTP tests.

Single demo token represents one local demo parent. This is not production identity, authoritative pet authorization, cryptographically signed audit or a multi-user service. The server binds only to 127.0.0.1. Do not expose it through a public tunnel. Local raw clips, sampled frames and reviews remain in `evidence/review-demo`; no retention/delete workflow exists yet. Review corrections require a new audited mechanism and are currently rejected.
