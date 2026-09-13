# Amazon AppDev 2026 — Demo Script (<3 minutes)

Target runtime: 2:35–2:50. English narration. No copyrighted music.

## 0:00–0:18 — Hook

**Screen:** CAIOS × CARLI title + synthetic Pika demo.

**Narration:**
“What if Alexa+ could remember the context around your pet, but still refuse to make a consequential write without you? This is CAIOS × CARLI: a longitudinal pet-care agent built on MCP, explicit owner approval, and Amazon Bedrock AgentCore.”

## 0:18–0:45 — Problem + architecture

**Screen:** README or a simple architecture view.

**Narration:**
“Pet care happens between visits: meals, behavior, stool, medication response, and small changes that are easy to forget. CAIOS keeps that longitudinal context. CARLI exposes only bounded context through six MCP tools. The runtime never becomes the source of truth; CAIOS remains the canonical companion record.”

## 0:45–1:25 — Alexa+ simulated experience

**Screen:** `/amazon-agent`.

1. Click **Pika didn't finish dinner**.
2. Show that no write has occurred.
3. Show **Owner Approval Required**.
4. Click **Approve & Record**.
5. Show `CARE EVENT INPUT RECORDED`.

**Narration:**
“Here Pika did not finish dinner. CARLI prepares the observation, but nothing is written yet. A mutating tool requires explicit owner approval. The server issues a short-lived confirmation token bound to this exact payload. Only then does the simulator call the same MCP `record_observation` tool an Alexa+ agent would use. If the payload changes, the confirmation fails.”

## 1:25–1:58 — Real AgentCore proof

**Screen:** `docs/hackathon/amazon-2026/aws-live-proof.md` and the public MCP tool registry.

**Narration:**
“This is not only a local simulation. A real Amazon Bedrock AgentCore Runtime is READY and exposed the CAIOS Home Pet Agent over MCP. `InvokeAgentRuntime` returned HTTP 200, negotiated MCP 2025-11-25, returned all six tools, and successfully completed a read-only `get_pet_context` call for synthetic Pika data.”

## 1:58–2:20 — AWS Builder + portability

**Screen:** `apps/web/features/amazon-agent/runtime.ts`.

**Narration:**
“For AWS Builder, CARLI keeps AWS behind a CAIOS-owned `AgentRuntime` boundary. The public code supports deterministic fallback and an AgentCore HTTPS adapter with timeout and fail-closed behavior. That keeps cloud runtime state separate from the pet's canonical record.”

## 2:20–2:40 — Canonical outcome mapping

**Screen:** `apps/web/features/amazon-agent/care-event.ts`.

**Narration:**
“After an approved care action, CARLI projects the outcome into the existing CAIOS `PetEvent(OBSERVATION)` shape with provenance, runtime metadata, owner-approval state, and an idempotency key. We did not invent a hackathon-only data model.”

## 2:40–2:52 — Close

**Screen:** Pika + public GitHub URL.

**Narration:**
“CAIOS remembers. CARLI acts. The owner stays in control. Alexa+ becomes a safe ambient interface to continuous companion care.”

## Recording checklist

- Final uploaded video must remain under 3:00; target 2:45.
- Public YouTube or Vimeo.
- English narration.
- Show the actual `/amazon-agent` interaction, not slides only.
- Show sanitized AgentCore proof.
- Do not expose AWS account IDs, credentials, private URLs, real pet records, or owner data.
- End with `github.com/corwinlim/caios-carli-amazon-appdev-2026` on screen.
