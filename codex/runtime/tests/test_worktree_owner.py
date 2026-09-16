"""#298: single-writer ownership for change worktrees."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_worktree_owner import (
    CODE_CLAIM_INVALID,
    CODE_OWNER_MISMATCH,
    CODE_UNCLAIMED,
    MARKER_NAME,
    SESSION_ENV,
    OwnerMarker,
    WorktreeOwnerError,
    authorize_push,
    caller_session,
    claim,
    marker_path,
    read_marker,
    record_push,
    write_marker,
)
from aisoft_loop.worktree import (
    GAP_REASONS,
    WorktreeError,
    current_branch,
    head_sha,
    is_ancestor,
    list_change_worktrees,
    require_branch,
    resolve_git_dir,
    scan_change_worktrees,
)

BRANCH = "change/298-worktree-single-writer"
OWNER = "session-a"
INTRUDER = "session-b"


def _marker(**overrides: object) -> dict[str, object]:
    base = {
        "schema_version": 1,
        "issue": 298,
        "branch": BRANCH,
        "session": OWNER,
        "worktree": "/private/tmp/issue-298-worktree-single-writer",
        "created": "2026-09-16T10:00:00+08:00",
        "last_push_head": None,
        "last_push_at": None,
    }
    base.update(overrides)
    return base


class MarkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.git_dir = Path(self.directory.name)

    def _write_raw(self, payload: object) -> None:
        marker_path(self.git_dir).write_text(
            json.dumps(payload) if not isinstance(payload, str) else payload,
            encoding="utf-8",
        )

    def test_round_trip_preserves_every_field(self) -> None:
        marker = OwnerMarker(
            issue=298,
            branch=BRANCH,
            session=OWNER,
            worktree="/private/tmp/issue-298-worktree-single-writer",
            created="2026-09-16T10:00:00+08:00",
            last_push_head="a" * 40,
            last_push_at="2026-09-16T11:00:00+08:00",
        )
        write_marker(self.git_dir, marker)
        self.assertEqual(read_marker(self.git_dir), marker)

    def test_missing_marker_is_unclaimed_not_invalid(self) -> None:
        """The two must never collapse into one code: 'nobody claimed this' and
        'this claim cannot be trusted' have different fixes."""
        with self.assertRaises(WorktreeOwnerError) as caught:
            read_marker(self.git_dir)
        self.assertEqual(caught.exception.code, CODE_UNCLAIMED)
        self.assertIn("claim-worktree", str(caught.exception))

    def test_malformed_json_is_claim_invalid(self) -> None:
        self._write_raw("{not json")
        with self.assertRaises(WorktreeOwnerError) as caught:
            read_marker(self.git_dir)
        self.assertEqual(caught.exception.code, CODE_CLAIM_INVALID)

    def test_key_set_is_exact(self) -> None:
        for payload, label in (
            ({k: v for k, v in _marker().items() if k != "session"}, "missing"),
            (_marker(extra="x"), "unknown"),
        ):
            with self.subTest(label):
                self._write_raw(payload)
                with self.assertRaises(WorktreeOwnerError) as caught:
                    read_marker(self.git_dir)
                self.assertEqual(caught.exception.code, CODE_CLAIM_INVALID)

    def test_each_field_rule_is_enforced(self) -> None:
        cases = {
            "schema": _marker(schema_version=2),
            "issue-type": _marker(issue="298"),
            "issue-bool": _marker(issue=True),
            "issue-mismatch": _marker(issue=299),
            "branch-not-change": _marker(branch="main", issue=298),
            "session-empty": _marker(session=""),
            "session-control-char": _marker(session="a\nb"),
            "session-too-long": _marker(session="a" * 129),
            "worktree-relative": _marker(worktree="relative/path"),
            "created-blank": _marker(created="   "),
            "head-short": _marker(last_push_head="abc", last_push_at="now"),
            "head-uppercase": _marker(last_push_head="A" * 40, last_push_at="now"),
            "head-without-at": _marker(last_push_head="a" * 40),
            "at-without-head": _marker(last_push_at="now"),
        }
        for label, payload in cases.items():
            with self.subTest(label):
                self._write_raw(payload)
                with self.assertRaises(WorktreeOwnerError) as caught:
                    read_marker(self.git_dir)
                self.assertEqual(caught.exception.code, CODE_CLAIM_INVALID)

    def test_write_leaves_no_temporary_file_behind(self) -> None:
        write_marker(self.git_dir, OwnerMarker(
            issue=298,
            branch=BRANCH,
            session=OWNER,
            worktree="/tmp/x",
            created="now",
            last_push_head=None,
            last_push_at=None,
        ))
        self.assertEqual(
            sorted(path.name for path in self.git_dir.iterdir()), [MARKER_NAME]
        )


class ClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.git_dir = Path(self.directory.name)

    def test_first_claim_creates_and_repeat_is_a_no_op(self) -> None:
        first, first_result = claim(
            self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", now="t0"
        )
        second, second_result = claim(
            self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", now="t1"
        )
        self.assertEqual(first_result, "created")
        self.assertEqual(second_result, "no-op")
        self.assertEqual(second.created, "t0", "created must not be rewritten by a re-claim")
        self.assertEqual(first.issue, 298)

    def test_another_session_is_refused_and_changes_nothing(self) -> None:
        claim(self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", now="t0")
        before = marker_path(self.git_dir).read_text(encoding="utf-8")
        with self.assertRaises(WorktreeOwnerError) as caught:
            claim(self.git_dir, branch=BRANCH, session=INTRUDER, worktree="/tmp/wt")
        self.assertEqual(caught.exception.code, CODE_OWNER_MISMATCH)
        self.assertEqual(marker_path(self.git_dir).read_text(encoding="utf-8"), before)

    def test_takeover_is_explicit_and_carries_the_push_ledger(self) -> None:
        claim(self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", now="t0")
        record_push(self.git_dir, head="b" * 40, now="t1")
        marker, result = claim(
            self.git_dir, branch=BRANCH, session=INTRUDER, worktree="/tmp/wt", takeover=True
        )
        self.assertEqual(result, "taken-over")
        self.assertEqual(marker.session, INTRUDER)
        self.assertEqual(marker.created, "t0")
        self.assertEqual(
            marker.last_push_head, "b" * 40,
            "the push ledger is a fact about the remote, not about the owner",
        )

    def test_invalid_marker_needs_takeover_too(self) -> None:
        marker_path(self.git_dir).write_text("{}", encoding="utf-8")
        with self.assertRaises(WorktreeOwnerError) as caught:
            claim(self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt")
        self.assertEqual(caught.exception.code, CODE_CLAIM_INVALID)
        marker, result = claim(
            self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", takeover=True
        )
        self.assertEqual(result, "taken-over")
        self.assertEqual(marker.session, OWNER)

    def test_claim_rejects_a_non_change_branch_and_a_bad_session(self) -> None:
        with self.assertRaises(WorktreeOwnerError) as branch_error:
            claim(self.git_dir, branch="main", session=OWNER, worktree="/tmp/wt")
        self.assertEqual(branch_error.exception.code, CODE_CLAIM_INVALID)
        with self.assertRaises(WorktreeOwnerError) as session_error:
            claim(self.git_dir, branch=BRANCH, session="", worktree="/tmp/wt")
        self.assertEqual(session_error.exception.code, CODE_CLAIM_INVALID)


class AuthorizePushTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.git_dir = Path(self.directory.name)
        claim(self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", now="t0")

    def test_owner_is_authorized(self) -> None:
        marker = authorize_push(self.git_dir, branch=BRANCH, session=OWNER)
        self.assertEqual(marker.session, OWNER)

    def test_every_refusal_has_its_own_code_and_none_is_worktree_dirty(self) -> None:
        cases = {
            "another session": (BRANCH, INTRUDER, CODE_OWNER_MISMATCH),
            "no session id": (BRANCH, "", CODE_OWNER_MISMATCH),
            "another branch": ("change/299-other-branch", OWNER, CODE_OWNER_MISMATCH),
        }
        for label, (branch, session, expected) in cases.items():
            with self.subTest(label):
                with self.assertRaises(WorktreeOwnerError) as caught:
                    authorize_push(self.git_dir, branch=branch, session=session)
                self.assertEqual(caught.exception.code, expected)
                self.assertNotIn("WORKTREE_DIRTY", caught.exception.code)

    def test_messages_separate_a_forgotten_id_from_a_foreign_session(self) -> None:
        """Same code, different operator mistake — the message is what tells
        them apart, so it must actually differ."""
        with self.assertRaises(WorktreeOwnerError) as forgotten:
            authorize_push(self.git_dir, branch=BRANCH, session="")
        with self.assertRaises(WorktreeOwnerError) as foreign:
            authorize_push(self.git_dir, branch=BRANCH, session=INTRUDER)
        self.assertIn(SESSION_ENV, str(forgotten.exception))
        self.assertIn(INTRUDER, str(foreign.exception))
        self.assertNotEqual(str(forgotten.exception), str(foreign.exception))

    def test_unclaimed_worktree_is_refused_before_anything_else(self) -> None:
        marker_path(self.git_dir).unlink()
        with self.assertRaises(WorktreeOwnerError) as caught:
            authorize_push(self.git_dir, branch=BRANCH, session=OWNER)
        self.assertEqual(caught.exception.code, CODE_UNCLAIMED)


class RecordPushTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.git_dir = Path(self.directory.name)
        claim(self.git_dir, branch=BRANCH, session=OWNER, worktree="/tmp/wt", now="t0")

    def test_records_head_and_time_together(self) -> None:
        marker = record_push(self.git_dir, head="c" * 40, now="t9")
        self.assertEqual(marker.last_push_head, "c" * 40)
        self.assertEqual(marker.last_push_at, "t9")
        self.assertEqual(read_marker(self.git_dir), marker)

    def test_rejects_anything_that_is_not_a_full_lowercase_sha(self) -> None:
        for head in ("", "abc", "C" * 40, "g" * 40, "a" * 41):
            with self.subTest(head=head):
                with self.assertRaises(WorktreeOwnerError) as caught:
                    record_push(self.git_dir, head=head)
                self.assertEqual(caught.exception.code, CODE_CLAIM_INVALID)

    def test_keeps_the_owner_untouched(self) -> None:
        marker = record_push(self.git_dir, head="d" * 40, now="t9")
        self.assertEqual(marker.session, OWNER)
        self.assertEqual(marker.created, "t0")


class CallerSessionTests(unittest.TestCase):
    def test_reads_and_trims_the_environment_variable(self) -> None:
        self.assertEqual(caller_session({SESSION_ENV: "  abc  "}), "abc")

    def test_absent_or_blank_is_an_empty_string(self) -> None:
        self.assertEqual(caller_session({}), "")
        self.assertEqual(caller_session({SESSION_ENV: "   "}), "")

    def test_defaults_to_the_process_environment(self) -> None:
        original = os.environ.get(SESSION_ENV)
        os.environ[SESSION_ENV] = "from-process"
        try:
            self.assertEqual(caller_session(), "from-process")
        finally:
            if original is None:
                del os.environ[SESSION_ENV]
            else:
                os.environ[SESSION_ENV] = original


class LinkedWorktreeTests(unittest.TestCase):
    """Real Git: the marker has to land in the *linked* worktree's own git dir,
    which is the whole reason `.git` cannot be joined by hand."""

    def _git(self, argv: list[str], cwd: Path) -> str:
        result = subprocess.run(
            ["git", *argv], cwd=str(cwd), capture_output=True, text=True, check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
        )
        return result.stdout.strip()

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.main = root / "repo"
        self.main.mkdir()
        self._git(["init", "-q", "-b", "main"], self.main)
        (self.main / "f.txt").write_text("1\n", encoding="utf-8")
        self._git(["add", "."], self.main)
        self._git(["commit", "-qm", "one"], self.main)
        self.linked = root / "issue-298-worktree-single-writer"
        self._git(["worktree", "add", "-q", str(self.linked), "-b", BRANCH], self.main)

    def test_each_worktree_gets_its_own_marker_directory(self) -> None:
        main_dir = resolve_git_dir(self.main)
        linked_dir = resolve_git_dir(self.linked)
        self.assertNotEqual(main_dir, linked_dir)
        self.assertTrue(linked_dir.is_absolute())
        self.assertEqual(linked_dir.parent.name, "worktrees")

    def test_the_marker_never_shows_up_as_a_dirty_working_tree(self) -> None:
        """If it did, `git.push.change` would report WORKTREE_DIRTY and never
        read the marker at all."""
        claim(
            resolve_git_dir(self.linked),
            branch=BRANCH,
            session=OWNER,
            worktree=self.linked,
        )
        self.assertEqual(self._git(["status", "--porcelain"], self.linked), "")

    def test_claiming_a_worktree_standing_on_another_branch_is_refused(self) -> None:
        with self.assertRaises(WorktreeOwnerError) as caught:
            require_branch(self.main, BRANCH)
        self.assertEqual(caught.exception.code, CODE_CLAIM_INVALID)
        require_branch(self.linked, BRANCH)

    def test_branch_head_and_ancestry_helpers_read_real_git(self) -> None:
        self.assertEqual(current_branch(self.linked), BRANCH)
        base = head_sha(self.linked)
        (self.linked / "g.txt").write_text("2\n", encoding="utf-8")
        self._git(["add", "."], self.linked)
        self._git(["commit", "-qm", "two"], self.linked)
        advanced = head_sha(self.linked)
        self.assertTrue(is_ancestor(self.linked, base, advanced))
        self.assertFalse(is_ancestor(self.linked, advanced, base))

    def test_an_unknown_object_is_not_reported_as_an_ancestor(self) -> None:
        self.assertFalse(is_ancestor(self.linked, "e" * 40, head_sha(self.linked)))

    def test_git_failures_surface_as_worktree_errors(self) -> None:
        with self.assertRaises(WorktreeError):
            resolve_git_dir(Path(self.directory.name) / "not-a-repo")


class ScanTests(unittest.TestCase):
    """AC-3: a read-only sweep that says which change worktrees left their last
    push, and which of those are worth stopping for."""

    def _git(self, argv: list[str], cwd: Path) -> str:
        return subprocess.run(
            ["git", *argv], cwd=str(cwd), capture_output=True, text=True, check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
        ).stdout.strip()

    def _commit(self, worktree: Path, name: str) -> str:
        (worktree / name).write_text(name, encoding="utf-8")
        self._git(["add", "."], worktree)
        self._git(["commit", "-qm", name], worktree)
        return head_sha(worktree)

    def _worktree(self, branch: str) -> Path:
        path = self.root / f"issue-{branch.split('/')[1]}"
        self._git(["worktree", "add", "-q", str(path), "-b", branch], self.canonical)
        return path

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.canonical = self.root / "repo"
        self.canonical.mkdir()
        self._git(["init", "-q", "-b", "main"], self.canonical)
        self._commit(self.canonical, "base")

    def _scan(self) -> dict[str, str]:
        return {
            entry.branch: entry.reason for entry in scan_change_worktrees(self.canonical)
        }

    def test_only_change_branches_are_scanned(self) -> None:
        self._git(["worktree", "add", "-q", str(self.root / "plain"), "-b", "feature/x"],
                  self.canonical)
        claimed = self._worktree("change/301-claimed-branch")
        claim(resolve_git_dir(claimed), branch="change/301-claimed-branch",
              session=OWNER, worktree=claimed)
        listed = list_change_worktrees(self.canonical)
        self.assertEqual([branch for _path, branch in listed], ["change/301-claimed-branch"])

    def test_every_reason_is_reported_and_only_three_are_gaps(self) -> None:
        clean = self._worktree("change/301-clean-branch")
        claim(resolve_git_dir(clean), branch="change/301-clean-branch",
              session=OWNER, worktree=clean)
        record_push(resolve_git_dir(clean), head=head_sha(clean))

        ahead = self._worktree("change/302-ahead-branch")
        claim(resolve_git_dir(ahead), branch="change/302-ahead-branch",
              session=OWNER, worktree=ahead)
        record_push(resolve_git_dir(ahead), head=head_sha(ahead))
        self._commit(ahead, "later")

        rewritten = self._worktree("change/303-rewritten-branch")
        claim(resolve_git_dir(rewritten), branch="change/303-rewritten-branch",
              session=OWNER, worktree=rewritten)
        landed = self._commit(rewritten, "landed")
        record_push(resolve_git_dir(rewritten), head=landed)
        # Somebody else rebased it: same content, a sha that no longer has the
        # pushed commit in its history.
        self._git(["commit", "-q", "--amend", "-m", "rewritten by somebody else"], rewritten)
        self.assertFalse(is_ancestor(rewritten, landed, head_sha(rewritten)))

        unpushed = self._worktree("change/304-unpushed-branch")
        claim(resolve_git_dir(unpushed), branch="change/304-unpushed-branch",
              session=OWNER, worktree=unpushed)

        self._worktree("change/305-unclaimed-branch")

        mismatched = self._worktree("change/306-mismatched-branch")
        claim(resolve_git_dir(mismatched), branch="change/307-some-other-branch",
              session=OWNER, worktree=mismatched)

        self.assertEqual(self._scan(), {
            "change/301-clean-branch": "clean",
            "change/302-ahead-branch": "ahead",
            "change/303-rewritten-branch": "rewritten",
            "change/304-unpushed-branch": "unpushed",
            "change/305-unclaimed-branch": "unclaimed",
            "change/306-mismatched-branch": "claim-invalid",
        })
        self.assertEqual(GAP_REASONS, frozenset({"rewritten", "unclaimed", "claim-invalid"}))
        gaps = {entry.branch for entry in scan_change_worktrees(self.canonical) if not entry.ok}
        self.assertEqual(gaps, {
            "change/303-rewritten-branch",
            "change/305-unclaimed-branch",
            "change/306-mismatched-branch",
        })

    def test_ahead_reports_how_far_and_stays_a_pass(self) -> None:
        """Unpushed local commits are the normal state for most of a change's
        life. If that were a GAP the command would be red throughout and nobody
        would read it."""
        ahead = self._worktree("change/302-ahead-branch")
        claim(resolve_git_dir(ahead), branch="change/302-ahead-branch",
              session=OWNER, worktree=ahead)
        record_push(resolve_git_dir(ahead), head=head_sha(ahead))
        self._commit(ahead, "one")
        self._commit(ahead, "two")
        entry = scan_change_worktrees(self.canonical)[0]
        self.assertTrue(entry.ok)
        self.assertIn("2 local commit", entry.detail)

    def test_the_scan_writes_nothing(self) -> None:
        claimed = self._worktree("change/301-clean-branch")
        git_dir = resolve_git_dir(claimed)
        claim(git_dir, branch="change/301-clean-branch", session=OWNER, worktree=claimed)
        unclaimed = self._worktree("change/305-unclaimed-branch")
        before_marker = marker_path(git_dir).read_text(encoding="utf-8")
        before_status = self._git(["status", "--porcelain"], claimed)

        scan_change_worktrees(self.canonical)

        self.assertEqual(marker_path(git_dir).read_text(encoding="utf-8"), before_marker)
        self.assertEqual(self._git(["status", "--porcelain"], claimed), before_status)
        self.assertFalse(
            marker_path(resolve_git_dir(unclaimed)).exists(),
            "a scan must never repair the thing it is reporting on",
        )

    def test_a_removed_worktree_directory_is_reported_not_raised(self) -> None:
        missing = self._worktree("change/308-missing-branch")
        claim(resolve_git_dir(missing), branch="change/308-missing-branch",
              session=OWNER, worktree=missing)
        subprocess.run(["rm", "-rf", str(missing)], check=True)
        entry = scan_change_worktrees(self.canonical)[0]
        self.assertFalse(entry.ok)
        self.assertEqual(entry.reason, "claim-invalid")


if __name__ == "__main__":
    unittest.main()
