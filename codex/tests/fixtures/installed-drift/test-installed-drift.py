"""Exercise the public CLI against copies made by the eight real installers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(sys.argv.pop(1)).resolve()
CHECKER = REPO / "codex/tools/check-installed-drift.sh"
INSTALLERS = (
    "install-vm", "install-skills", "install-host-role", "install-host-access-broker",
    "architecture/install", "docker-release/install", "sync/install", "skill-for-claude/install",
)


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def fingerprint(root):
    result = {}
    for p in sorted(root.rglob("*")):
        name = str(p.relative_to(root))
        st = p.lstat()
        result[name] = (st.st_mode, st.st_mtime_ns,
                        os.readlink(p) if p.is_symlink() else
                        (hashlib.sha256(p.read_bytes()).hexdigest() if st.st_mode & 0o444 else "UNREADABLE")
                        if p.is_file() else None)
    return result


class InstalledDriftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CHECKER.is_file():
            raise AssertionError("public installed-drift CLI has not been implemented")
        cls.temp = tempfile.TemporaryDirectory(prefix="aisoft-installed-drift-")
        cls.base = Path(cls.temp.name).resolve() / "base"
        home = cls.base / "home"
        system = cls.base / "system"
        agent = cls.base / "custom-agent"
        arch = cls.base / "custom-architecture"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                   AISOFT_HOST_ACCESS_INSTALL_ROOT=str(system),
                   AISOFT_HOST_ROLE_INSTALL_ROOT=str(system),
                   AISOFT_DOCKER_RELEASE_INSTALL_ROOT=str(system),
                   AISOFT_SYNC_INSTALL_ROOT=str(system))
        commands = [
            ["bash", "codex/install-vm.sh", str(home), str(agent)],
            ["bash", "codex/install-skills.sh", str(home)],
            ["bash", "codex/install-host-role.sh"],
            ["bash", "codex/install-host-access-broker.sh"],
            ["bash", "architecture/install.sh", "--prefix", str(arch)],
            ["bash", "docker-release/install.sh"],
            ["bash", "sync/install.sh"],
            ["bash", "skill-for-claude/install.sh", str(home)],
        ]
        for args in commands:
            p = run(args, cwd=REPO, env=env)
            if p.returncode:
                raise AssertionError(f"fixture installer failed: {args}: {p.stderr}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.temp.name, prefix="case-")).resolve()
        shutil.copytree(self.base, self.work / "installed", symlinks=True)
        self.installed = self.work / "installed"
        self.home = self.installed / "home"
        self.system = self.installed / "system"
        self.arch = self.installed / "custom-architecture"
        self.agent = self.installed / "custom-agent"

    def tearDown(self):
        shutil.rmtree(self.work)

    def args(self, repo=REPO):
        return ["bash", str(CHECKER), "--repo", str(repo),
                "--target-home", str(self.home), "--install-root", str(self.system),
                "--agent-dir", str(self.agent), "--architecture-prefix", str(self.arch), "--json"]

    def check(self, code=0, extra=(), repo=REPO):
        before = fingerprint(self.installed)
        p = run(self.args(repo) + list(extra))
        self.assertEqual(p.returncode, code, p.stderr + p.stdout)
        self.assertEqual(fingerprint(self.installed), before, "checker mutated the installation surface")
        return json.loads(p.stdout)

    def row(self, report, name):
        return next(row for row in report["installers"] if row["installer"] == name)

    def clone_source(self):
        source = self.work / "source"
        source.mkdir()
        # Only repository data; no Git metadata, user home, credentials or live files.
        for directory in ["codex", "architecture", "docker-release", "sync", "skill-for-codex", "skill-for-claude", "templates"]:
            shutil.copytree(REPO / directory, source / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return source

    def test_all_eight_real_installer_fixtures_pass(self):
        report = self.check()
        self.assertEqual(tuple(r["installer"] for r in report["installers"]), INSTALLERS)
        self.assertTrue(all(r["result"] == "PASS" for r in report["installers"]))
        self.assertEqual(self.row(report, "install-vm")["also_checked_by"], ["install-skills"])
        self.assertEqual(report["source"]["remote_freshness"], "EXTERNAL_EVIDENCE_REQUIRED")

    def test_missing_new_module_equal_count_and_restore(self):
        for installer, directory in [
            ("install-vm", self.home / ".local/lib/aisoft-loop"),
            ("install-host-access-broker", self.system / "usr/local/lib/aisoft-host-access"),
        ]:
            p = directory / "aisoft_worktree_owner.py"
            renamed = p.with_name("old_other_module.py")
            p.rename(renamed)
            report = self.check(1)
            row = self.row(report, installer)
            self.assertEqual(row["result"], "GAP")
            self.assertTrue(any(e["target"] == str(p) and e["reason"] == "missing" for e in row["gaps"]))
            renamed.rename(p)
            self.check()

    def test_equal_operations_do_not_hide_old_bytes(self):
        p = self.system / "usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py"
        original = p.read_bytes()
        p.write_bytes(b"#" + original[1:])
        report = self.check(1)
        row = self.row(report, "install-host-access-broker")
        self.assertEqual(row["quantities"]["operations"]["expected"], row["quantities"]["operations"]["installed"])
        self.assertTrue(any(e["reason"] == "bytes-differ" and e["target"] == str(p) for e in row["gaps"]))
        p.write_bytes(original)
        self.check()

    def test_each_installer_reports_missing_target_and_restoration(self):
        targets = {
            "install-vm": self.home / ".local/lib/aisoft-loop/aisoft_loop/worktree.py",
            "install-skills": self.home / ".agents/skills/issue-session-flow/SKILL.md",
            "install-host-role": self.system / "usr/local/libexec/aisoft/verify-host-role",
            "install-host-access-broker": self.system / "usr/local/libexec/aisoft/host-access-broker",
            "architecture/install": self.arch / "share/aisoft-architecture/catalog.json",
            "docker-release/install": self.system / "opt/aisoft-docker-release/docker-release-v1/compatibility/image-stores-v1.json",
            "sync/install": self.system / "etc/systemd/system/aisoft-inbound-sync@.timer",
            "skill-for-claude/install": self.home / ".claude/skills/aisoft-platform/references/onboarding-runbook.md",
        }
        for name, p in targets.items():
            with self.subTest(installer=name):
                old = p.read_bytes()
                p.unlink()
                row = self.row(self.check(1), name)
                self.assertEqual(row["result"], "GAP")
                self.assertTrue(any(g["target"] == str(p) for g in row["gaps"]))
                p.write_bytes(old)
                self.check()

    def test_changed_quantities_and_invalid_json(self):
        p = self.system / "usr/local/share/aisoft/host-capabilities.json"
        original = p.read_bytes()
        doc = json.loads(original)
        doc["capabilities"].pop(next(iter(doc["capabilities"])))
        p.write_text(json.dumps(doc))
        q = self.row(self.check(1), "install-host-role")["quantities"]["capabilities"]
        self.assertNotEqual(q["expected"], q["installed"])
        p.write_text("invalid JSON with private placeholder SHOULD_NOT_PRINT")
        report = self.check(1)
        self.assertNotIn("SHOULD_NOT_PRINT", json.dumps(report))
        p.write_bytes(original)
        self.check()

    def test_catalog_matrix_revisions_and_schema_count(self):
        for name, path, key, label in [
            ("architecture/install", self.arch / "share/aisoft-architecture/catalog.json", "revision", "catalog revision"),
            ("docker-release/install", self.system / "opt/aisoft-docker-release/docker-release-v1/compatibility/image-stores-v1.json", "matrix_revision", "matrix revision"),
        ]:
            old = path.read_bytes()
            doc = json.loads(old)
            doc[key] = "old-revision"
            path.write_text(json.dumps(doc))
            q = self.row(self.check(1), name)["quantities"][label]
            self.assertNotEqual(q["expected"], q["installed"])
            path.write_bytes(old)
            self.check()
        path = next((self.system / "opt/aisoft-docker-release/docker-release-v1/schema").glob("*.json"))
        old = path.read_bytes()
        path.unlink()
        q = self.row(self.check(1), "docker-release/install")["quantities"]["schemas"]
        self.assertEqual(q["installed"], q["expected"] - 1)
        path.write_bytes(old)
        self.check()

    def test_missing_all_components_is_gap_not_skip(self):
        shutil.rmtree(self.installed)
        self.installed.mkdir()
        report = self.check(1)
        self.assertTrue(all(r["result"] == "GAP" for r in report["installers"]))

    def test_symlink_and_fifo_are_not_read(self):
        p = self.system / "usr/local/libexec/aisoft/verify-host-role"
        original = p.read_bytes()
        p.unlink()
        secret = self.work / "auth.json"
        secret.write_text("DO_NOT_READ_SECRET")
        p.symlink_to(secret)
        report = self.check(1)
        self.assertNotIn("DO_NOT_READ_SECRET", json.dumps(report))
        self.assertTrue(any(g["reason"] == "symlink" for g in self.row(report, "install-host-role")["gaps"]))
        p.unlink()
        os.mkfifo(p)
        # fingerprint must not open FIFOs, nor should the checker.
        out = run(self.args(), timeout=20)
        self.assertEqual(out.returncode, 1)
        self.assertIn("not-regular", out.stdout)
        p.unlink()
        p.write_bytes(original)
        self.check()

    def test_symlink_parent_is_gap_without_following(self):
        directory = self.home / ".local/lib/aisoft-loop/aisoft_loop"
        moved = self.work / "protected-modules"
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        report = self.check(1)
        self.assertTrue(any(g["reason"] == "symlink-parent" for g in self.row(report, "install-vm")["gaps"]))

    def test_zero_permission_is_gap(self):
        p = self.system / "usr/local/libexec/aisoft/verify-host-role"
        p.chmod(0)
        try:
            report = self.check(1)
            self.assertTrue(any(g["reason"] == "unreadable" for g in self.row(report, "install-host-role")["gaps"]))
        finally:
            p.chmod(0o755)

    def test_matt_current_and_skill_links_are_verified(self):
        current = self.home / ".agents/vendor/mattpocock/current"
        current.unlink()
        current.symlink_to("releases/old")
        row = self.row(self.check(1), "install-skills")
        self.assertTrue(any(g["reason"] == "link-target-differ" for g in row["gaps"]))
        current.unlink()
        current.symlink_to("releases/v1.2.2")
        link = self.home / ".agents/skills/triage"
        link.unlink()
        link.symlink_to("../vendor/mattpocock/current/skills/engineering/implement")
        self.assertEqual(self.row(self.check(1), "install-skills")["result"], "GAP")

    def test_exact_tree_extra_and_non_managed_boundaries(self):
        extra = self.home / ".claude/skills/issue-session-flow/unexpected.md"
        extra.write_text("unexpected")
        row = self.row(self.check(1), "skill-for-claude/install")
        self.assertTrue(any(g["reason"] == "unexpected-entry" and g["target"] == str(extra) for g in row["gaps"]))
        extra.unlink()
        for p in [self.home / ".codex/auth.json", self.home / ".config/aisoft/projects/private.env",
                  self.home / ".agents/skills/unrelated/SKILL.md",
                  self.system / "usr/local/lib/aisoft-host-access/aisoft_worktree_owner.py.previous"]:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("NEVER_PRINT_PRIVATE_FILE")
        self.check()

    def test_source_only_never_reads_target_home(self):
        shutil.rmtree(self.installed)
        self.installed.mkdir()
        report = self.check(extra=["--source-only"])
        self.assertEqual(report["mode"], "source-only")
        self.assertTrue(all(r["scope"] == "SOURCE" for r in report["installers"]))
        self.assertNotIn("INSTALLED", json.dumps(report))

    def test_default_agent_symlink_root_is_gap(self):
        (self.home / "agent").symlink_to(self.agent, target_is_directory=True)
        args = self.args()
        offset = args.index("--agent-dir")
        del args[offset:offset + 2]
        p = run(args)
        self.assertEqual(p.returncode, 1, p.stderr)
        row = self.row(json.loads(p.stdout), "install-vm")
        self.assertTrue(any(g["reason"] == "symlink-root" for g in row["gaps"]))

    def test_parent_replacement_cannot_read_private_target(self):
        # Deterministic replacement between the preliminary stat and open.
        # The checker is loaded but main is not invoked; only the read seam runs.
        script = REPO / "codex/tools/check-installed-drift.py"
        harness = r'''
import os, pathlib, runpy, sys
namespace = runpy.run_path(sys.argv[1], run_name="test_seam")
root = pathlib.Path(sys.argv[2])
target = root / "managed/file"
original = namespace["read_bytes"].__globals__["checked_stat"]
def swap(path, boundary, **kwargs):
    result = original(path, boundary, **kwargs)
    (root / "managed").rename(root / "old")
    (root / "managed").symlink_to(root / "private", target_is_directory=True)
    return result
namespace["read_bytes"].__globals__["checked_stat"] = swap
try:
    namespace["read_bytes"](target, root)
except namespace["InspectionError"]:
    raise SystemExit(0)
raise SystemExit("unexpected read through replaced parent")
'''
        root = self.work / "race"
        for name in ("managed", "private"):
            (root / name).mkdir(parents=True)
            (root / name / "file").write_text("PRIVATE_SENTINEL" if name == "private" else "public")
        p = run([sys.executable, "-B", "-c", harness, str(script), str(root)])
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertNotIn("PRIVATE_SENTINEL", p.stdout + p.stderr)

    def test_matt_source_content_and_manifest_integrity(self):
        source = self.clone_source()
        snapshot = source / "codex/vendor/mattpocock/v1.2.2"
        manifest = snapshot / "manifest.json"
        original = manifest.read_bytes()
        for field in ("license_sha256", "sha256", "control_sha256"):
            doc = json.loads(original)
            (doc if field == "license_sha256" else doc["skills"][0])[field] = "0" * 64
            manifest.write_text(json.dumps(doc))
            self.assertIn("matt-manifest-contract-differ", json.dumps(self.check(2, repo=source)))
        manifest.write_bytes(original)
        license_file = snapshot / "LICENSE"
        license_file.write_text("changed license")
        self.assertIn("matt-license-hash-differ", json.dumps(self.check(2, repo=source)))
        shutil.copyfile(REPO / "codex/vendor/mattpocock/v1.2.2/LICENSE", license_file)
        skill = snapshot / json.loads(original)["skills"][0]["path"]
        skill.write_text(skill.read_text() + "\nchanged source\n")
        self.assertIn("matt-skill-hash-differ", json.dumps(self.check(2, repo=source)))

    def test_installer_changes_and_new_installer_fail_source_validation(self):
        source = self.clone_source()
        p = source / "codex/install-vm.sh"
        p.write_text(p.read_text() + '\ninstall -m 644 new.py "$RUNTIME_DIR/new.py"\n')
        self.assertIn("installer-mapping-stale", json.dumps(self.check(2, repo=source)))
        shutil.copyfile(REPO / "codex/install-vm.sh", p)
        other = source / "codex/new-component/install.sh"
        other.parent.mkdir(parents=True)
        other.write_text('aisoft_install_source_guard new-component "$ROOT" operations 1\n')
        self.assertIn("installer-set-mismatch", json.dumps(self.check(2, repo=source)))

    def test_retired_broker_target_is_gap_without_reading(self):
        path = self.system / "usr/local/libexec/aisoft/keychain-acl-audit.previous"
        path.write_text("retired")
        row = self.row(self.check(1), "install-host-access-broker")
        self.assertTrue(any(g["reason"] == "retired-target-present" and g["target"] == str(path) for g in row["gaps"]))

    def test_untracked_new_source_module_not_cached_main(self):
        source = self.clone_source()
        for args in [["git", "init", "-q", str(source)],
                     ["git", "-C", str(source), "add", "."],
                     ["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                      "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture baseline"],
                     ["git", "-C", str(source), "update-ref", "refs/remotes/origin/main", "HEAD"]]:
            p = run(args)
            self.assertEqual(p.returncode, 0, p.stderr)
        (source / "codex/runtime/aisoft_loop/uninstalled_new_module.py").write_text("# new module\n")
        report = self.check(1, repo=source)
        self.assertEqual(report["source"]["managed_source_matches_cached_main"], False)
        self.assertEqual(self.row(report, "install-vm")["result"], "GAP")
        (source / "codex/runtime/aisoft_loop/uninstalled_new_module.py").unlink()
        (source / "codex/runtime/aisoft_loop/worktree.py").unlink()
        report = self.check(0, repo=source, extra=["--source-only"])
        self.assertFalse(report["source"]["managed_source_matches_cached_main"])
        shutil.copyfile(REPO / "codex/runtime/aisoft_loop/worktree.py", source / "codex/runtime/aisoft_loop/worktree.py")
        shutil.rmtree(source / "codex/skills/issue-session-flow")
        report = self.check(0, repo=source, extra=["--source-only"])
        self.assertFalse(report["source"]["managed_source_matches_cached_main"])

    def test_valid_pr_source_changes_pass_source_only_but_report_main_gap(self):
        source = self.clone_source()
        for args in [["git", "init", "-q", str(source)], ["git", "-C", str(source), "add", "."],
                     ["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                      "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture baseline"],
                     ["git", "-C", str(source), "update-ref", "refs/remotes/origin/main", "HEAD"]]:
            p = run(args)
            self.assertEqual(p.returncode, 0, p.stderr)
        module = source / "codex/runtime/aisoft_loop/worktree.py"
        module.write_text(module.read_text() + "\n# valid pending PR change\n")
        report = self.check(0, repo=source, extra=["--source-only"])
        self.assertEqual(report["result"], "PASS")
        self.assertEqual(report["source"]["result"], "GAP")
        self.assertFalse(report["source"]["managed_source_matches_cached_main"])
        self.assertEqual(report["source"]["remote_freshness"], "EXTERNAL_EVIDENCE_REQUIRED")
        self.assertTrue(all(r["scope"] == "SOURCE" for r in report["installers"]))
        self.check(1, repo=source)

    def test_git_clean_filter_and_environment_cannot_run_or_redirect(self):
        source = self.clone_source()
        commands = [["git", "init", "-q", str(source)], ["git", "-C", str(source), "add", "."],
                    ["git", "-C", str(source), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                     "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture"],
                    ["git", "-C", str(source), "update-ref", "refs/remotes/origin/main", "HEAD"]]
        for args in commands:
            p = run(args)
            self.assertEqual(p.returncode, 0, p.stderr)
        marker = self.work / "FILTER_MUST_NOT_RUN"
        filter_script = self.work / "filter.sh"
        filter_script.write_text('touch "$1"\ncat\n')
        p = run(["git", "-C", str(source), "config", "filter.sentinel.clean", f'bash "{filter_script}" "{marker}"'])
        self.assertEqual(p.returncode, 0, p.stderr)
        (source / ".gitattributes").write_text("*.py filter=sentinel\n")
        env = dict(os.environ, GIT_DIR="/nonexistent-fixture-git", GIT_WORK_TREE="/nonexistent-fixture-tree")
        p = run(self.args(source) + ["--source-only"], env=env)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertTrue(json.loads(p.stdout)["source"]["managed_source_matches_cached_main"])
        self.assertFalse(marker.exists(), "checker executed Git clean filter")

    def test_relative_options_are_rejected(self):
        p = run(["bash", str(CHECKER), "--repo", ".", "--json"])
        self.assertEqual(p.returncode, 2)
        self.assertIn("absolute", p.stderr + p.stdout)

    def test_checker_audit_blocks_writes_and_non_readonly_subprocesses(self):
        # Installed surface and Python source remain unchanged under a write-denying audit hook.
        script = REPO / "codex/tools/check-installed-drift.py"
        audit = r'''
import argparse, dataclasses, fnmatch, hashlib, json, os, pathlib, re, runpy, stat, subprocess, sys
script = sys.argv.pop(1)
def guard(event, args):
    if event == "open":
        mode, flags = args[1:3]
        if isinstance(mode, str) and any(c in mode for c in "wax+"):
            raise RuntimeError("WRITE_BLOCKED")
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise RuntimeError("WRITE_BLOCKED")
    if event in {"os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.chmod", "os.symlink", "os.link", "socket.connect"}:
        raise RuntimeError("MUTATION_BLOCKED: " + event)
    if event == "subprocess.Popen":
        command = args[1]
        if command[0] != "git" or any(x in command for x in ["fetch", "push", "checkout", "commit", "status", "config", "sudo"]):
            raise RuntimeError("SUBPROCESS_BLOCKED")
sys.addaudithook(guard)
sys.argv[0] = script
runpy.run_path(script, run_name="__main__")
'''
        args = self.args()[2:]
        # Remove wrapper path, preserve the public Python CLI's same options.
        before = fingerprint(self.installed)
        p = run([sys.executable, "-B", "-c", audit, str(script)] + args)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertEqual(fingerprint(self.installed), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
