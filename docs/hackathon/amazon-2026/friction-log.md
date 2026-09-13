# Amazon AppDev 2026 — Friction Log

Project: CAIOS × CARLI Home Pet Agent  
Primary track: Alexa+  
Mini challenge target: AWS Builder

This log records concrete developer friction encountered during hackathon-window work. It is intentionally factual and does not imply defects beyond what was observed.

## Entry 1 — MCP session model ambiguity

**Task attempted:** Choose the smallest compliant self-hosted MCP transport for an Alexa+ submission.  
**Expected:** A single obvious server shape for MCP 2025-11-25.  
**Observed:** Current MCP material spans both 2025-11-25 and newer protocol-era guidance, while Streamable HTTP can be implemented with or without server-issued session IDs.  
**Severity:** Medium.  
**Workaround:** Keep the hackathon gateway stateless and implement the required handshake/tool methods while pinning the advertised protocol version to `2025-11-25`.  
**Suggestion:** Alexa+ hackathon docs should include one minimal reference server showing the required `initialize`, `tools/list`, `tools/call`, transport headers, and whether session IDs are optional for judging.  
**Priority:** Important.

## Entry 2 — Existing-product significant-update boundary

**Task attempted:** Reuse CAIOS without exposing proprietary Background IP or presenting pre-existing work as hackathon-window work.  
**Expected:** A clear checklist for what must be newly built versus what can remain Background IP.  
**Observed:** Rules allow significantly updated existing projects, but teams still need to construct their own evidence trail for what changed after the submission period opened.  
**Severity:** Medium.  
**Workaround:** Isolate the Alexa+/MCP adapter, synthetic Pika dataset, confirmation guard, simulator, tests, and submission docs on a dedicated feature branch and public-repo manifest.  
**Suggestion:** Provide a recommended prior-work disclosure template with fields for baseline commit, hackathon commit range, new features, reused Background IP, and demo evidence.  
**Priority:** Important.

## Entry 3 — Public repository versus proprietary core

**Task attempted:** Meet the public open-source repository requirement while preserving CAIOS proprietary longitudinal-memory implementation.  
**Expected:** Clear guidance for submissions that extend a private commercial product.  
**Observed:** The submission repository must be public and functional, so a direct mirror of the commercial monorepo would disclose unrelated proprietary implementation.  
**Severity:** High for startup entrants.  
**Workaround:** Define a public-safe extraction manifest containing only the hackathon adapter, contracts, synthetic data, tests, demo UI, setup instructions, evidence docs, and license.  
**Suggestion:** Explicitly document that a reproducible submission-specific open-source slice is acceptable when it contains all code necessary to run the judged project and clearly discloses Background IP boundaries.  
**Priority:** Critical.

## Entry 4 — Confirmation semantics for agentic writes

**Task attempted:** Let an Alexa+/MCP agent record a pet observation without permitting silent autonomous mutations.  
**Expected:** A standard approval primitive in the track starter architecture.  
**Observed:** Tool invocation itself does not define the product-level semantics for binding human approval to the exact consequential payload.  
**Severity:** High for care workflows.  
**Workaround:** Add a short-lived confirmation token bound to action name, normalized payload, and expiry; changed payloads require new approval.  
**Suggestion:** Include human-in-the-loop confirmation patterns in Alexa+ agent examples, especially for caretaking, purchasing, access, health, and smart-home actions.  
**Priority:** Important.

## Entry 5 — Local proof versus sponsor-runtime proof

**Task attempted:** Build sponsor-specific AWS runtime integration without weakening CAIOS vendor portability.  
**Expected:** Runtime integration examples that keep domain contracts separate from cloud SDK objects.  
**Observed:** It is easy for a hackathon implementation to leak provider-specific request/response types into product-domain code.  
**Severity:** Medium.  
**Workaround:** Keep AWS behind a CAIOS-owned runtime adapter and preserve canonical PetEvent/CareEvent-shaped data independently of Bedrock, AgentCore, or Strands payloads.  
**Suggestion:** Sponsor samples should demonstrate an explicit domain/adapter boundary, not only direct SDK calls from UI or business logic.  
**Priority:** Nice-to-have.
