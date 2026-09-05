"""#180: the Issue JSON that feeds the analyzer must carry the comment thread.

`get-issue` used to dump the raw Gitea Issue object, whose `comments` field is
only a count; the analyzer therefore judged Issues whose scope had been revised
in comments without knowing it was blind. The CLI now appends `issue_comments`
(the projected thread) next to the untouched count, and `render-analysis`
refuses a payload without it so the wrapper can never silently run on the old
shape again.
"""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from aisoft_loop import cli
from aisoft_loop.gitea import GiteaError
from tests.test_analysis import SMALL, result_payload


ISSUE = {
    "number": 8,
    "title": "Pilot issue",
    "state": "open",
    "comments": 2,
    "body": "## Acceptance criteria\n\n- [ ] Existing behavior is restored.",
    "labels": [{"id": 1, "name": "needs-analysis"}],
}

COMMENTS = [
    {
        "id": 11,
        "author": "reviewer",
        "created_at": "2026-09-05T10:00:00+08:00",
        "body": "范围改为新增 schema 迁移。",
    },
    {
        "id": 12,
        "author": "requester",
        "created_at": "2026-09-05T10:05:00+08:00",
        "body": "同意。",
    },
]


class FakeGitea:
    def __init__(self, issue: dict, comments: list[dict] | Exception) -> None:
        self.issue = issue
        self.comments = comments
        self.calls: list[tuple[str, int]] = []

    def get_issue(self, issue_number: int) -> dict:
        self.calls.append(("issue", issue_number))
        return dict(self.issue)

    def list_issue_comments(self, issue_number: int) -> list[dict]:
        self.calls.append(("comments", issue_number))
        if isinstance(self.comments, Exception):
            raise self.comments
        return [dict(entry) for entry in self.comments]


class GetIssuePayloadTests(unittest.TestCase):
    def test_get_issue_appends_the_thread_and_keeps_the_count(self) -> None:
        gitea = FakeGitea(ISSUE, COMMENTS)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            cli, "_gitea_from_env", return_value=gitea
        ):
            output = Path(tmp) / "issue.json"
            self.assertEqual(cli.main(["get-issue", "8", str(output)]), 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(payload["comments"], 2)
        self.assertEqual(payload["issue_comments"], COMMENTS)
        self.assertEqual(len(payload["issue_comments"]), payload["comments"])
        for key, value in ISSUE.items():
            self.assertEqual(payload[key], value)
        self.assertEqual(gitea.calls, [("issue", 8), ("comments", 8)])

    def test_get_issue_fails_instead_of_writing_a_thread_less_payload(self) -> None:
        gitea = FakeGitea(ISSUE, GiteaError("Gitea HTTP 500: unavailable"))
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            cli, "_gitea_from_env", return_value=gitea
        ), contextlib.redirect_stderr(stderr):
            output = Path(tmp) / "issue.json"
            self.assertEqual(cli.main(["get-issue", "8", str(output)]), 2)
            self.assertFalse(output.exists())
        self.assertIn("Gitea HTTP 500", stderr.getvalue())


class RenderAnalysisGuardTests(unittest.TestCase):
    def render(self, issue: dict) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            issue_path = root / "issue.json"
            result_path = root / "result.json"
            output_directory = root / "summary"
            issue_path.write_text(json.dumps(issue, ensure_ascii=False), encoding="utf-8")
            result_path.write_text(json.dumps(result_payload(SMALL)), encoding="utf-8")
            environment = {
                "GITEA_URL": "http://gitea.test:3000",
                "GITEA_OWNER": "owner",
                "GITEA_REPO": "repo",
                "AISOFT_GOVERNANCE_MANIFEST": str(root / "missing-manifest.json"),
            }
            stderr = io.StringIO()
            with mock.patch.dict(os.environ, environment), contextlib.redirect_stdout(
                io.StringIO()
            ), contextlib.redirect_stderr(stderr):
                code = cli.main(
                    [
                        "render-analysis",
                        str(issue_path),
                        str(result_path),
                        str(output_directory),
                    ]
                )
            rendered = sorted(output_directory.glob("*.md")) if output_directory.exists() else []
            content = rendered[0].read_text(encoding="utf-8") if rendered else ""
            return code, stderr.getvalue(), content

    def test_payload_without_the_thread_fails_closed(self) -> None:
        for issue in (dict(ISSUE), {**ISSUE, "issue_comments": 2}, {**ISSUE, "issue_comments": None}):
            with self.subTest(issue_comments=issue.get("issue_comments")):
                code, stderr, content = self.render(issue)
                self.assertEqual(code, 2)
                self.assertIn("issue_comments", stderr)
                self.assertEqual(content, "")

    def test_empty_and_populated_threads_render_the_same_summary(self) -> None:
        silent_code, _, silent = self.render({**ISSUE, "issue_comments": []})
        discussed_code, _, discussed = self.render({**ISSUE, "issue_comments": COMMENTS})
        self.assertEqual((silent_code, discussed_code), (0, 0))
        self.assertIn("issue: 8", silent)
        self.assertIn("branch: change/8-pilot-fix", silent)
        self.assertEqual(silent, discussed)
        self.assertNotIn("schema 迁移", discussed)


if __name__ == "__main__":
    unittest.main()
