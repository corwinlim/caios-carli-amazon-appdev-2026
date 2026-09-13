# Amazon AppDev 2026 — Judge Runbook

## One-line thesis

**CAIOS × CARLI turns Alexa+ into a context-aware pet-care interface that remembers longitudinal context, requires owner approval for consequential writes, and records what happened next.**

## Demo boundary

- Synthetic Pika data only.
- Non-diagnostic.
- No production CAIOS credentials or private owner data.
- Owner approval is required before a mutating action.
- Current local demo uses the public-safe MCP gateway and synthetic store.
- AWS runtime integration is shown or claimed only after its runtime proof is complete.

## 0–20 seconds — Problem

Pika is home this evening. A pet parent notices she did not finish dinner. A generic voice assistant can answer a question, but it does not automatically have the governed longitudinal context needed to understand whether this is new, what changed recently, or how to safely record the event.

## 20–40 seconds — CAIOS context

Open `/amazon-agent` and establish that this is a **Synthetic demo** and **Non-diagnostic** flow. Explain that CAIOS owns the canonical companion context; CARLI is the ambient execution layer.

## 40–65 seconds — Prepare, do not mutate

Click **Pika didn't finish dinner**.

Expected result:
- The observation is prepared locally.
- UI displays **Owner Approval Required**.
- No `record_observation` MCP mutation has occurred yet.

## 65–90 seconds — Explicit approval

Click **Approve & Record**.

Expected network path:
1. Browser requests a short-lived confirmation token for the exact `record_observation` payload.
2. Browser calls MCP `tools/call` → `record_observation` with that token.
3. ActionGuard verifies action name, normalized payload, and expiry.
4. Synthetic store records the observation.
5. UI shows `CARE EVENT INPUT RECORDED`.

## 90–120 seconds — Why this is not a basic MCP wrapper

Show the six tools:
- `get_pet_context`
- `get_today_summary`
- `get_recent_changes`
- `record_observation`
- `create_follow_up`
- `generate_health_story`

## 120–145 seconds — Architecture

`Alexa+ / simulator → MCP Streamable HTTP → CAIOS Agent Gateway → bounded context → ActionGuard → CARLI action → CareEvent / outcome`

## 145–165 seconds — AWS Builder proof

Only after verified, show the actual runtime call path and logs. Do not substitute a README mention for runtime proof.

## 165–180 seconds — Closing

“One pet. One meaningful change. One context-aware agent. The owner stays in control, and the outcome becomes memory for the next decision.”

## Judge verification checklist

- [ ] `/amazon-agent` loads without authentication to private production data.
- [ ] Synthetic/non-diagnostic labels are visible.
- [ ] Clicking the dinner scenario does not write before approval.
- [ ] Approval produces confirmation request followed by MCP `record_observation`.
- [ ] Invalid/mismatched/expired confirmation is rejected in automated tests.
- [ ] `tools/list` exposes exactly six tools.
- [ ] Public repository contains setup/run instructions and an open-source license.
- [ ] Prior-work disclosure identifies CAIOS Background IP and hackathon-window additions.
- [x] AWS runtime proof is present before AWS Builder is selected in the final submission.
- [ ] Demo video is public, English, and under three minutes.
