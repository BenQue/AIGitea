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

    def test_pre_push_input_exact_one_sha_ref_and_old_id(self):
        line = (self.first + " " + self.first + " refs/heads/" + BRANCH + " " + "0" * 40 + "\n").encode()
        validate_pre_push(line, branch=BRANCH, head=self.first, remote=None)
        for data in (b"", line + line, line.replace(self.first.encode(), self.base.encode(), 1),
                     line.replace(b"refs/heads/change/327", b"refs/heads/main")):
            with self.assertRaises(GitError):
                validate_pre_push(data, branch=BRANCH, head=self.first, remote=None)



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
