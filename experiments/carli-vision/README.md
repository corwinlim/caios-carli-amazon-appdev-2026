# CARLi Vision — isolated post-deadline policy prototype

This folder contains **newly authored** standard-library Python code for conservative decision proposals. It is **not** the operator's original CARLi OpenCV Build 02 or Build 06 source, and it **does not run OpenCV or AWS**.

The Amazon AppDev submission deadline was 2026-10-23 19:00 UTC. These files were added **after** that deadline and must not be represented as part of the original eligible submission.

## Run locally

```powershell
cd experiments/carli-vision
python -m unittest discover -s . -p "test_*.py" -v
```

## Safety contract

- No veterinary diagnosis, feeding confirmation, or autonomous actuation.
- No MCP mutation, confirmation-token issuance, camera capture, or cloud call.
- Poor quality, occlusion, ambiguous pet identity and invalid ROI abstain.
- Proximity to a bowl means *possible proximity*, not eating.
- The existing Alexa+/MCP owner-approval flow must independently authorize any future `record_observation`.

## Follow-up

Integrate the **actual** locally verified OpenCV Build 02 source only after comparing its implementation, fixing the motion detection false-negative, screening secrets/data, and obtaining a reproducible CI result. Keep the Amazon submission timestamp boundary explicit.
