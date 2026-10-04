"""Read-only scope verification for the Issue #337 governance candidate."""
import copy
import json
from pathlib import Path
import subprocess

from aisoft_gitea_governance.contract import repository_declarations_sha256
from aisoft_host_access.contract import load_access_contract

BASE = "e2edb3e08194624a6647212571c6cc866298575b"
ACCESS = "codex/config/host-access-broker.json"
GOVERNANCE = "codex/config/gitea-governance.json"


def baseline(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"])


access = json.loads(Path(ACCESS).read_text())
governance = json.loads(Path(GOVERNANCE).read_text())
old_access = json.loads(baseline(ACCESS))
old_governance = json.loads(baseline(GOVERNANCE))
without_access = copy.deepcopy(access)
without_access["projects"] = [p for p in without_access["projects"]
                              if p["project_id"] != "hsdb"]
assert without_access == old_access
without_governance = copy.deepcopy(governance)
without_governance["repositories"] = [r for r in without_governance["repositories"]
                                     if r["name"] != "HSDB"]
old_seal = next(r for r in old_governance["repositories"]
                if r["name"] == "NewEMaint")["routine_live_pilot"]["non_target_repositories_sha256"]
next(r for r in without_governance["repositories"]
     if r["name"] == "NewEMaint")["routine_live_pilot"]["non_target_repositories_sha256"] = old_seal
assert without_governance == old_governance
pilot = next(r for r in governance["repositories"]
             if r["name"] == "NewEMaint")["routine_live_pilot"]
assert repository_declarations_sha256(governance["repositories"], exclude_name="NewEMaint") == pilot["non_target_repositories_sha256"]
contract = load_access_contract(ACCESS, GOVERNANCE)
assert {p.repository for p in contract.projects} == {r.name for r in contract.governance.repositories}
assert len(contract.projects) == 7 and len(contract.operations) == 38
protected = ["AGENTS.md", "codex/runtime/aisoft_host_access/contract.py",
             "codex/runtime/aisoft_gitea_governance/contract.py", "codex/tests/smoke.sh",
             ".gitea/workflows/ci.yml"]
for path in protected:
    assert Path(path).read_bytes() == baseline(path), path
allowed = {"README.md", "03-Issue-Spec-Plan与单闸门开发流程.md", ACCESS, GOVERNANCE,
           "codex/tests/test-host-access-broker.sh", "codex/runtime/tests/test_host_access.py",
           "codex/runtime/tests/test_gitea_governance.py"}
changed = set()
for args in (["git", "diff", "--name-only", "-z", BASE],
             ["git", "ls-files", "--others", "--exclude-standard", "-z"]):
    changed.update(p.decode() for p in subprocess.check_output(args).split(b"\0") if p)
assert all(p in allowed or p.startswith("docs/changes/337-restore-hsdb-governance/")
           for p in changed), sorted(changed)
print(json.dumps({"result": "PASS", "baseline_source": BASE,
                  "approved_contract_commit": "53078bfa0ea42ce0c7fd8ce2bd7d63eaafedb2a8",
                  "only_new_project": "hsdb", "only_new_repository": "HSDB",
                  "existing_access_declarations_unchanged": True,
                  "existing_governance_declarations_unchanged_except_non_target_seal": True,
                  "non_target_seal_matches_same_tree": True,
                  "protected_files_unchanged": protected,
                  "vm_profile_repositories": sorted(p.repository for p in contract.projects
                                                    if p.vm_profile is not None),
                  "project_count": len(contract.projects), "operation_count": len(contract.operations),
                  "production_runtime_changes": False, "secret_values_read_or_printed": False},
                 ensure_ascii=False, indent=2))
