"""#327: real Git objects and transport, without authority/installed claims."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from aisoft_main_integration import (
    GitError, GitRepository, PushGuard, git_environment, ordinary_push, validate_pre_push,
)


BRANCH = "change/327-broker-ff-integration"


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.remote = self.root / "remote.git"
        self.git("init", "-q", "--bare", str(self.remote), cwd=self.root)
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.root)
        self.git("config", "user.name", "fixture")
        self.git("config", "user.email", "fixture@localhost")
        self.base = self.commit("base.txt", "base\n")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", BRANCH)
        self.first = self.commit("issue.txt", "one\n")
        self.repository = GitRepository(self.repo)

    def git(self, *args, cwd=None, allowed=(0,)):
        env = dict(os.environ)
        for key in list(env):
            if key.startswith(("GIT_", "AISOFT_GIT_GUARD_")):
                del env[key]
        env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
        r = subprocess.run(["/usr/bin/git", *args], cwd=cwd or self.repo,
                           env=env, capture_output=True, text=True)
        self.assertIn(r.returncode, allowed, r.stderr)
        return r.stdout.strip()

    def commit(self, name, contents):
        (self.repo / name).write_text(contents)
        self.git("add", "--", name)
        self.git("commit", "-q", "-m", "#327 T02: fixture")
        return self.git("rev-parse", "HEAD")

    def remote_head(self):
        out = self.git("ls-remote", "--heads", "origin", "refs/heads/" + BRANCH)
        return out.split("\t")[0] if out else None

    def advance_main(self, name="main.txt"):
        self.git("checkout", "-q", "main")
        main = self.commit(name, "main\n")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", BRANCH)
        return main

    def history(self, main=None, original=None, remote=None, scope=("issue.txt",)):
        return self.repository.verify_history(
            head=self.git("rev-parse", "HEAD"), main=main or self.base,
            original=original, remote=remote, paths=scope,
        )

    def publish(self, previous=None, runner=None):
        head = self.git("rev-parse", "HEAD")
        return ordinary_push(self.repository, remote_name="origin", branch=BRANCH,
                             head=head, remote=previous, read_remote=self.remote_head,
                             runner=runner)

    def test_create_ff_and_truthful_transport_receipt(self):
        self.history()
        first = self.publish()
        self.assertEqual(first["observed_remote_head"], self.first)
        self.assertEqual(first["write_status"], "PUBLISHED")
        self.assertTrue(first["guard_executed"])
        next_head = self.commit("issue.txt", "two\n")
        self.history(original=self.first, remote=self.first)
        second = self.publish(self.first)
        self.assertEqual(self.remote_head(), next_head)
        self.assertEqual(second["previous_head"], self.first)
        self.assertNotIn("--force", " ".join(second["argv"]))
        self.assertIn(next_head + ":refs/heads/" + BRANCH, second["argv"])

    def test_valid_repeated_main_integrations_and_linear_repair(self):
        self.publish()
        main = self.advance_main()
        self.git("merge", "-q", "--no-ff", "-m", "#327 fixture integration", main)
        self.history(main, self.first, self.first)
        self.publish(self.first)
        previous = self.remote_head()
        main = self.advance_main("more-main.txt")
        self.git("merge", "-q", "--no-ff", "-m", "#327 fixture integration", main)
        self.commit("issue.txt", "CI repair\n")
        self.history(main, self.first, previous)
        self.publish(previous)
        self.assertEqual(self.remote_head(), self.git("rev-parse", "HEAD"))

    def test_non_ff_and_intermediate_out_of_scope_delta_are_rejected(self):
        self.publish()
        self.git("checkout", "-q", "--detach", self.base)
        self.commit("other.txt", "foreign\n")
        with self.assertRaises(GitError) as caught:
            self.history(original=self.first, remote=self.first)
        self.assertEqual(caught.exception.code, "NON_FAST_FORWARD")
        self.git("checkout", "-q", BRANCH)
        self.commit("other.txt", "foreign\n")
        self.git("rm", "-q", "other.txt")
        self.git("commit", "-q", "-m", "#327 T02: hide foreign delta")
        with self.assertRaises(GitError) as caught:
            self.history()
        self.assertEqual(caught.exception.code, "SCOPE_DENIED")
        self.assertEqual(self.remote_head(), self.first)

    def test_merge_extra_content_reversed_and_foreign_parent_are_rejected(self):
        main = self.advance_main()
        tree = self.git("rev-parse", "HEAD^{tree}")
        for parents in ((self.first, main), (main, self.first), (self.first, self.base, main)):
            args = ["commit-tree", tree]
            for parent in parents:
                args.extend(("-p", parent))
            forged = self.git(*args, "-m", "#327 T02: invalid merge")
            with self.assertRaises(GitError):
                self.repository.verify_history(head=forged, main=main, original=None,
                                               remote=None, paths=("issue.txt",))

    def test_unsupported_drivers_replace_graft_shallow_and_missing_objects_fail(self):
        for filename in ("info/grafts", "shallow"):
            path = self.repo / ".git" / filename
            path.parent.mkdir(exist_ok=True)
            path.write_text(self.base + "\n")
            with self.assertRaises(GitError):
                self.history()
            path.unlink()
        self.git("config", "merge.custom.driver", "true")
        with self.assertRaises(GitError):
            self.history()
        self.git("config", "--unset", "merge.custom.driver")
        self.git("replace", self.first, self.base)
        with self.assertRaises(GitError):
            self.history()
        self.git("replace", "-d", self.first)
        with self.assertRaises(GitError):
            self.repository.verify_history(head="a" * 40, main=self.base, original=None,
                                           remote=None, paths=("issue.txt",))

    def test_advertisement_race_refuses_even_when_new_remote_is_ancestor_of_head(self):
        self.publish()
        middle = self.commit("issue.txt", "middle\n")
        self.commit("issue.txt", "last\n")
        self.git("push", "-q", "origin", middle + ":refs/heads/" + BRANCH)
        with self.assertRaises(GitError) as caught:
            self.publish(self.first)
        self.assertEqual(caught.exception.code, "REMOTE_BRANCH_MOVED")
        self.assertFalse(caught.exception.receipt["possible_write"])
        self.assertEqual(self.remote_head(), middle)

    def test_first_ref_race_delete_recreate_and_local_head_move(self):
        self.git("push", "-q", "origin", self.base + ":refs/heads/" + BRANCH)
        with self.assertRaises(GitError):
            self.publish()
        self.assertEqual(self.remote_head(), self.base)
        self.git("push", "-q", "origin", ":refs/heads/" + BRANCH)
        with self.assertRaises(GitError):
            self.publish(self.base)
        self.assertIsNone(self.remote_head())
        with PushGuard(self.repository, BRANCH, self.first, None) as guard:
            self.commit("issue.txt", "changed after verification\n")
            r = guard.run()
            self.assertNotEqual(r.returncode, 0)
            self.assertIsNone(self.remote_head())

    def test_server_old_id_race_after_guard_is_refused(self):
        self.publish()
        head = self.commit("issue.txt", "last\n")
        # receive-pack's update hook runs after advertisement/pre-push. This
        # writes a different ref tip between those two windows using real Git.
        hook = self.remote / "hooks" / "update"
        hook.write_text("#!/bin/sh\n/usr/bin/git update-ref \"$1\" " + self.base + "\n")
        hook.chmod(0o755)
        with self.assertRaises(GitError) as caught:
            self.publish(self.first)
        self.assertTrue(caught.exception.receipt["guard_executed"])
        self.assertNotEqual(self.remote_head(), head)

    def test_unexpected_up_to_date_or_unexecuted_guard_never_reports_write_pass(self):
        self.publish()
        with self.assertRaises(GitError) as caught:
            self.publish(self.base)
        self.assertNotEqual(caught.exception.code, "PUBLISHED")
        self.assertFalse(caught.exception.receipt["possible_write"])
        self.commit("issue.txt", "two\n")
        def bypass(argv, **kwargs):
            return subprocess.CompletedProcess(argv, 0, "", "")
        with self.assertRaises(GitError) as caught:
            self.publish(self.first, runner=bypass)
        self.assertEqual(caught.exception.code, "GUARD_NOT_EXECUTED")
        self.assertEqual(self.remote_head(), self.first)

    def test_guard_pin_drift_fails_before_transport(self):
        with PushGuard(self.repository, BRANCH, self.first, None) as guard:
            guard.program.chmod(0o600)
            guard.program.write_text("raise SystemExit(0)\n")
            with self.assertRaises(GitError) as caught:
                guard.run()
            self.assertEqual(caught.exception.code, "GUARD_DRIFT")
        self.assertIsNone(self.remote_head())

    def test_crisscross_and_missing_reachable_blob_fail_closed(self):
        tree = self.git("rev-parse", self.first + "^{tree}")
        side = self.git("commit-tree", tree, "-p", self.base, "-m", "side")
        left = self.git("commit-tree", tree, "-p", self.first, "-p", side, "-m", "left")
        right = self.git("commit-tree", tree, "-p", side, "-p", self.first, "-m", "right")
        crossing = self.git("commit-tree", tree, "-p", left, "-p", right, "-m", "crossing")
        with self.assertRaises(GitError) as caught:
            self.repository.verify_history(head=crossing, main=right, original=None,
                                           remote=None, paths=("issue.txt",))
        self.assertEqual(caught.exception.code, "MERGE_BASE_DENIED")
        blob = self.git("rev-parse", self.first + ":issue.txt")
        (self.repo / ".git/objects" / blob[:2] / blob[2:]).unlink()
        with self.assertRaises(GitError):
            self.history()
        self.assertIsNone(self.remote_head())

    def test_merge_driver_in_quoted_unicode_path_is_rejected(self):
        self.git("checkout", "-q", "main")
        name = "\u4e2d\u6587/.gitattributes"
        (self.repo / "\u4e2d\u6587").mkdir()
        main = self.commit(name, "issue.txt merge=union\n")
        self.git("checkout", "-q", BRANCH)
        with self.assertRaises(GitError) as caught:
            self.repository.merge_tree(self.first, main)
        self.assertEqual(caught.exception.code, "MERGE_DRIVER_DENIED")

    def test_remote_helper_override_and_recursive_push_cannot_bypass_single_ref(self):
        self.git("config", "remote.origin.vcs", "unexpected")
        with self.assertRaises(GitError) as caught:
            self.history()
        self.assertEqual(caught.exception.code, "GIT_CONFIG_DENIED")
        self.git("config", "--unset", "remote.origin.vcs")
        self.git("config", "push.recurseSubmodules", "on-demand")
        with PushGuard(self.repository, BRANCH, self.first, None) as guard:
            config = self.repository.run("config", "--get", "push.recurseSubmodules", env=guard.env).stdout.strip()
            self.assertEqual(config, "no")
            self.assertEqual(guard.program.stat().st_mode & 0o777, 0o400)
            self.assertEqual(guard.hook.stat().st_mode & 0o777, 0o500)
        self.assertIsNone(self.remote_head())

    def test_standard_worktree_config_is_supported_and_unsafe_override_is_denied(self):
        self.git("config", "extensions.worktreeConfig", "true")
        self.history()
        self.git("config", "--worktree", "merge.custom.driver", "true")
        with self.assertRaises(GitError) as caught:
            self.history()
        self.assertEqual(caught.exception.code, "GIT_CONFIG_DENIED")

    def test_unrelated_ref_housekeeping_does_not_skip_reachable_object_checks(self):
        (self.repo / ".git/refs/.DS_Store").write_bytes(b"fixture housekeeping")
        self.history()
        blob = self.git("rev-parse", self.first + ":issue.txt")
        (self.repo / ".git/objects" / blob[:2] / blob[2:]).unlink()
        with self.assertRaises(GitError):
            self.history()

    def test_scope_uses_committed_mapped_front_matter_and_fails_closed(self):
        tail = BRANCH.split("/", 1)[1]
        directory = self.repo / "docs/changes" / tail
        directory.mkdir(parents=True)
        summary = "summary-broker-ff-integration-261006.md"
        spec = "spec-broker-ff-integration-261006.md"
        (directory / summary).write_text("---\nissue: 327\nbranch: " + BRANCH + "\nstatus: approved\ndocuments:\n  spec: " + spec + "\n---\n")
        contents = "---\nissue: 327\nbranch: " + BRANCH + "\nstatus: approved\ngit_scope:\n  - issue.txt\n---\n"
        (directory / spec).write_text(contents)
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 T02: mapped fixture")
        head = self.git("rev-parse", "HEAD")
        self.assertEqual(self.repository.scope(head, BRANCH).paths, ("issue.txt",))
        (directory / spec).write_text(contents.replace("issue.txt", "*"))
        self.assertEqual(self.repository.scope(head, BRANCH).paths, ("issue.txt",), "uncommitted scope is ignored")
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 T02: invalid wildcard")
        with self.assertRaises(GitError):
            self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)

    def mapped_scope_fixture(self):
        directory = self.repo / "docs/changes/327-broker-ff-integration"
        directory.mkdir(parents=True)
        summary = directory / "summary-broker-ff-integration-261006.md"
        spec = directory / "spec-broker-ff-integration-261006.md"
        paths = ("issue.txt", str(summary.relative_to(self.repo)), str(spec.relative_to(self.repo)))
        summary_text = ("---\nissue: 327\nbranch: " + BRANCH
                        + "\ncreated: 2026-10-06\nstatus: approved\ngitea_url: http://fixture.invalid/admin/platform/issues/327"
                        + "\npr_url: ''\nrequired_docs:\n  - summary\n  - spec\ndocuments:\n  summary: " + summary.name
                        + "\n  spec: " + spec.name + "\n---\n")
        spec_text = ("---\nissue: 327\nbranch: " + BRANCH
                     + "\ncreated: 2026-10-06\nstatus: approved\ngit_scope:\n"
                     + "".join("  - " + name + "\n" for name in paths) + "---\n")
        summary.write_text(summary_text)
        spec.write_text(spec_text)
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 approved mapped fixture")
        return summary, spec, paths, summary_text, spec_text

    def test_actual_pr_backfill_keeps_approved_spec_scope_and_publishes_ff(self):
        from aisoft_loop.documents import backfill_pr_url
        summary, _spec, paths, _summary_text, _spec_text = self.mapped_scope_fixture()
        initial = self.git("rev-parse", "HEAD")
        self.assertEqual(self.repository.scope(initial, BRANCH).paths, paths)
        self.history(scope=paths)
        self.publish()
        backfill_pr_url(self.repo, 327, "http://fixture.invalid/admin/platform/pulls/346")
        self.assertIn("status: pr-open", summary.read_text())
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 actual PR backfill")
        final = self.git("rev-parse", "HEAD")
        self.assertEqual(self.repository.scope(final, BRANCH).paths, paths)
        self.history(original=initial, remote=initial, scope=paths)
        published = self.publish(initial)
        self.assertEqual(published["previous_head"], initial)
        self.assertEqual(self.remote_head(), final)
        self.assertTrue(published["guard_executed"])

    def test_pr_lifecycle_does_not_accept_bad_binding_or_unapproved_spec(self):
        summary, spec, _paths, summary_text, spec_text = self.mapped_scope_fixture()
        opened = summary_text.replace("status: approved", "status: pr-open").replace(
            "pr_url: ''", "pr_url: http://fixture.invalid/admin/platform/pulls/346")
        cases = (
            (opened.replace("status: pr-open", "status: draft"), spec_text),
            (opened.replace("status: pr-open", "status: approved\nstatus: pr-open"), spec_text),
            (opened.replace("pr_url: http://fixture.invalid/admin/platform/pulls/346", "pr_url: ''"), spec_text),
            (opened.replace("/pulls/346", "/pulls/0"), spec_text),
            (opened.replace("/pulls/346", "/pulls/346\npr_url: http://fixture.invalid/admin/platform/pulls/347"), spec_text),
            (opened.replace("pr_url: http://fixture.invalid", "pr_url: http://other.invalid"), spec_text),
            (opened.replace("/issues/327", "/issues/328"), spec_text),
            (opened, spec_text.replace("status: approved", "status: draft")),
            (opened.replace("status: pr-open", "status: pr-open\nstatus:"), spec_text),
            (opened.replace("/pulls/346", "/pulls/346\npr_url:"), spec_text),
            (opened.replace("/issues/327", "/issues/327\ngitea_url: http://fixture.invalid/admin/platform/issues/328"), spec_text),
            (opened.replace("/issues/327", "/issues/327\ngitea_url:"), spec_text),
            (opened.replace("/issues/327", "/issues/327\ngitea_url: malformed"), spec_text),
            (opened.replace("issue: 327", "issue: 327\nissue:"), spec_text),
            (opened.replace("branch: " + BRANCH, "branch: " + BRANCH + "\nbranch:"), spec_text),
            (opened, spec_text.replace("status: approved", "status: approved\nstatus:")),
        )
        for index, (bad_summary, bad_spec) in enumerate(cases):
            with self.subTest(case=index):
                summary.write_text(bad_summary)
                spec.write_text(bad_spec)
                self.git("add", "docs")
                self.git("commit", "-q", "-m", "#327 rejected lifecycle fixture")
                with self.assertRaises(GitError) as caught:
                    self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
                self.assertEqual(caught.exception.code, "SCOPE_UNKNOWN")
                self.assertIsNone(self.remote_head())

    def test_pre_push_input_exact_one_sha_ref_and_old_id(self):
        line = (self.first + " " + self.first + " refs/heads/" + BRANCH + " " + "0" * 40 + "\n").encode()
        validate_pre_push(line, branch=BRANCH, head=self.first, remote=None)
        for data in (b"", line + line, line.replace(self.first.encode(), self.base.encode(), 1),
                     line.replace(b"refs/heads/change/327", b"refs/heads/main")):
            with self.assertRaises(GitError):
                validate_pre_push(data, branch=BRANCH, head=self.first, remote=None)

    def canonical_context(self, holder=True):
        import hashlib
        from aisoft_main_integration import TemplateScopeContext
        manifest = self.root / "canonical-manifest.json"
        if not manifest.exists():
            manifest.write_text('{"fixture":true}\n')
        return TemplateScopeContext("http://fixture.invalid/admin/platform", holder,
                                    ((manifest, hashlib.sha256(manifest.read_bytes()).hexdigest()),))

    def canonical_fixture(self, selected=None):
        summary, spec, own, _summary_text, _spec_text = self.mapped_scope_fixture()
        templates = tuple("docs/changes/_template/" + role + ".md"
                          for role in ("summary", "spec", "plan", "verification"))
        paths = own + (templates if selected is None else tuple(selected))
        spec.write_text(spec.read_text().split("git_scope:", 1)[0] + "git_scope:\n"
                        + "".join("  - " + p + "\n" for p in paths) + "---\n")
        source = Path(__file__).resolve().parents[3] / "templates/docs/changes/_template"
        for path in templates:
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / target.name).read_bytes())
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 T03: approved vendored templates")
        self.repository.template_context = self.canonical_context
        return summary, spec, paths, templates

    def test_canonical_approved_templates_allow_real_history_and_ordinary_ff(self):
        summary, _spec, paths, templates = self.canonical_fixture()
        first = self.git("rev-parse", "HEAD")
        self.assertEqual(self.repository.scope(first, BRANCH).paths, paths)
        self.history(scope=paths)
        receipt = self.publish()
        self.assertEqual(receipt["observed_remote_head"], first)
        main = self.advance_main()
        self.git("merge", "-q", "--no-ff", "-m", "#327 T03: main integration", main)
        self.commit(templates[0], "approved template repair\n")
        self.history(main, first, first, scope=paths)
        second = self.publish(first)
        self.assertEqual(second["observed_remote_head"], self.git("rev-parse", "HEAD"))
        self.assertTrue(second["guard_executed"])
        self.assertNotIn("--force", second["argv"])

    def test_canonical_paths_do_not_grant_unapproved_templates_or_another_issue(self):
        _summary, spec, paths, templates = self.canonical_fixture(selected=())
        self.assertEqual(self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH).paths, paths)
        with self.assertRaises(GitError) as caught:
            self.history(scope=paths)
        self.assertEqual(caught.exception.code, "SCOPE_DENIED")
        text = spec.read_text()
        for path in ("docs/changes/999-other-issue/spec.md", "docs/changes/_template/extra.md",
                     "docs/changes/_template/sub/spec.md", "docs/changes/_template/../spec.md",
                     "docs/changes/_template/Summary.md", "Docs/changes/_template/summary.md",
                     "docs/changes/_template/%73ummary.md", "docs/changes/_template/summary.md/"):
            with self.subTest(path=path):
                self.commit(str(spec.relative_to(self.repo)), text.replace("  - issue.txt\n", "  - " + path + "\n"))
                with self.assertRaises(GitError) as refused:
                    self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
                self.assertEqual(refused.exception.code, "SCOPE_DENIED")

    def test_canonical_approved_subset_updates_only_the_selected_baseline_template(self):
        selected = ("docs/changes/_template/summary.md",)
        _summary, _spec, paths, templates = self.canonical_fixture(selected=selected)
        baseline = self.git("rev-parse", "HEAD")
        self.commit(templates[0], "approved one-template update\n")
        scope = self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
        self.assertEqual(set(scope.paths) & set(templates), set(selected))
        self.history(baseline, scope=paths)
        self.commit(templates[1], "unapproved sibling update\n")
        with self.assertRaises(GitError) as refused:
            self.history(baseline, scope=paths)
        self.assertEqual(refused.exception.code, "SCOPE_DENIED")

    def test_canonical_holder_status_source_and_worktree_drift_fail_closed(self):
        summary, spec, _paths, _templates = self.canonical_fixture()
        head = self.git("rev-parse", "HEAD")
        self.repository.template_context = None
        with self.assertRaises(GitError):
            self.repository.scope(head, BRANCH)
        self.repository.template_context = lambda: self.canonical_context(False)
        with self.assertRaises(GitError) as refused:
            self.repository.scope(head, BRANCH)
        self.assertEqual(refused.exception.code, "SCOPE_DENIED")
        context = self.canonical_context()
        self.repository.template_context = lambda: context
        context.fingerprints[0][0].write_text("drift\n")
        with self.assertRaises(GitError) as refused:
            self.repository.scope(head, BRANCH)
        self.assertEqual(refused.exception.code, "BROKER_SURFACE_GAP")

    def test_canonical_history_rejects_deleted_executable_symlink_and_hidden_delta(self):
        _summary, _spec, paths, templates = self.canonical_fixture()
        head = self.git("rev-parse", "HEAD")
        self.assertEqual(self.repository.scope(head, BRANCH).paths, paths)
        target = self.repo / templates[0]
        original = target.read_bytes()
        for kind in ("executable", "symlink", "delete"):
            with self.subTest(kind=kind):
                if target.exists() or target.is_symlink():
                    target.unlink()
                if kind == "symlink":
                    target.symlink_to("../../../base.txt")
                elif kind == "executable":
                    target.write_bytes(original)
                    target.chmod(0o755)
                self.git("add", "docs")
                self.git("commit", "-q", "-m", "#327 T03: invalid template kind")
                if target.exists() or target.is_symlink():
                    target.unlink()
                target.write_bytes(original)
                self.git("add", "docs")
                self.git("commit", "-q", "-m", "#327 T03: restore final template")
                with self.assertRaises(GitError) as refused:
                    self.history(scope=paths)
                self.assertEqual(refused.exception.code, "SCOPE_DENIED")

    def test_canonical_history_anchor_is_exact_and_cannot_launder_other_issue(self):
        _summary, spec, paths, templates = self.canonical_fixture()
        anchor = self.git("rev-parse", "HEAD")
        text = spec.read_text()
        self.commit(str(spec.relative_to(self.repo)), text.replace("git_scope:\n",
            "git_history_head: " + anchor + "\ngit_history_paths:\n"
            + "".join("  - " + p + "\n" for p in paths) + "git_scope:\n"))
        scope = self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
        self.repository.verify_history(head=self.git("rev-parse", "HEAD"), main=self.base,
            original=None, remote=None, paths=scope.paths, history_head=scope.history_head,
            history_paths=scope.history_paths)
        legal = spec.read_text()
        for bad in (legal.replace(anchor, "f" * 40),
                    legal.replace("git_history_paths:\n", "git_history_paths:\n  - docs/changes/999-other-issue/spec.md\n")):
            self.commit(str(spec.relative_to(self.repo)), bad)
            with self.assertRaises(GitError):
                scope = self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
                self.repository.verify_history(head=self.git("rev-parse", "HEAD"), main=self.base,
                    original=None, remote=None, paths=scope.paths, history_head=scope.history_head,
                    history_paths=scope.history_paths)

    def test_canonical_parent_link_and_repository_binding_are_rejected(self):
        summary, _spec, _paths, _templates = self.canonical_fixture()
        head = self.git("rev-parse", "HEAD")
        from dataclasses import replace
        context = self.canonical_context()
        self.repository.template_context = lambda: replace(context, repository_url="http://other.invalid/admin/platform")
        with self.assertRaises(GitError) as refused:
            self.repository.scope(head, BRANCH)
        self.assertEqual(refused.exception.code, "SCOPE_UNKNOWN")
        self.repository.template_context = self.canonical_context
        parent = self.repo / "docs/changes/_template"
        parked = self.root / "parked-template"
        parent.rename(parked)
        parent.symlink_to(parked, target_is_directory=True)
        with self.assertRaises(GitError) as refused:
            self.repository.scope(head, BRANCH)
        self.assertEqual(refused.exception.code, "SCOPE_DENIED")

    def test_canonical_scope_never_uses_uncommitted_approval_or_requires_content_lock(self):
        summary, spec, paths, templates = self.canonical_fixture()
        first = self.git("rev-parse", "HEAD")
        summary.write_text(summary.read_text().replace("status: approved", "status: analyzed"))
        self.assertEqual(self.repository.scope(first, BRANCH).paths, paths)
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 T03: unapproved summary")
        with self.assertRaises(GitError) as refused:
            self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
        self.assertEqual(refused.exception.code, "SCOPE_UNKNOWN")
        summary.write_text(summary.read_text().replace("status: analyzed", "status: approved"))
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 T03: restore approval")
        self.commit(templates[0], "explicitly approved template content differs from current source\n")
        self.history(scope=paths)

    def test_canonical_identity_matches_existing_four_template_contract(self):
        from aisoft_main_integration import CANONICAL_TEMPLATE_PATHS
        manifest = Path(__file__).resolve().parents[3] / "codex/config/change-template-sync.json"
        declared = json.loads(manifest.read_text())
        self.assertEqual(CANONICAL_TEMPLATE_PATHS,
                         {"docs/changes/_template/" + name for name in declared["documents"]})

    def test_canonical_context_reuses_real_parsers_and_rejects_override_or_drift(self):
        from dataclasses import replace
        from unittest.mock import patch
        from aisoft_host_access.contract import load_access_contract
        from aisoft_main_integration import template_scope_context
        source = Path(__file__).resolve().parents[3] / "codex/config"
        selected = self.root / "selected"
        installed = self.root / "installed"
        selected.mkdir()
        installed.mkdir()
        paths = tuple(directory / name for directory in (selected, installed)
                      for name in ("host-access-broker.json", "gitea-governance.json"))
        for path in paths:
            path.write_bytes((source / path.name).read_bytes())
        with patch("aisoft_main_integration._template_manifest_paths", return_value=paths), \
             patch("aisoft_main_integration.qualified_broker_environment", return_value={}) as qualified:
            contract = load_access_contract(paths[0], paths[1])
            self.assertFalse(template_scope_context(contract, "aisoft-platform").holder)
            qualified.assert_called_once_with()
            self.assertTrue(template_scope_context(contract, "hsdb").holder)
            with self.assertRaises(GitError):
                template_scope_context(contract, "unknown-project")
            with self.assertRaises(GitError):
                template_scope_context(replace(contract, path=installed / "fake.json"), "hsdb")
            raw = json.loads(paths[1].read_text())
            next(x for x in raw["repositories"] if x["name"] == "HSDB")["vendors_change_templates"] = False
            from aisoft_gitea_governance.contract import repository_declarations_sha256
            next(x for x in raw["repositories"] if x["name"] == "NewEMaint")["routine_live_pilot"][
                "non_target_repositories_sha256"] = repository_declarations_sha256(raw["repositories"], exclude_name="NewEMaint")
            paths[1].write_text(json.dumps(raw))
            with self.assertRaises(GitError) as refused:
                template_scope_context(contract, "hsdb")
            self.assertEqual(refused.exception.code, "BROKER_SURFACE_GAP")
            paths[3].write_bytes(paths[1].read_bytes())
            fresh = load_access_contract(paths[0], paths[1])
            self.assertFalse(template_scope_context(fresh, "hsdb").holder)
            with self.assertRaises(GitError):
                template_scope_context(contract, "hsdb")
            context = template_scope_context(fresh, "hsdb")
            paths[0].write_text("{}")
            with self.assertRaises(GitError):
                context.verify()

    def test_canonical_context_rejects_old_or_mixed_runtime_before_policy_read(self):
        from unittest.mock import patch
        from aisoft_main_integration import template_scope_context
        with patch("aisoft_main_integration.qualified_broker_environment",
                   side_effect=GitError("BROKER_SURFACE_GAP", "old or mixed runtime")) as qualified, \
             patch("aisoft_main_integration._template_manifest_paths",
                   return_value=(self.root / "unavailable.json",) * 4) as paths:
            with self.assertRaisesRegex(GitError, "old or mixed runtime"):
                template_scope_context(None, "hsdb")
            qualified.assert_called_once_with()
            paths.assert_not_called()

    def test_canonical_scope_rejects_empty_duplicate_projection_and_malformed_history_anchor(self):
        _summary, spec, _paths, _templates = self.canonical_fixture()
        text = spec.read_text()
        for extra in ("git_scope:\n", "git_scope: []\n", "git_history_head: invalid\n",
                      "git_history_paths: []\n"):
            self.commit(str(spec.relative_to(self.repo)), text.replace("git_scope:\n", extra + "git_scope:\n"))
            with self.subTest(extra=extra):
                with self.assertRaises(GitError) as refused:
                    self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH)
                self.assertEqual(refused.exception.code, "SCOPE_UNKNOWN")

    def test_canonical_intermediate_integration_tree_cannot_hide_invalid_template_mode(self):
        _summary, _spec, paths, templates = self.canonical_fixture()
        baseline = self.git("rev-parse", "HEAD")
        self.git("branch", "-f", "main", baseline)
        self.commit("issue.txt", "candidate change\n")
        self.git("checkout", "-q", "main")
        (self.repo / templates[0]).chmod(0o755)
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 fixture main mode change")
        main = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", BRANCH)
        self.git("merge", "-q", "--no-ff", "-m", "#327 fixture standard main integration", main)
        (self.repo / templates[0]).chmod(0o644)
        self.git("add", "docs")
        self.git("commit", "-q", "-m", "#327 fixture restore final mode")
        self.assertEqual(self.repository.scope(self.git("rev-parse", "HEAD"), BRANCH).paths, paths)
        with self.assertRaises(GitError) as refused:
            self.history(main, scope=paths)
        self.assertEqual(refused.exception.code, "SCOPE_DENIED")



class InstalledDispatchBindingTests(unittest.TestCase):
    def test_exact_dispatch_and_ff_modules_required_before_any_invocation(self):
        from unittest.mock import patch
        import aisoft_main_integration as module
        original_path = Path
        source = original_path(module.__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temporary:
            root = original_path(temporary)
            lib = root / "lib"
            wrapper = root / "wrapper"
            wrapper.write_bytes((source.parent / "tools/host-access-broker.sh").read_bytes())
            names = ("aisoft_main_integration.py", "aisoft_worktree_owner.py", "aisoft_change_name.py",
                     "aisoft_host_access/__init__.py", "aisoft_host_access/cli.py",
                     "aisoft_host_access/broker.py", "aisoft_host_access/contract.py")
            for name in names:
                target = lib / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / name).read_bytes())
            def paths(value):
                return {"/usr/local/libexec/aisoft/host-access-broker": wrapper,
                        "/usr/local/lib/aisoft-host-access": lib}.get(str(value), original_path(value))
            with patch.object(module, "Path", side_effect=paths), \
                 patch.dict(os.environ, {"AISOFT_SESSION_ID": "fixture-session", "PYTHONPATH": "untrusted", "GIT_DIR": "untrusted"}):
                environment = module.qualified_broker_environment()
                self.assertEqual(environment["PATH"], "/usr/bin:/bin")
                self.assertEqual(environment["AISOFT_SESSION_ID"], "fixture-session")
                self.assertNotIn("PYTHONPATH", environment)
                self.assertNotIn("GIT_DIR", environment)
                (lib / "aisoft_host_access/broker.py").write_text("old lease-force implementation")
                with self.assertRaisesRegex(module.GitError, "old or mixed"):
                    module.qualified_broker_environment()
                (lib / "aisoft_host_access/broker.py").write_bytes((source / "aisoft_host_access/broker.py").read_bytes())
                (lib / "aisoft_main_integration.py").unlink()
                with self.assertRaises(module.GitError):
                    module.qualified_broker_environment()

if __name__ == "__main__":
    unittest.main()
