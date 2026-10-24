# CARLi Build 10–17 — Post-deadline delivery freeze

**Scope:** synthetic local CARLi vision observation, read-only proposals, approval and audit dry-run. **Not** a submission receipt for the original Amazon AppDev deadline. Do not merge to main or deploy production.

## Reported Windows gates

| Gate | Evidence from user-provided PowerShell logs | Confidence |
|---|---|---|
| Build 14–15 | 54/54 unittest PASS with ResourceWarning strict mode | user log |
| Build 16 | 60/60 unittest PASS with ResourceWarning strict mode | user log |
| Build 17 | 66/66 unittest PASS in 1.910s with ResourceWarning strict mode | user log |
| Build 17 evidence review | status PASS, failures [] | user log |

Build16 evidence metadata: commit `06b2a2dbb2d443419c0e5d33462601fb79dd6e2e`; SHA256 `8113CD4647C5E3BB8C3FB3034EB4F9FFFA9C4897B5282501A3C4CBE8E3949414`; local file `Downloads/CARLi_Evidence/build16_evidence.json`.

Build17 review reported HEAD `d73c08792536d09bbe48f92b1b9a7a8a156c9662`, and `test_results_independently_verified=false`.

**Important:** These local logs and hashes have been provided in chat, not independently reproduced by GitHub CI or cryptographically bound to a raw unittest output artifact. Build16's `tests_passed` and `test_count` fields were supplied by the CLI caller. Local evidence files are not uploaded to this repository.

## Security and operational limitations

- Synthetic owner is not authenticated. No real owner identity proof.
- SQLite approval and audit records do not share one atomic transaction.
- Simulated uncertain dispatch and consumed-approval/pending-audit states fail closed, but no actual forced-process-kill test was performed.
- No real MCP mutation, AWS live execution, or exactly-once external side-effect guarantee.
- Audit hash chaining is not independently tamper-proof or externally anchored.
- Vision motion/bowl proximity does not establish that a pet ate food.
- Do not expose this prototype as production-ready or represent post-deadline commits as contest-period work.

## Final acceptance decision

**PASS — isolated local synthetic prototype tests and evidence integrity review.**
**NOT APPROVED — production rollout, real MCP dispatch, AWS integration, PR merge, or original contest submission claims.**

## Reproducibility

Run `python -W error::ResourceWarning -m unittest discover -s . -p "test_*.py" -q` in `experiments/carli-vision`. Expected at Build17 commit: 66 tests.

Run `build17_evidence_review.py` with the Build16 JSON and the known SHA/commit to verify file integrity. A PASS checks the artifact and declared metadata, not independent historic test execution.

## Before production consideration

Require authenticated owner identity, atomic outbox/recovery design, actual crash-process injection, network failure replay, tamper-evident external audit, CI-hosted test artifacts, privacy review, and human approval for any real-world mutation.
