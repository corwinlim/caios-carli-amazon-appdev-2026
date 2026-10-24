"""Post-deadline, synthetic-only CARLi vision proposal policy.

Never generates an owner confirmation token, mutates pet state, or confirms feeding.
This is newly authored isolated example code, NOT a copy of local Build 02/06.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Signal:
    quality_ok: bool
    roi_valid: bool
    bowl_near: bool = False
    occluded: bool = False
    multiple_pets: bool = False
    identity_verified: bool = False
    motion_frames: int = 0
    frame_count: int = 0


def propose(signal: Signal) -> dict[str, Any]:
    if not signal.quality_ok:
        outcome, action = "insufficient_video_quality", "request_better_video"
    elif not signal.roi_valid:
        outcome, action = "invalid_region_of_interest", "recalibrate_roi"
    elif signal.multiple_pets:
        outcome, action = "ambiguous_pet_identity", "request_owner_identification"
    elif signal.occluded:
        outcome, action = "occluded_observation", "request_more_evidence"
    elif signal.bowl_near:
        outcome, action = "possible_bowl_proximity", "request_owner_confirmation"
    else:
        outcome, action = "no_relevant_activity_confirmed", "continue_observation"
    return {
        "status": "proposal_only",
        "observation": outcome,
        "next_action": action,
        "feeding_confirmed": False,
        "owner_confirmation": "pending",
        "mutating_tool_invoked": False,
        "signal": asdict(signal),
    }
