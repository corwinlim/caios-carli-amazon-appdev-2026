"""Build 11: read-only inventory of legacy synthetic approval/audit databases.

Never opens a writable SQLite connection; never migrates approval tokens.
"""
import argparse
import json
import sqlite3
from pathlib import Path

def _read(path, query):
    path = Path(path)
    if not path.is_file():
        return None
    # mode=ro prevents accidental DB creation and mutation.
    uri = path.resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        db.execute("PRAGMA query_only=ON")
        return db.execute(query).fetchall()
    finally:
        db.close()

def inventory(directory):
    root = Path(directory)
    operations = _read(root / "audit.sqlite",
                       "SELECT operation_id,state,payload_hash FROM operations ORDER BY operation_id")
    approvals = _read(root / "approval.sqlite",
                      "SELECT state,payload_hash FROM approvals ORDER BY token_hash")
    report = {"schema":"carli-build11-inventory/1","mode":"read_only",
              "authorization_inherited":False,"safe_to_dispatch":False,
              "databases_present":{"audit":operations is not None,
                                   "approval":approvals is not None},
              "operations":[],"approval_state_counts":{},
              "limitations":["legacy approval rows lack a reliable operation_id join",
                             "no legacy approval is imported or promoted",
                             "read-only inventory is not a migration"]}
    for state, _ in (approvals or []):
        report["approval_state_counts"][state] = report["approval_state_counts"].get(state,0)+1
    for operation_id,state,payload_hash in (operations or []):
        # Never print raw payload or approval token; a raw payload hash is
        # insufficient to prove operation-bound authorization.
        report["operations"].append({
            "operation_id":operation_id,"legacy_state":state,
            "classification":"manual_review_required",
            "authorized_for_new_engine":False,
            "safe_to_dispatch":False})
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True)
    p.add_argument("--output")
    args=p.parse_args()
    report=inventory(args.directory)
    rendered=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.output:
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(rendered,encoding="utf-8")
    print(rendered,end="")
