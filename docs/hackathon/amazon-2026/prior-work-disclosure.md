# Amazon AppDev 2026 — Prior Work Disclosure

## Background IP

CAIOS existed before the Amazon Developer Hackathon 2026. Pre-existing Background IP includes the private CAIOS companion-data platform, longitudinal pet event model, memory/context architecture, recommendation/evidence pipeline, production application, and proprietary implementation details not required to run this hackathon submission.

CARLI is the CAIOS physical-world execution direction. The product thesis—using ambient interfaces and connected devices to observe or assist pet care—also predates this submission.

## Hackathon-window work

The Amazon submission is a significant update built during the eligible hackathon window. Submission-specific work includes:

- Alexa+/MCP public tool contracts for a bounded synthetic Pika workflow.
- A self-hosted stateless Streamable HTTP MCP gateway advertising protocol version `2025-11-25`.
- Synthetic Pika context and recent-change provider for judge testing without production data.
- Payload-bound, expiring owner-confirmation guard for mutating actions.
- Guarded synthetic observation and follow-up store.
- MCP tool dispatcher with schema validation and error handling.
- Alexa+ judge simulator demonstrating approval before mutation.
- Automated contract, safety, component, and end-to-end tests.
- Amazon product-feedback/friction evidence and public-repository extraction controls.
- AWS runtime adapter and CAIOS canonical write-back integration are claimed only where implemented and verified.

## Claim boundary

The submission must not imply that the hackathon created the CAIOS core platform. The judging claim is narrower: Amazon developer technology is being used to add a new ambient agent interface and guarded execution path to a pre-existing companion intelligence platform.

The submission repository contains the Amazon-specific integration slice but excludes unrelated proprietary CAIOS core implementation, production credentials, private owner/pet data, and proprietary scoring logic.

## Data disclosure

All Pika data used by the Amazon judge flow is synthetic demo data. It must not be presented as a veterinary record, clinical validation dataset, or evidence of medical outcome.
