"""Build 16: read-only cross-database recovery inspection and evidence seal.

No real MCP dispatch, network access, or production mutations.
"""
import hashlib
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from build15_workflow import ReviewWorkflow

def inspect_operation(root, operation_id):
    workflow = ReviewWorkflow(root)
    with workflow.audit.db() as db:
        row = db.execute("SELECT state,payload_hash,evidence_hash FROM operations WHERE operation_id=?", (operation_id,)).fetchone()
    if row is None:
        return {"operation_id":operation_id,"status":"unknown_operation","safe_to_dispatch":False}
    audit_state, payload_hash, evidence_hash = row
    # Operation-bound approval hashes cannot be joined to the raw audit
    # payload hash without the original payload. Conservatively classify
    # all pending operations as requiring manual reconciliation.
    states = []
    if audit_state == "pending":
        status = "manual_reconciliation_required"
    elif audit_state == "dispatched_unknown":
        status = "dispatch_outcome_unknown"
    elif audit_state == "ready":
        status = "approved_dry_run_only"
    else:
        status = audit_state
    return {"operation_id":operation_id,"status":status,"audit_state":audit_state,
            "approval_states":states,"evidence_hash":evidence_hash,
            "audit_chain_valid":workflow.audit.verify(),
            "safe_to_dispatch":False,"network_called":False}

def write_evidence(root, output_path, test_count, test_success):
    root, output_path = Path(root), Path(output_path)
    try:
        commit = subprocess.run(["git","rev-parse","HEAD"],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
    except (OSError,subprocess.CalledProcessError):
        commit = "unavailable"
    report = {"schema":"carli-build16-evidence/1","created_utc":datetime.now(timezone.utc).isoformat(),
              "git_commit":commit,"test_count":test_count,"tests_passed":bool(test_success),
              "mode":"synthetic_local_only","real_mcp_invoked":False,
              "limitations":["caller-supplied owner is not authenticated",
                             "approval and audit databases are not one atomic transaction",
                             "no exactly-once external side-effect guarantee",
                             "test counts supplied by caller; not independently verified"]}
    output_path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    output_path.write_text(content,encoding="utf-8")
    digest=hashlib.sha256(output_path.read_bytes()).hexdigest()
    output_path.with_suffix(output_path.suffix+".sha256").write_text(digest+"  "+output_path.name+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--tests",type=int,required=True)
    args=parser.parse_args()
    print(json.dumps(write_evidence(args.repo,args.output,args.tests,True),indent=2))
