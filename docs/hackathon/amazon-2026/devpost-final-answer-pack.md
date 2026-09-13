# Amazon AppDev 2026 — Final Devpost Answer Pack

Project: **CAIOS x CARLI Home Pet Agent**  
Devpost project ID: `1426014`  
Draft submission ID: `1179816`  
Primary track: **Alexa+**

> Final submission must not be sent until the public video URL is present and the submitter explicitly confirms all three eligibility checkboxes.

## Required fields

### 28285 — Submitter Type
`Individual`

### 28286 — Organization Name
`N/A`

### 28287 — Country of Residence
`Malaysia`

### 28288 — Canada Province
`N/A`

### 28289 — Primary Track
`Alexa+`

### 28290 — Public code repository
`https://github.com/corwinlim/caios-carli-amazon-appdev-2026`

### 28291 — New or existing prior to August 31, 2026?
`Existing, but significantly updated.`

### 28292 — Significant update explanation
CAIOS existed before the hackathon. During the submission window we added the Amazon-specific ambient execution layer: a self-hosted MCP 2025-11-25 Streamable HTTP surface, six public-safe pet-context and care tools, synthetic Pika context, payload-bound owner confirmation for mutations, the CARLI runtime abstraction, a simulated Alexa+ judge experience, real Amazon Bedrock AgentCore Runtime proof, canonical CAIOS PetEvent outcome mapping, automated verification, prior-work disclosure, and a fresh public open-source extraction repository. The CAIOS proprietary memory/retrieval core remains Background IP and is not presented as hackathon-window work.

### 28293 — AWS Builder Mini Challenge
`Yes`

### 28294 — AWS services incorporated and how
We use **Amazon Bedrock AgentCore Runtime** as the AWS execution environment for the CAIOS Home Pet Agent MCP surface. A real AgentCore Runtime is documented as `READY`; `InvokeAgentRuntime` successfully negotiated MCP `2025-11-25`, returned the six CAIOS tools through `tools/list`, and completed a safe read-only `get_pet_context` call using synthetic Pika data. The public web code keeps AWS behind a CAIOS-owned `AgentRuntime` abstraction with an HTTPS-only AgentCore adapter, bounded timeout, and fail-closed non-2xx behavior. AWS receives bounded demo context only and does not become the canonical pet record.

### 28295 — Open Source Mini Challenge
`Yes`

### 28296 — Contribution URL
`https://github.com/corwinlim/caios-carli-amazon-appdev-2026`

### 28297 — Project Repository URL
`https://github.com/corwinlim/caios-carli-amazon-appdev-2026`

### 28298 — GitHub Username
`corwinlim`

### 28299 — Open Source contribution description
We created a new MIT-licensed public repository during the hackathon window containing the Amazon-specific CAIOS × CARLI integration rather than exposing the proprietary CAIOS monorepo. The public slice includes the MCP 2025-11-25 gateway, six tool contracts, synthetic Pika data, owner-confirmation guard, guarded mutation flow, Alexa+ simulation source, AgentCore runtime adapter, canonical PetEvent mapping, CI verification, AWS live-proof documentation, friction log, and Background IP disclosure. This matters because it makes the judged Alexa+/AWS capability reproducible while preserving unrelated commercial IP and private companion data.

### 28300 — Optional Feature Request
**AgentCore MCP session debugger — Important.** A developer-facing view showing protocol-version negotiation, initialize response, session identifiers, content negotiation, `tools/list`, and `tools/call` traces would materially shorten debugging of MCP runtimes and make transport/session mistakes much easier to diagnose.

### 28301 — Optional Friction Log
`https://github.com/corwinlim/caios-carli-amazon-appdev-2026/blob/main/docs/hackathon/amazon-2026/friction-log.md`

### 28302 — Optional Project Testing Link
`PENDING — only provide a deployed /amazon-agent URL after live verification.`

## Product feedback

### 28303 — Q1: Which tools/APIs/SDKs did you use and for what?
We used Alexa+'s MCP integration model as the ambient interface target; MCP `2025-11-25` with Streamable HTTP for tool discovery and invocation; Amazon Bedrock AgentCore Runtime for live AWS-hosted MCP execution proof; Next.js and TypeScript for the simulated Alexa+ experience and server routes; Zod for tool-input validation; and Vitest plus GitHub Actions for deterministic safety and build verification.

### 28304 — Q2: What worked well?
MCP gave us a clean separation between conversational intent and bounded pet-care tools. The Alexa+ simulated-experience path made it possible to prove the human-approval UX without requiring production customer access. AgentCore Runtime successfully hosted an MCP surface and returned a real initialize/tools/list/tools/call path. The combination works well for a product such as CAIOS because the model/runtime can stay replaceable while canonical pet context remains in the application domain.

### 28305 — Q3: What needs work?
The largest friction was MCP session/transport clarity across protocol-era documentation and runtime invocation semantics. It was not immediately obvious which session behavior, headers, and method-specific fields were required for a minimal AgentCore MCP proof. Product-level human confirmation is also left to each developer even when tools can mutate meaningful state. More reference implementations for approval-bound writes and a dedicated MCP session debugger would reduce integration risk.

### 28306 — Q4: How was onboarding?
The basic concepts were approachable, but getting from local MCP code to a verified AWS-hosted invocation required more iteration than a normal hello-world path. The biggest onboarding improvement would be one end-to-end Alexa+ + AgentCore MCP reference showing initialize, session handling, tools/list, tools/call, debugging output, and a simulated Alexa+ UI in one place.

### 28307 — Q5: Would you build with these services again?
Yes. MCP fits CAIOS because it lets us expose a small governed tool surface instead of coupling an assistant directly to our data layer, and AgentCore gives us an AWS execution path without forcing AWS-specific objects into the canonical companion model. We would use the combination again, especially if MCP session diagnostics and human-in-the-loop patterns become more explicit.

## Final eligibility gates — do not auto-answer

### 28308 — Age
`PENDING explicit submitter confirmation`

### 28309 — Eligible Jurisdiction
`PENDING explicit submitter confirmation`

### 28310 — Employee / Promotion Entities
`PENDING explicit submitter confirmation`

## Deliverable gate

- Public GitHub repo: **PASS**
- MIT License: **PASS**
- Alexa+ simulated MCP source: **PASS**
- AWS AgentCore live proof: **PASS**
- Public English demo video under 3 minutes: **PENDING URL**
- Eligibility checkbox confirmation: **PENDING**
- Final Devpost status: **DRAFT / NOT SUBMITTED**
