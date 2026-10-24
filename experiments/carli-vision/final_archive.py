"""Build 17 final offline archive: validate evidence before issuing a local receipt.

Never contacts GitHub, AWS, or MCP. Does not assert independent historical test execution.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BUILD16_SHA = "8113cd4647c5e3bb8c3fb3034eb4f9fffa9c4897b5282501a3c4cbe8e3949414"
BUILD16_COMMIT = "06b2a2dbb2d443419c0e5d33462601fb79dd6e2e"
BUILD17_COMMIT = "d73c08792536d09bbe48f92b1b9a7a8a156c9662"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence-dir", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--test-log", required=True, help="Raw captured stdout+stderr of a fresh strict unittest run")
    args = p.parse_args()
    folder = Path(args.evidence_dir).resolve()
    repo = Path(args.repo).resolve()
    build16 = folder / "build16_evidence.json"
    sidecar = folder / "build16_evidence.json.sha256"
    review = folder / "build17_review.json"
    log = Path(args.test_log).resolve()
    failures = []
    for f in (build16, sidecar, review, log):
        if not f.is_file():
            failures.append("missing: " + str(f))
    if failures:
        raise ValueError("; ".join(failures))
    if digest(build16) != BUILD16_SHA:
        failures.append("build16 SHA mismatch")
    parts = sidecar.read_text(encoding="utf-8").strip().split()
    if len(parts) != 2 or parts != [BUILD16_SHA, build16.name]:
        failures.append("build16 sidecar mismatch")
    b16 = json.loads(build16.read_text(encoding="utf-8"))
    r17 = json.loads(review.read_text(encoding="utf-8"))
    if b16.get("git_commit") != BUILD16_COMMIT or b16.get("mode") != "synthetic_local_only" or b16.get("real_mcp_invoked") is not False:
        failures.append("build16 metadata mismatch")
    if r17.get("status") != "PASS" or r17.get("failures") != [] or r17.get("evidence_sha256", "").lower() != BUILD16_SHA:
        failures.append("build17 review mismatch")
    if r17.get("working_tree_head") != BUILD17_COMMIT or r17.get("test_results_independently_verified") is not False:
        failures.append("build17 review provenance mismatch")
    content = log.read_text(encoding="utf-8-sig", errors="replace")
    if "Ran 66 tests" not in content or "OK" not in content or "FAILED (" in content or "Traceback (most recent call last)" in content:
        failures.append("test log does not show a clean 66-test result")
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("cannot inspect git repository") from exc
    if dirty:
        failures.append("git working tree dirty; archive only from clean checkout")
    if failures:
        raise ValueError("; ".join(failures))
    receipt = {
        "schema": "carli-final-ship-receipt/1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "LOCAL_SYNTHETIC_PROTOTYPE_ACCEPTED",
        "production_approved": False,
        "contest_submission_proven": False,
        "post_deadline": True,
        "git_head_at_archive": head,
        "build16_commit": BUILD16_COMMIT,
        "build17_review_commit": BUILD17_COMMIT,
        "windows_tests": {"expected": 66, "result": "PASS_REPORTED_IN_CAPTURED_LOCAL_LOG",
                          "independently_reexecuted_by_archive_script": False},
        "files": {f.name: {"sha256": digest(f), "bytes": f.stat().st_size} for f in (build16, sidecar, review, log)},
        "limitations": [
            "No authenticated owner identity", "Non-atomic approval and audit databases",
            "No actual forced-process-kill validation", "No live MCP or AWS execution",
            "No exactly-once external side-effect guarantee",
            "Local logs are user-generated, not independent CI attestation",
        ],
    }
    output = folder / "CARLI_FINAL_SHIP_RECEIPT.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    archive = folder / "CARLI_BUILD10_17_FINAL_ARCHIVE.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in (build16, sidecar, review, log, output):
            z.write(f, arcname=f.name)
    archive_hash = digest(archive)
    (folder / (archive.name + ".sha256")).write_text(archive_hash + "  " + archive.name + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "receipt": str(output), "archive": str(archive),
                      "archive_sha256": archive_hash, "git_head": head}, indent=2))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print("FINAL ARCHIVE FAIL: " + str(e), file=sys.stderr)
        sys.exit(1)
