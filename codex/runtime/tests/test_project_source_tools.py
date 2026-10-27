"""Session tools on a project-declared checkout, over real HTTP (#434, ADR 0003).

The checkout has no entry in any platform manifest. Every remote step goes
through aisoft-access with the credential the user's own Git credential helper
returns; the fake server answers REST and smart-HTTP Git and accepts nothing
but that credential.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.project_source_fixture import (
    AGENT, BRANCH, NAME, OWNER, ROOT, SENTINEL, SESSION, FakeGitea, GiteaServer, build_project,
    contract_documents, git, write_declaration,
)


def tool_path() -> str:
    directories = ["/usr/bin", "/bin"]
    for binary in ("jq", "python3"):
        found = shutil.which(binary)
        if found:
            directories.append(os.path.dirname(found))
    return ":".join(dict.fromkeys(directories))


class ProjectSourceToolsCase(unittest.TestCase):
    aisoft = ROOT / "codex/tools/aisoft"

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.gitea = FakeGitea()
        self.server = GiteaServer(self.temporary.name, self.gitea)
        self.addCleanup(self.server.close)
        self.gitea.base = self.server.url
        self.issue_url = f"{self.server.url}/{OWNER}/{NAME}/issues/7"
        write, self.names = contract_documents(self.issue_url)
        self.remote, self.canonical, self.linked = build_project(
            self.temporary.name, remote_url=f"{self.server.url}/{OWNER}/{NAME}.git",
            remote_path=self.server.project_root / OWNER / f"{NAME}.git", documents=write)
        git(["config", "credential.helper",
             f"!f() {{ test \"$1\" = get && printf 'username={AGENT}\\npassword={SENTINEL}\\n'; }}; f"],
            cwd=self.canonical)
        home = Path(self.temporary.name) / "home"
        home.mkdir()
        self.env = {"HOME": str(home), "PATH": tool_path(), "LANG": "C", "LC_ALL": "C",
                    "AISOFT_SESSION_ID": SESSION}

    def run_tool(self, *argv: str, check: bool = True, cwd=None) -> subprocess.CompletedProcess:
        result = subprocess.run([str(self.aisoft), "--repo", str(self.linked), *argv],
                                cwd=cwd or self.linked, env=self.env, text=True,
                                capture_output=True, check=False)
        if check and result.returncode != 0:
            self.fail(f"{argv} exited {result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}")
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        return result

    def label_names(self, number: int) -> set[str]:
        return {label["name"] for label in self.gitea.issues[number]["labels"]}


class ProjectSourceToolsTest(ProjectSourceToolsCase):
    def test_labels_provision_aligns_an_empty_repository(self) -> None:
        self.run_tool("labels-provision")
        canonical = json.loads((ROOT / "codex/config/gitea-labels.json").read_text())["canonical"]
        self.assertEqual({label["name"] for label in self.gitea.labels},
                         {entry["name"] for entry in canonical})
        self.run_tool("labels-provision")
        self.assertEqual(len(self.gitea.labels), len(canonical))

    def test_classify_apply_and_verify(self) -> None:
        self.run_tool("labels-provision")
        self.gitea.add_issue(7, "demo change", labels=("needs-analysis",))
        self.run_tool("classify", "--apply", "7")
        self.assertTrue({"type/refactor", "complexity/complex"} <= self.label_names(7))
        verified = self.run_tool("classify", "--verify", "7")
        self.assertIn('"result":"projected"', verified.stdout.replace(" ", ""))

    def test_open_pr_pushes_creates_and_backfills_through_the_helper_credential(self) -> None:
        body = Path(self.temporary.name) / "body.md"
        body.write_text(f"Closes #7\n\nSummary: docs/changes/7-demo-change/{self.names['summary']}\n")
        self.run_tool("open-pr", "7", "--title", "demo", "--body-file", str(body))
        self.assertEqual(len(self.gitea.pulls), 1)
        pull = next(iter(self.gitea.pulls.values()))
        self.assertEqual(pull["head"]["ref"], BRANCH)
        head = git(["rev-parse", "HEAD"], cwd=self.linked)
        self.assertEqual(git(["rev-parse", BRANCH], cwd=self.remote), head)
        summary = (self.linked / "docs/changes/7-demo-change" / self.names["summary"]).read_text()
        self.assertIn(f"pr_url: {pull['html_url']}", summary)
        self.assertIn("status: pr-open", summary)
        self.assertIn("ok", self.server.git_auth)
        self.assertNotIn("other", self.server.git_auth)

    def test_ticket_issue_read_uses_the_project_entry(self) -> None:
        self.run_tool("labels-provision")
        self.gitea.add_issue(7, "demo change", labels=("approved",))
        script = ("import json, sys; from pathlib import Path; "
                  "from aisoft_loop.ticket_execution import read_issue; "
                  "print(json.dumps(read_issue(Path(sys.argv[1]), 7)))")
        result = subprocess.run(["python3", "-c", script, str(self.linked)], cwd=self.linked,
                                env={**self.env, "PYTHONPATH": str(ROOT / "codex/runtime")},
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["html_url"], self.issue_url)

    def test_route_reads_change_control_from_the_declaration(self) -> None:
        production = json.loads(self.run_tool("resolve-route", "7", "--provider", "claude").stdout)
        self.assertEqual(production["route"]["process"], "complex-production")
        # Declared development: the stored production card now contradicts the
        # policy, which is only possible if the declaration was consumed.
        write_declaration(self.linked, change_control="development")
        refused = self.run_tool("resolve-route", "7", "--provider", "claude", check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("route contradicts provider/policy", refused.stderr)
        write_declaration(self.linked, repository=f"{OWNER}/another")
        mismatch = self.run_tool("resolve-route", "7", "--provider", "claude", check=False)
        self.assertIn(f"does not declare {OWNER}/{NAME}", mismatch.stderr)

    def test_project_check_reports_manual_protection_and_live_identity(self) -> None:
        self.run_tool("labels-provision")
        result = self.run_tool("project-check", "--remote", check=False)
        self.assertIn("PASS: labels-readback", result.stdout)
        self.assertIn("PASS: access-identity", result.stdout)
        self.assertIn("MANUAL: ci-context — 人工保护证据已登记：Issue #1", result.stdout)
        self.assertIn("MANUAL: ci-outdated-branch", result.stdout)
        self.assertRegex(result.stdout, r"result: pass=\d+ gap=\d+ skip=\d+ manual=2")
        self.gitea.user = {"login": AGENT, "is_admin": True}
        refused = self.run_tool("project-check", "--remote", check=False)
        self.assertIn("GAP: access-identity — IDENTITY_MISMATCH", refused.stdout)

    def test_explicit_project_is_refused_on_a_declared_checkout(self) -> None:
        result = self.run_tool("complete", "--project", "widget", "--apply", "7", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("declares its own project", result.stderr + result.stdout)

    def test_two_sources_naming_different_repositories_stop(self) -> None:
        manifests = Path(self.temporary.name) / "manifests"
        manifests.mkdir()
        access = json.loads((ROOT / "codex/tests/fixtures/manifests/host-access-broker.json").read_text())
        governance = json.loads((ROOT / "codex/tests/fixtures/manifests/gitea-governance.json").read_text())
        governance["base_url"] = self.server.url
        governance["owner"] = OWNER
        access["projects"][0]["repository"] = NAME
        (manifests / "host-access-broker.json").write_text(json.dumps(access))
        (manifests / "gitea-governance.json").write_text(json.dumps(governance))
        write_declaration(self.linked, repository=f"{OWNER}/widget-renamed")
        self.env.update(AISOFT_ACCESS_MANIFEST=str(manifests / "host-access-broker.json"),
                        AISOFT_GOVERNANCE_MANIFEST=str(manifests / "gitea-governance.json"))
        result = self.run_tool("classify", "--verify", "7", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to pick one", result.stderr + result.stdout)


class ReviewFindingsToolsTest(ProjectSourceToolsCase):
    """Implementation cross-review findings (#434 round 1) on the shell entries."""

    def site_manifests(self, *, base: str, owner: str, repository: str) -> Path:
        manifests = Path(self.temporary.name) / "manifests"
        manifests.mkdir(exist_ok=True)
        access = json.loads((ROOT / "codex/tests/fixtures/manifests/host-access-broker.json").read_text())
        governance = json.loads((ROOT / "codex/tests/fixtures/manifests/gitea-governance.json").read_text())
        governance["base_url"] = base
        governance["owner"] = owner
        access["projects"][0]["repository"] = repository
        (manifests / "host-access-broker.json").write_text(json.dumps(access))
        (manifests / "gitea-governance.json").write_text(json.dumps(governance))
        return manifests

    def test_same_short_name_under_another_owner_and_host_is_a_conflict(self) -> None:
        git(["remote", "add", "mirror", "http://mirror.invalid/elsewhere/widget.git"], cwd=self.canonical)
        manifests = self.site_manifests(base="http://mirror.invalid", owner="elsewhere", repository=NAME)
        self.env.update(AISOFT_ACCESS_MANIFEST=str(manifests / "host-access-broker.json"),
                        AISOFT_GOVERNANCE_MANIFEST=str(manifests / "gitea-governance.json"))
        result = self.run_tool("classify", "--verify", "7", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to pick one", result.stderr + result.stdout)
        checked = self.run_tool("project-check", "--remote", check=False)
        self.assertIn("refusing to pick one", checked.stdout + checked.stderr)
        self.assertNotIn("PASS: access-identity", checked.stdout)

    def test_site_open_pr_runs_the_broker_inside_the_target_checkout(self) -> None:
        platform = Path(self.temporary.name) / "platform"
        (platform / "codex/tools").mkdir(parents=True)
        (platform / "codex" / "config").mkdir()
        shutil.copy2(ROOT / "codex/tools/aisoft", platform / "codex/tools/aisoft")
        for name in ("agent", "runtime"):
            (platform / "codex" / name).symlink_to(ROOT / "codex" / name)
        record = Path(self.temporary.name) / "broker-cwd"
        stub = platform / "codex/tools/host-access-broker.sh"
        stub.write_text(f"#!/bin/sh\npwd -P > '{record}'\nexit 1\n")
        stub.chmod(0o755)
        manifests = self.site_manifests(base=self.server.url, owner=OWNER, repository=NAME)
        for name in ("host-access-broker.json", "gitea-governance.json"):
            shutil.copy2(manifests / name, platform / "codex" / "config" / name)
        (self.linked / ".aisoft/project.json").unlink()
        git(["commit", "-q", "-am", "#7 T01: site-registered checkout"], cwd=self.linked)
        body = Path(self.temporary.name) / "body.md"
        body.write_text(f"Closes #7\n\nSummary: docs/changes/7-demo-change/{self.names['summary']}\n")
        elsewhere = Path(self.temporary.name) / "elsewhere"
        elsewhere.mkdir()
        result = subprocess.run([str(platform / "codex/tools/aisoft"), "--repo", str(self.linked), "open-pr",
                                 "7", "--title", "demo", "--body-file", str(body)], cwd=elsewhere,
                                env=self.env, text=True, capture_output=True, check=False)
        self.assertIn("first push refused", result.stderr)
        self.assertEqual(record.read_text().strip(), os.path.realpath(self.linked))


if __name__ == "__main__":
    unittest.main()
