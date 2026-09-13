# CAIOS × CARLI — Amazon AppDev 2026

Amazon AppDev submission slice for a guarded companion-care agent using Alexa+/MCP and AWS AgentCore.

## Included
- Six MCP 2025-11-25 tools for bounded pet context and care actions.
- Synthetic Pika data only.
- Explicit owner confirmation before mutating actions.
- CARLI runtime abstraction with deterministic fallback and AWS AgentCore adapter.
- Canonical CAIOS-style PetEvent write-back mapping.
- Judge simulator and automated tests.

## Excluded
CAIOS core memory/retrieval internals, production pet data, credentials, proprietary scoring, unrelated commercial code, and owner PII remain Background IP and are not included here.

## Safety
This project is non-diagnostic. CARLI cannot diagnose, prescribe, or autonomously perform consequential pet-care actions. Mutating actions require explicit owner confirmation.

## Run
```bash
cd apps/web
npm install
npm run test
npm run typecheck
npm run dev
```

Open `http://localhost:3000/amazon-agent`.

See `docs/hackathon/amazon-2026/prior-work-disclosure.md` for the Background IP boundary.
