"""End to end: a project with no platform record runs the whole flow (#434, AC-3).

The project receives only the exported .aisoft/ tool kit. The platform manifest
paths point nowhere, PATH has no platform checkout, and there is no .agent.env:
every step must be served by the project's own .aisoft/bin entries, its
.aisoft/project.json and the credential its own Git helper returns.
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
    contract_documents, export_tool_kit, git, write_declaration,
)
from tests.test_project_source_tools import tool_path


class ProjectSourceEndToEndTest(unittest.TestCase):
    def build(self, *, lifecycle: str = "none", verification: bool = False,
              change_control: str = "production") -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.gitea = FakeGitea()
        self.server = GiteaServer(self.temporary.name, self.gitea)
        self.addCleanup(self.server.close)
        self.gitea.base = self.server.url
        self.gitea.remote = self.server.project_root / OWNER / f"{NAME}.git"
        self.issue_url = f"{self.server.url}/{OWNER}/{NAME}/issues/7"
        write, self.names = contract_documents(self.issue_url, verification=verification,
                                               development=change_control == "development")

        def prepare(canonical: Path) -> None:
            export_tool_kit(canonical)
            write_declaration(canonical, deployment_lifecycle=lifecycle, change_control=change_control)

        self.remote, self.canonical, self.linked = build_project(
            self.temporary.name, remote_url=f"{self.server.url}/{OWNER}/{NAME}.git",
            remote_path=self.server.project_root / OWNER / f"{NAME}.git", documents=write,
            prepare_main=prepare)
        git(["config", "credential.helper",
             f"!f() {{ test \"$1\" = get && printf 'username={AGENT}\\npassword={SENTINEL}\\n'; }}; f"],
            cwd=self.canonical)
        home = Path(self.temporary.name) / "home"
        home.mkdir()
        missing = str(Path(self.temporary.name) / "no-platform")
        self.env = {"HOME": str(home), "PATH": tool_path(), "LANG": "C", "LC_ALL": "C",
                    "AISOFT_SESSION_ID": SESSION, "AISOFT_ACCESS_MANIFEST": missing + "/a.json",
                    "AISOFT_GOVERNANCE_MANIFEST": missing + "/g.json",
                    "AGENT_ENV_FILE": missing + "/agent.env"}

    def sandbox(self) -> list[str]:
        """Deny reads of the platform checkout and of every site install path."""
        if shutil.which("sandbox-exec") is None:
            return []
        profile = Path(self.temporary.name) / "deny.sb"
        denied = [os.path.realpath(ROOT), "/usr/local/libexec/aisoft", "/usr/local/share/aisoft",
                  "/usr/local/lib/aisoft-host-access", "/usr/local/etc/aisoft"]
        profile.write_text("(version 1)\n(allow default)\n"
                           + "".join(f'(deny file-read* (subpath "{path}"))\n' for path in denied))
        return ["sandbox-exec", "-f", str(profile)]

    def run_kit(self, entry: str, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run([*self.sandbox(), str(self.linked / ".aisoft/bin" / entry), *argv],
                                cwd=self.linked,
                                env=self.env, text=True, capture_output=True, check=False)
        if check and result.returncode != 0:
            self.fail(f"{entry} {argv} exited {result.returncode}\n{result.stdout}\n{result.stderr}")
        self.assertNotIn(SENTINEL, result.stdout + result.stderr)
        self.assertNotIn("/usr/local", result.stdout + result.stderr)
        return result

    def labels(self) -> set[str]:
        return {label["name"] for label in self.gitea.issues[7]["labels"]}

    def test_whole_flow_without_any_platform_record(self) -> None:
        self.build()
        # 1. labels
        self.run_kit("aisoft", "labels-provision")
        # 2. create and read back an Issue through the project entry
        created = json.loads(self.run_kit(
            "aisoft-access", "--operation", "gitea.issue.create", "--title", "demo change",
            "--body", "AC-1 works", "--entry-label", "needs-analysis").stdout)
        self.assertEqual(created["number"], 1)
        self.gitea.issues[7] = {**self.gitea.issues.pop(1), "number": 7,
                                "html_url": self.issue_url}
        read = json.loads(self.run_kit("aisoft-access", "--operation", "gitea.issue.read",
                                       "--number", "7").stdout)
        self.assertEqual(read["html_url"], self.issue_url)
        # 4. classification projection (before approval, as the flow orders it)
        self.run_kit("aisoft", "classify", "--apply", "7")
        verified = self.run_kit("aisoft", "classify", "--verify", "7").stdout
        self.assertIn('"result":"projected"', verified.replace(" ", ""))
        self.run_kit("aisoft-access", "--operation", "gitea.issue.labels.set", "--number", "7",
                     "--lifecycle", "approved")
        # 3. prepare-ticket reads the approved Issue through the project entry; the
        # change base is persisted first, the way an executing session records it.
        summary = self.linked / "docs/changes/7-demo-change" / self.names["summary"]
        base = git(["merge-base", "main", "HEAD"], cwd=self.linked)
        summary.write_text(summary.read_text() + "\n```aisoft-execution\n"
                           + json.dumps({"change_base": base}) + "\n```\n")
        git(["commit", "-q", "-am", "#7 T01: record change base"], cwd=self.linked)
        prepared = json.loads(self.run_kit("aisoft", "prepare-ticket", "7", "T01",
                                           "--provider", "claude").stdout)
        self.assertEqual(prepared["identity"]["issue"], 7)
        # 5. one ticket commit, then review-candidate on that fixed head
        (self.linked / "change.txt").write_text("change 7, ticket T01\n")
        git(["commit", "-q", "-am", "#7 T01: demo ticket"], cwd=self.linked)
        head = git(["rev-parse", "HEAD"], cwd=self.linked)
        reviewed = self.run_kit("aisoft", "review-candidate", "7", "T01", "--head", head)
        self.assertIn(head, reviewed.stdout)
        # 6. open-pr: first push, create, backfill, second push
        body = Path(self.temporary.name) / "body.md"
        body.write_text(f"Closes #7\n\nSummary: docs/changes/7-demo-change/{self.names['summary']}\n")
        self.run_kit("aisoft", "open-pr", "7", "--title", "demo", "--body-file", str(body))
        pull = next(iter(self.gitea.pulls.values()))
        self.assertEqual(git(["rev-parse", BRANCH], cwd=self.remote), git(["rev-parse", "HEAD"], cwd=self.linked))
        # 7. PR head and commit status, both for the final published head: the
        # backfill commit moved HEAD past the reviewed candidate.
        final = git(["rev-parse", "HEAD"], cwd=self.linked)
        self.assertNotEqual(final, head)
        self.assertEqual(git(["rev-parse", BRANCH], cwd=self.remote), final)
        read_pull = json.loads(self.run_kit("aisoft-access", "--operation", "gitea.pull.read",
                                            "--number", str(pull["number"])).stdout)
        self.assertEqual(read_pull["head"]["sha"], final)
        status = json.loads(self.run_kit("aisoft-access", "--operation", "gitea.commit.status.read",
                                         "--sha", final).stdout)
        self.assertEqual((status["sha"], status["state"]), (final, "success"))
        stale = self.run_kit("aisoft-access", "--operation", "gitea.commit.status.read", "--sha", head,
                             check=False)
        self.assertEqual(json.loads(stale.stderr)["code"], "HTTP_404")
        # 8. merged: completed is written once and the rerun is a no-op
        pull.update(state="closed", merged=True)
        self.run_kit("aisoft", "complete", "--apply", "7")
        self.assertIn("completed", self.labels())
        again = self.run_kit("aisoft", "complete", "--apply", "7")
        self.assertIn("completed", self.labels())
        self.assertIn('"result":"no-op"', again.stdout.replace(" ", ""))
        self.assertIn("ok", self.server.git_auth)
        self.assertNotIn("other", self.server.git_auth)

    def test_complete_waits_for_deployment_when_every_merge_deploys(self) -> None:
        self.build(lifecycle="application-deploy", verification=True)
        self.run_kit("aisoft", "labels-provision")
        self.gitea.add_issue(7, "demo change", labels=("pr-open",))
        result = self.run_kit("aisoft", "complete", "--apply", "7")
        self.assertIn("requires-deployment", result.stdout)
        self.assertNotIn("completed", self.labels())

    def test_development_route_is_read_from_the_declaration(self) -> None:
        self.build()
        write_declaration(self.linked, change_control="development")
        refused = self.run_kit("aisoft", "resolve-route", "7", "--provider", "claude", check=False)
        self.assertIn("route contradicts provider/policy", refused.stderr)

    def test_development_project_prepares_the_synthetic_ticket(self) -> None:
        """AC-3 step 9: a declared development project reaches complex-development."""
        self.build(change_control="development")
        self.run_kit("aisoft", "labels-provision")
        self.gitea.add_issue(7, "demo change", labels=("approved",))
        self.gitea.issues[7]["body"] = "## Acceptance criteria\n\n- [ ] AC-1 the demo works\n"
        route = json.loads(self.run_kit("aisoft", "resolve-route", "7", "--provider", "claude").stdout)
        self.assertEqual(route["route"]["process"], "complex-development")
        self.assertEqual(route["differences"], {})
        prepared = json.loads(self.run_kit("aisoft", "prepare-ticket", "7", "T01",
                                           "--provider", "claude").stdout)
        self.assertEqual(prepared["route"]["process"], "complex-development")
        self.assertEqual(prepared["identity"]["plan_path"], "issue:" + self.issue_url)


if __name__ == "__main__":
    unittest.main()
