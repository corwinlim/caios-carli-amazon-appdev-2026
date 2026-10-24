"""Build 11: create a review-only proposal from a Build 10 JSON receipt.

No token minting, MCP invocation, database write or feeding classification.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def create_proposal(evidence: dict, evidence_bytes: bytes) -> dict:
    if evidence.get("schema") != "carli-vision-local-proposal/1":
        raise ValueError("unsupported evidence schema")
    motion = evidence.get("motion", {})
    decision = evidence.get("decision", {})
    if motion.get("feeding_confirmed") is not False:
        raise ValueError("feeding must remain unconfirmed")
    if decision.get("mutating_tool_invoked") is not False:
        raise ValueError("unexpected mutation flag")
    if decision.get("owner_confirmation") != "pending":
        raise ValueError("owner approval must be pending")
    frames = motion.get("frame_count")
    moving = motion.get("motion_frames")
    if type(frames) is not int or type(moving) is not int or not (0 <= moving < frames):
        raise ValueError("invalid motion counts")
    return {
        "schema": "carli-vision-owner-review/1",
        "status": "awaiting_explicit_owner_review",
        "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        "evidence_video_sha256": evidence.get("video_sha256"),
        "observation_type": "unclassified_roi_pixel_motion",
        "summary": f"Detected ROI pixel changes on {moving} of {frames} frames; this does not establish pet identity, eating or feeding.",
        "motion_frames": moving,
        "frame_count": frames,
        "feeding_confirmed": False,
        "approved": False,
        "confirmation_token": None,
        "mcp_tool_invoked": False,
        "proposed_mutation": None,
        "next_step": "Owner must review context and explicitly compose and approve an exact observation; use the existing MCP approval path separately.",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raw = args.evidence.read_bytes()
    result = create_proposal(json.loads(raw), raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "evidence_sha256": result["evidence_sha256"], "mcp_tool_invoked": False}))


if __name__ == "__main__":
    main()
