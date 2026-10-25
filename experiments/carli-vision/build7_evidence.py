"""Build7: evidence from subprocess exit status, never caller-supplied PASS.

Writes only under a caller-chosen local output directory. Does not deploy.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def run_gate(output_dir, *, root=ROOT, python=None):
    root=Path(root).resolve()
    output_dir=Path(output_dir).resolve()
    if output_dir == root or root in output_dir.parents:
        raise ValueError("output directory must be outside source tree")
    output_dir.mkdir(parents=True,exist_ok=True)
    interpreter=python or sys.executable
    steps=[
        ("boundary", [interpreter,"-B","boundary_audit.py"]),
        ("unittest", [interpreter,"-B","-W","error::ResourceWarning",
                      "-m","unittest","discover","-s",".","-p","test_*.py","-q"]),
    ]
    results=[]
    for name,command in steps:
        completed=subprocess.run(command,cwd=root,capture_output=True,text=True,
            encoding="utf-8",errors="replace",timeout=180)
        log=(completed.stdout or "")+(completed.stderr or "")
        logfile=output_dir/(name+".log")
        logfile.write_text(log,encoding="utf-8")
        results.append({"name":name,"exit_code":completed.returncode,
            "log_file":logfile.name,"log_sha256":hashlib.sha256(logfile.read_bytes()).hexdigest()})
    git=subprocess.run(["git","rev-parse","HEAD"],cwd=root,
        capture_output=True,text=True,timeout=15)
    commit=git.stdout.strip() if git.returncode==0 else None
    report={
        "schema":"carli-p0a-build7-evidence/1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "git_commit":commit,
        "python":interpreter,
        "mode":"synthetic_offline_only",
        "production_approved":False,
        "real_mcp_invoked":False,
        "gate_passed":bool(commit) and all(x["exit_code"]==0 for x in results),
        "steps":results,
        "limitations":[
            "Local test process, not independent CI attestation",
            "Legacy modules remain importable; static audit is not a sandbox",
            "No production identity provider or administrative grant authorization",
            "Separate SQLite approval and audit databases are not atomic",
            "No real MCP/AWS dispatch or forced process-kill test",
            "Git commit is captured at run time; dirty tree must be checked separately"
        ]
    }
    dest=output_dir/"BUILD7_EVIDENCE.json"
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    (output_dir/"BUILD7_EVIDENCE.json.sha256").write_text(
        digest+"  BUILD7_EVIDENCE.json\n",encoding="utf-8")
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    report=run_gate(args.output)
    print("BUILD7 GATE:", "PASS" if report["gate_passed"] else "FAIL")
    print("EVIDENCE:",str(Path(args.output).resolve()/"BUILD7_EVIDENCE.json"))
    return 0 if report["gate_passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
