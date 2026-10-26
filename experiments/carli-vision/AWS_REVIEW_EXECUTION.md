# CARLi OpenCV → AWS review proof

Status: implementation and local SDK-boundary tests only. **NOT DEPLOYED / NO LIVE AWS VISION PROOF.**

## Why this component matters

OpenCV locally measures each video ROI. The proposed AWS Lambda validates the complete measured evidence, recomputes quality rather than trusting a client-supplied conclusion, selects recapture / human review / continued observation, and emits an evidence-hash-correlated log event. It does not classify eating or mutate care records. This is a proposed meaningful AWS component; contest acceptance is not guaranteed by its presence.

The current cloud code is standard-library-only and independent of the local OpenCV installation. The published numerical quality thresholds match the local prototype. Evidence hashes bind the submitted JSON to its response/log, but cannot prove that the caller supplied authentic video measurements.

## Current external blocker

On 2026-10-26 two AWS Core STS checks returned different, non-target accounts and Root principals. Neither matched the current AWS11 target account **the separately verified approved account**. No resource reads/writes or Lambda invocation followed those checks. Restore the intended authorized assumed-role connection; do not use Root or disable organizational restrictions.

The earlier `CARLi_AWS11_Collector_Completeness_Fix.zip` is a separate local simulation/reference and read-only collector. Its test passes or YAML do not establish this new OpenCV router as deployed.

## Prepare and test

```powershell
python -m pip install -r requirements-aws.txt
python -W error::ResourceWarning -m unittest discover -s . -p 'test_*.py' -v
python run_video.py --video YOUR_CONSENTED_CLIP.mp4 --roi 0 0 160 120 --out evidence/video-result.json
```

Use valid ROI pixel coordinates for your input. Tests use generated geometric footage and botocore Stubber for external SDK responses. They are not live AWS receipts.

## Deployment candidate

`cloud-review-template.yaml` is a plain CloudFormation candidate, **not executed or service-validated here**. It proposes one private Lambda, a dedicated log group with seven-day retention and an execution role restricted to that log group. No public API, pet-data store, device, production dependency, or existing CARLi resource is changed by this candidate. Artifact bucket, immutable object version and code digest must be supplied. Review the change set and account before separately authorizing deployment; no deployment command is included in the proof runner.

Create a ZIP containing only `vision_cloud.py` at its root. The SHA-256 digest of the ZIP, base64 encoded, becomes the Lambda `CodeSha256`. Use an approved private artifact bucket and an immutable S3 object version; do not upload keys or raw videos. An authorized operator must deploy and publish an actual version before proof execution. Name: `carli-opencv-review-staging`; handler: `vision_cloud.handler`; runtime: Python 3.12. The versioned ARN must end in a positive integer, never `$LATEST` or an alias.

## Live proof, after deployment is independently approved and verified

```powershell
python aws_vision_proof.py `
  --profile YOUR_APPROVED_SSO_PROFILE `
  --expected-account YOUR_APPROVED_ACCOUNT_ID `
  --evidence evidence/video-result.json `
  --function-arn YOUR_ACTUAL_VERSIONED_STAGING_ARN `
  --code-sha256 YOUR_ACTUAL_BASE64_ZIP_DIGEST `
  --out evidence/aws-runs
```

Placeholders must be replaced with actual inspected values. The runner never logs in, deploys, updates code, changes IAM, changes SCP, or writes pet state. The existing function invocation and its AWS logs may incur normal service charges.

Execution gates: correct account and assumed role → exact deployed function/runtime/version/code digest → Invoke → response evidence digest/action check → correlated Lambda request ID/log event and SDK request ID. Each run has a new output directory. Any failure produces BLOCKED, not a stale PASS. A PASS establishes only this linked invocation, not production authorization, animal accuracy, complete owner confirmation, award eligibility or final submission.

## Remaining delivery

Restore target role access; service-validate/review deployment; obtain real linked AWS receipts for dark/moving/static inputs; complete rendered-browser QA and authorized care-record integration; evaluate consented dog/cat footage; record ≤5-minute working demo; finish OpenCV-specific report and submission archive. Preserve the existing Amazon AppDev and Nebius submission boundaries.
