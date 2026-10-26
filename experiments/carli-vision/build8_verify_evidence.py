"""Build8: verify a local Build7 receipt against logs and its checksum.

A matching hash detects accidental modification, not malicious re-signing.
"""
import argparse
import hashlib
import json
from pathlib import Path

def verify(directory):
    root=Path(directory)
    receipt=root/"BUILD7_EVIDENCE.json"
    checksum=root/"BUILD7_EVIDENCE.json.sha256"
    try:
        raw=receipt.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        line=checksum.read_text(encoding="utf-8").strip()
        if line != digest+"  BUILD7_EVIDENCE.json":
            return False,"receipt checksum mismatch"
        data=json.loads(raw)
        if data.get("schema")!="carli-p0a-build7-evidence/1":
            return False,"wrong schema"
        if data.get("mode")!="synthetic_offline_only" or data.get("production_approved") is not False:
            return False,"unsafe mode"
        if data.get("gate_passed") is not True:
            return False,"gate not passed"
        if not isinstance(data.get("git_commit"),str) or len(data["git_commit"])!=40:
            return False,"invalid commit"
        steps=data.get("steps")
        if not isinstance(steps,list) or len(steps)!=2:
            return False,"missing steps"
        names=set()
        for step in steps:
            name=step.get("name")
            if name not in {"boundary","unittest"} or name in names:
                return False,"unexpected step"
            names.add(name)
            if step.get("exit_code") != 0 or type(step.get("exit_code")) is not int:
                return False,"nonzero exit"
            path=root/(name+".log")
            if step.get("log_file")!=path.name:
                return False,"unexpected log path"
            if hashlib.sha256(path.read_bytes()).hexdigest()!=step.get("log_sha256"):
                return False,"log hash mismatch"
        if names!={"boundary","unittest"}:
            return False,"missing gate"
        if "PASS" not in (root/"boundary.log").read_text(encoding="utf-8"):
            return False,"boundary log incomplete"
        unit=(root/"unittest.log").read_text(encoding="utf-8")
        if "Ran " not in unit or "\nOK" not in unit:
            return False,"test log incomplete"
        return True,"verified local receipt and logs"
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        return False,type(exc).__name__

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True)
    args=p.parse_args()
    ok,reason=verify(args.directory)
    print("BUILD8 EVIDENCE VERIFY:", "PASS" if ok else "FAIL", "-",reason)
    return 0 if ok else 1

if __name__=="__main__":
    raise SystemExit(main())
