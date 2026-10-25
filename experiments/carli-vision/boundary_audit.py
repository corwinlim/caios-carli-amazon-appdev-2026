"""P0-A Build 4: static architecture guard for the isolated prototype.

AST analysis is a change-control gate, not a Python sandbox/security boundary.
Legacy modules are explicit exceptions and must not grow new callers.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOWED_LEGACY_IMPORTS = {
    "authorized_review_workflow.py": {"build15_workflow"},
    "guarded_review_workflow.py": {"build15_workflow"},
    "build16_recovery.py": {"build15_workflow"},
    "build15_workflow.py": {"persistent_approval"},
}
LEGACY = {"build15_workflow", "persistent_approval", "guarded_review_workflow"}
AUTHORIZED = "authorized_review_workflow"

def inspect_source(filename, source):
    tree = ast.parse(source, filename=filename)
    violations = []
    allowed = ALLOWED_LEGACY_IMPORTS.get(filename, set())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [(node.module or "").split(".")[0]]
        else:
            continue
        for module in modules:
            if module in LEGACY and module not in allowed:
                violations.append(f"{filename}:{node.lineno}: forbidden import {module}")
    return violations

def inspect_tree(root=ROOT):
    violations = []
    for path in sorted(Path(root).rglob("*.py")):
        if path.name.startswith("test_") or "__pycache__" in path.parts:
            continue
        violations.extend(inspect_source(path.name, path.read_text(encoding="utf-8")))
    return violations

if __name__ == "__main__":
    issues = inspect_tree()
    if issues:
        print("\n".join(issues))
        raise SystemExit(1)
    print("CARLi P0-A BUILD4 STATIC BOUNDARY: PASS (non-test imports)")
