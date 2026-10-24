# CARLi Vision Evidence — post-deadline extension (2026-10-24)

> **Not part of the October 23, 2026 Amazon AppDev submission cutoff.** This is a subsequent research/prototype extension, published for transparency. It must not be presented as functionality available at the competition deadline or as an amendment to the frozen submission.

## Where this fits

The Amazon AppDev slice already provides Alexa+/MCP Streamable HTTP, six tool contracts, deterministic owner-approval guard, a synthetic Pika simulator, and a separate, documented live AgentCore MCP read-only proof. See [AWS live proof](./aws-live-proof.md) and [prior-work disclosure](./prior-work-disclosure.md).

CARLi OpenCV work explores an **observation-only** computer vision input that could eventually propose an event to the existing **owner-confirmed** `record_observation` tool. **No automatic write-back**, feeding diagnosis, or autonomous device action is claimed.

## Verified local evidence supplied by operator

| Item | Evidence | Boundary |
| --- | --- | --- |
| OpenCV runtime | `cv2.__version__ == 5.0.0`, `opencv-python 5.0.0.93` | Local Windows Python 3.14.6 only |
| Synthetic clip | 640 × 480, 15 fps, 150 frames / 10 seconds | Generated imagery, not real animal footage |
| Decision policy | 13/13 unit tests passed in Build 02 | Tests policy signals, not real-world feeding classification |
| AWS decision handler | 7/7 synthetic tests passed in Build 06 | Local-only; NOT an AWS invocation |
| Output contract | `feeding_confirmed: false`; human confirmation remains pending | Abstention is intentional |
| AWS identity check | STS succeeded but pointed to account `6168…8598` with Root ARN; target account is `0811…1283` | **Deployment blocked** pending verified authorized non-Root credentials |

### Critical known gap

The generated synthetic video contains a moving shape, but the reported `motion_frames` was **0**. The original ROI mean-difference threshold failed to register that movement. This is an unresolved detection-quality problem: do not claim working animal activity recognition or accurate feeding inference.

## Proposed interface: separate untrusted vision from authorized action

```text
synthetic/consented video
  → OpenCV 5 ROI quality / motion signals
  → conservative proposed observation or abstention
  → review surface (synthetic evidence + uncertainty)
  → explicit owner approval, exact payload confirmation
  → existing MCP record_observation
  → synthetic CAIOS-style PetEvent
```

This is a **design contract**, not a verified end-to-end integration. Vision output must never issue or forge the `confirmation_token`, and it must never call a mutating tool on its own.

## Acceptance gates before integration

1. Repair and regression-test localized movement detection; include no-motion, movement, occlusion, multiple-pet and poor-quality fixtures.
2. Supply a minimal, reproducible public-safe OpenCV script and sanitized deterministic input/evidence output. Never publish unconsented camera footage.
3. Map vision output into a *proposal* compatible with the existing `record_observation` schema (source `vision`), but prohibit direct mutation.
4. Prove negative paths: no token, mismatched payload, expired token, and declined owner approval.
5. Verify any AWS execution independently with non-Root STS identity, Request ID and logs; never use the wrong account or a root principal.
6. Run repository CI and capture exact SHA plus run URL before claiming PASS.

## Build separation

- **Amazon AppDev 2026 submission:** Alexa+/MCP + guarded synthetic pet workflow + documented AgentCore MCP proof, all assessed against original submission timestamp.
- **CARLi OpenCV prototype:** subsequent local observation-only development; has *not* demonstrated AWS OpenCV execution.
- **CAIOS production:** excluded. Never import production credentials, health records, proprietary models, or unrestricted private memory.

## Verification commands (operator's separate local prototype)

```powershell
cd "$env:USERPROFILE\Downloads\carli_build06"
$python = "$env:USERPROFILE\Downloads\CARLi_OpenCV_Build02\.venv\Scripts\python.exe"
& $python -m unittest discover -s tests -v
```

The actual Build 02 and Build 06 Python source has **not** been pushed in this documentation-only commit. Reproducing OpenCV measurement from this repository alone is **not yet possible**. The documented local test results are operator-provided evidence, not newly run GitHub CI.
