"""Build 17: offline evidence manifest verification. No network or mutation."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def git_head(repo):
    return subprocess.run(["git","rev-parse","HEAD"],cwd=repo,check=True,
                          capture_output=True,text=True).stdout.strip()

def verify(evidence_path, repo, expected_sha, expected_commit):
    evidence_path=Path(evidence_path)
    failures=[]
    if not evidence_path.is_file():
        return {"status":"FAIL","failures":["evidence_missing"]}
    actual_hash=sha256(evidence_path)
    if actual_hash.lower()!=expected_sha.lower():
        failures.append("evidence_hash_mismatch")
    try:
        data=json.loads(evidence_path.read_text(encoding="utf-8"))
    except (UnicodeError,ValueError):
        return {"status":"FAIL","failures":failures+["invalid_json"],"actual_sha256":actual_hash}
    if data.get("schema")!="carli-build16-evidence/1":
        failures.append("schema_mismatch")
    if data.get("mode")!="synthetic_local_only" or data.get("real_mcp_invoked") is not False:
        failures.append("safety_boundary_mismatch")
    if data.get("git_commit")!=expected_commit:
        failures.append("evidence_commit_mismatch")
    try:
        current=git_head(repo)
    except (OSError,subprocess.CalledProcessError):
        current=None
        failures.append("git_head_unavailable")
    # New Build17 commit is expected to differ from the Build16 evidence commit.
    if current and current==expected_commit:
        commit_relation="same"
    else:
        commit_relation="different_or_unavailable"
    sidecar=evidence_path.with_suffix(evidence_path.suffix+".sha256")
    if not sidecar.is_file():
        failures.append("sidecar_missing")
    else:
        parts=sidecar.read_text(encoding="utf-8").strip().split()
        if len(parts)!=2 or parts[0].lower()!=actual_hash or parts[1]!=evidence_path.name:
            failures.append("sidecar_mismatch")
    return {"schema":"carli-build17-review/1","status":"PASS" if not failures else "FAIL",
            "failures":failures,"evidence_sha256":actual_hash,
            "evidence_commit":data.get("git_commit"),"working_tree_head":current,
            "commit_relation":commit_relation,
            "reported_test_count":data.get("test_count"),
            "reported_tests_passed":data.get("tests_passed"),
            "test_results_independently_verified":False,
            "post_deadline":True,"real_mcp_invoked":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--repo",required=True)
    p.add_argument("--expected-sha",required=True)
    p.add_argument("--expected-commit",required=True)
    p.add_argument("--output")
    args=p.parse_args()
    result=verify(args.evidence,args.repo,args.expected_sha,args.expected_commit)
    output=json.dumps(result,indent=2,sort_keys=True)+"\n"
    print(output,end="")
    if args.output:
        Path(args.output).write_text(output,encoding="utf-8")
    raise SystemExit(0 if result["status"]=="PASS" else 1)
