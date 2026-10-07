"""Real pinned releases, isolated homes and one injected activation failure."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aisoft_loop import matt_snapshot as matt

ROOT = Path(__file__).parents[3]
OLD = ROOT / "codex/vendor/mattpocock/v1.2.2"
NEW = ROOT / "codex/vendor/mattpocock/v1.3.1"


class MattInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve() / "home"
        self.vendor = self.home / ".agents/vendor/mattpocock"
        self.skills = self.home / ".agents/skills"

    def assert_release(self, version, count):
        self.assertEqual(os.readlink(self.vendor / "current"), f"releases/{version}")
        manifest = json.loads((self.vendor / "current/manifest.json").read_text())
        self.assertEqual(manifest["skill_count"], count)
        for skill in manifest["skills"]:
            target = self.skills / skill["name"] / "SKILL.md"
            self.assertTrue(target.is_file(), skill["name"])
            self.assertEqual(target.read_bytes(), (self.vendor / "current" / skill["path"]).read_bytes())
        self.assertFalse(any(p.is_symlink() and not p.exists() for p in self.skills.iterdir()))

    def cli(self, *args, code=0):
        result = subprocess.run(["bash", str(ROOT / "codex/install-skills.sh"), str(self.home), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def test_real_installer_first_install_and_idempotence(self):
        self.cli()
        self.assert_release("v1.3.1", 37)
        before = {p.name: os.readlink(p) for p in self.skills.iterdir() if p.is_symlink()}
        self.cli()
        self.assertEqual(before, {p.name: os.readlink(p) for p in self.skills.iterdir() if p.is_symlink()})
        self.assertFalse((self.vendor / "previous").exists())

    def test_real_installer_upgrade_rollback_and_preserved_other_sources(self):
        matt.install_snapshot(OLD, self.home)
        lock = self.home / ".agents/.skill-lock.json"
        lock.write_text('{"legacy": "preserve all records"}\n')
        gstack = self.skills / "gstack/retro/SKILL.md"
        gstack.parent.mkdir(parents=True)
        gstack.write_text("---\nname: retro\n---\ngstack fixture\n")
        plugin = self.home / ".claude/plugins/fixture"
        plugin.parent.mkdir(parents=True)
        plugin.write_text("independent provider")
        output = self.cli().stdout
        self.assertIn("gstack retro coexist", output)
        self.assert_release("v1.3.1", 37)
        self.assertEqual(os.readlink(self.vendor / "previous"), "releases/v1.2.2")
        self.assertFalse((self.skills / "resolving-merge-conflicts").is_symlink())
        adapter = (self.skills / "aisoft-matt-workflow/SKILL.md").read_bytes()
        self.cli("--rollback")
        self.assert_release("v1.2.2", 35)
        self.assertEqual(os.readlink(self.vendor / "previous"), "releases/v1.3.1")
        for name in ("pr", "retro", "implement-spec"):
            self.assertFalse((self.skills / name).exists())
        self.assertEqual((self.skills / "aisoft-matt-workflow/SKILL.md").read_bytes(), adapter)
        self.assertEqual(plugin.read_text(), "independent provider")
        self.assertIn("gstack fixture", gstack.read_text())
        self.assertEqual(lock.read_text(), '{"legacy": "preserve all records"}\n')

    def test_unmanaged_new_skill_refuses_before_current_or_adapter_write(self):
        matt.install_snapshot(OLD, self.home)
        target = self.skills / "retro"
        target.mkdir()
        (target / "SKILL.md").write_text("user owned")
        self.cli(code=2)
        self.assert_release("v1.2.2", 35)
        self.assertEqual((target / "SKILL.md").read_text(), "user owned")
        self.assertFalse((self.skills / "aisoft-matt-workflow").exists())
        self.assertFalse((self.vendor / "releases/v1.3.1").exists())

    def test_unrelated_symlink_is_not_adopted(self):
        matt.install_snapshot(OLD, self.home)
        (self.skills / "pr").symlink_to("/unrelated/missing-skill")
        with self.assertRaisesRegex(matt.SnapshotError, "unmanaged Matt skill"):
            matt.install_snapshot(NEW, self.home)
        self.assertEqual(os.readlink(self.skills / "pr"), "/unrelated/missing-skill")
        self.assertEqual(os.readlink(self.vendor / "current"), "releases/v1.2.2")

    def test_retired_unmanaged_directory_is_preserved_and_reported(self):
        matt.install_snapshot(OLD, self.home)
        retired = self.skills / "resolving-merge-conflicts"
        retired.unlink()
        retired.mkdir()
        (retired / "SKILL.md").write_text("standalone")
        result = matt.install_snapshot(NEW, self.home)
        self.assertIn("unmanaged retired entry preserved", "\n".join(result["warnings"]))
        self.assertEqual((retired / "SKILL.md").read_text(), "standalone")

    def test_existing_release_cannot_authorize_its_own_modified_manifest(self):
        matt.install_snapshot(OLD, self.home)
        target = self.vendor / "releases/v1.3.1"
        shutil.copytree(NEW, target)
        (target / "LICENSE").write_text("tampered")
        manifest = json.loads((target / "manifest.json").read_text())
        manifest["license_sha256"] = matt._file_hash(target / "LICENSE")
        (target / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(matt.SnapshotError, "differs from pinned source"):
            matt.install_snapshot(NEW, self.home)
        self.assert_release("v1.2.2", 35)

    def test_activation_error_restores_previous_pointer_and_all_skill_links(self):
        matt.install_snapshot(OLD, self.home)
        before = {p.name: os.readlink(p) for p in self.skills.iterdir()}
        original = matt._replace_link
        failed = False

        def replace(path, target):
            nonlocal failed
            if path == self.vendor / "current" and not failed:
                failed = True
                raise OSError("injected current rename failure")
            original(path, target)

        with patch.object(matt, "_replace_link", side_effect=replace):
            with self.assertRaisesRegex(OSError, "injected"):
                matt.install_snapshot(NEW, self.home)
        self.assert_release("v1.2.2", 35)
        self.assertEqual(before, {p.name: os.readlink(p) for p in self.skills.iterdir()})
        self.assertFalse((self.vendor / "previous").exists())

    def test_linked_parent_and_missing_previous_fail_closed(self):
        outside = self.home.parent / "outside"
        outside.mkdir()
        (self.home / ".agents").mkdir(parents=True)
        self.skills.symlink_to(outside)
        with self.assertRaisesRegex(matt.SnapshotError, "parent"):
            matt.install_snapshot(NEW, self.home)
        self.assertEqual(list(outside.iterdir()), [])
        self.skills.unlink()
        with self.assertRaisesRegex(matt.SnapshotError, "no previous"):
            matt.install_snapshot(NEW, self.home, rollback=True)


if __name__ == "__main__":
    unittest.main()
