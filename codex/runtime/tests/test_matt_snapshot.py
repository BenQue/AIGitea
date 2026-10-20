import json
from pathlib import Path
import shutil
import tempfile
import unittest

from aisoft_loop.matt_snapshot import (
    PACKS,
    SnapshotError,
    _skill_front_matter,
    build_manifest,
    classify_update,
    verify_snapshot,
)


ROOT = Path(__file__).parents[3]
VENDOR = ROOT / "codex" / "vendor" / "mattpocock" / "v1.3.1"
SUPERPOWERS = ROOT / "codex" / "vendor" / "superpowers" / "v7.0.0"


class MattSnapshotTests(unittest.TestCase):
    def test_vendored_release_is_complete_and_matches_manifest(self) -> None:
        manifest = json.loads((VENDOR / "manifest.json").read_text())
        verified = verify_snapshot(VENDOR, manifest)
        self.assertEqual(verified["tag"], "v1.3.1")
        self.assertEqual(verified["commit"], "24fe0ef7737efae15c87225755e9f6f5965e4888")
        self.assertEqual(verified["skill_count"], 37)
        self.assertIn("triage", verified["skill_names"])
        self.assertIn("implement", verified["skill_names"])
        self.assertEqual(manifest["tag_object"], "0b6cee10f260a2e048279cf737bfd3e37b1fce0b")

    def test_old_release_retained_and_new_manual_skills_keep_invocation_policy(self):
        previous = VENDOR.parent / "v1.2.2"
        old = verify_snapshot(previous, json.loads((previous / "manifest.json").read_text()))
        new = verify_snapshot(VENDOR, json.loads((VENDOR / "manifest.json").read_text()))
        self.assertEqual(old["commit"], "8b36d4fb2635b3c21998dcd8144439c9e5ba7302")
        self.assertEqual(set(new["skill_names"]) - set(old["skill_names"]), {"pr", "retro", "implement-spec"})
        self.assertEqual(set(old["skill_names"]) - set(new["skill_names"]), {"resolving-merge-conflicts"})
        for name in ("retro", "implement-spec", "implement"):
            self.assertEqual(_skill_front_matter(VENDOR / "skills/engineering" / name / "SKILL.md"), (name, True))

    def test_skill_add_remove_or_critical_change_requires_complex_review(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            current = self._snapshot(root / "current", {"triage": "stable", "teach": "stable"})
            candidate = self._snapshot(root / "candidate", {"triage": "changed", "new-skill": "new"})
            current_manifest = build_manifest(current, tag="v1", commit="a" * 40, tag_object="b" * 40)
            candidate_manifest = build_manifest(candidate, tag="v2", commit="c" * 40, tag_object="d" * 40)
            result = classify_update(current_manifest, candidate_manifest)
            self.assertEqual(result["classification"], "complex")
            self.assertIn("skill set changed", result["reasons"])
            self.assertIn("critical skill changed: triage", result["reasons"])

    def test_noncritical_content_only_change_is_a_maintenance_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            current = self._snapshot(root / "current", {"teach": "one"})
            candidate = self._snapshot(root / "candidate", {"teach": "two"})
            current_manifest = build_manifest(current, tag="v1", commit="a" * 40, tag_object="b" * 40)
            candidate_manifest = build_manifest(candidate, tag="v2", commit="c" * 40, tag_object="d" * 40)
            result = classify_update(current_manifest, candidate_manifest)
            self.assertEqual(result["classification"], "maintenance-candidate")

    def test_noncritical_workflow_or_git_side_effect_change_is_complex(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            current = self._snapshot(root / "current", {"teach": "# Process\n1. Explain"})
            candidate = self._snapshot(
                root / "candidate",
                {"teach": "# Process\n1. Run git push"},
            )
            current_manifest = build_manifest(
                current, tag="v1", commit="a" * 40, tag_object="b" * 40
            )
            candidate_manifest = build_manifest(
                candidate, tag="v2", commit="c" * 40, tag_object="d" * 40
            )
            result = classify_update(current_manifest, candidate_manifest)
            self.assertEqual(result["classification"], "complex")
            self.assertIn(
                "workflow or side-effect contract changed: teach",
                result["reasons"],
            )

    def test_snapshot_with_undeclared_skill_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = self._snapshot(Path(tempdir), {"teach": "one"})
            manifest = build_manifest(root, tag="v1", commit="a" * 40, tag_object="b" * 40)
            self._write_skill(root, "extra", "surprise")
            with self.assertRaisesRegex(SnapshotError, "skill set"):
                verify_snapshot(root, manifest)

    def test_a_quoted_invocation_policy_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            for policy, expected in (
                ("true", True),
                ("false", False),
                ("TRUE", True),
                ("'true'", True),
                ('"true"', True),
                ("'false'", False),
                ('"false"', False),
            ):
                with self.subTest(policy=policy):
                    skill_file = self._front_matter(Path(tempdir), "demo-skill", policy)
                    self.assertEqual(
                        _skill_front_matter(skill_file), ("demo-skill", expected)
                    )

    def test_an_invalid_invocation_policy_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            for policy in ("yes", "1", "", "''", '""', "'true", 'true"'):
                with self.subTest(policy=policy):
                    skill_file = self._front_matter(Path(tempdir), "demo-skill", policy)
                    with self.assertRaisesRegex(SnapshotError, "invalid invocation policy"):
                        _skill_front_matter(skill_file)

    def test_a_quoted_skill_name_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            for name in ("demo-skill", "'demo-skill'", '"demo-skill"'):
                with self.subTest(name=name):
                    skill_file = self._front_matter(Path(tempdir), name, "true")
                    self.assertEqual(
                        _skill_front_matter(skill_file), ("demo-skill", True)
                    )

    def test_a_malformed_quoted_skill_name_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            for name in ("'demo-skill", 'demo-skill"'):
                with self.subTest(name=name):
                    skill_file = self._front_matter(Path(tempdir), name, "true")
                    with self.assertRaisesRegex(SnapshotError, "invalid skill name"):
                        _skill_front_matter(skill_file)

    def _front_matter(self, root: Path, name: str, policy: str) -> Path:
        skill_file = root / "SKILL.md"
        skill_file.write_text(
            f"---\nname: {name}\ndisable-model-invocation: {policy}\n---\n\nbody\n",
            encoding="utf-8",
        )
        return skill_file

    def _snapshot(self, root: Path, skills: dict[str, str]) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        (root / "LICENSE").write_text("MIT\n")
        for name, body in skills.items():
            self._write_skill(root, name, body)
        return root

    def _write_skill(self, root: Path, name: str, body: str) -> None:
        directory = root / "skills" / "engineering" / name
        directory.mkdir(parents=True)
        directory.joinpath("SKILL.md").write_text(
            f"---\nname: {name}\ndisable-model-invocation: true\n---\n\n{body}\n"
        )


if __name__ == "__main__":
    unittest.main()


class SuperpowersSnapshotTests(unittest.TestCase):
    """#392: superpowers is vendored as the three-tool pin baseline."""

    def manifest(self) -> dict:
        return json.loads((SUPERPOWERS / "manifest.json").read_text())

    def test_vendored_release_matches_the_pinned_upstream_tag(self) -> None:
        manifest = self.manifest()
        verified = verify_snapshot(SUPERPOWERS, manifest, "superpowers")
        self.assertEqual(verified["tag"], "v7.0.0")
        self.assertEqual(verified["commit"], "bb92a77741419a4ab5f06e711a283343f1ada0c3")
        self.assertEqual(manifest["tag_object"], "7f043e5eaf3522dc19178c673b76328de9b0c355")
        self.assertEqual(manifest["source"], "https://github.com/obra/superpowers")
        self.assertEqual(verified["skill_count"], 15)
        self.assertLessEqual(set(PACKS["superpowers"]["critical_skills"]), set(verified["skill_names"]))

    def test_packs_are_not_interchangeable(self) -> None:
        with self.assertRaises(SnapshotError):
            verify_snapshot(SUPERPOWERS, self.manifest())
        with self.assertRaises(SnapshotError):
            verify_snapshot(VENDOR, json.loads((VENDOR / "manifest.json").read_text()), "superpowers")
        with self.assertRaises(SnapshotError):
            verify_snapshot(SUPERPOWERS, self.manifest(), "unknown")

    def test_a_missing_critical_skill_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE").write_text("MIT\n")
            (root / "skills/brainstorming").mkdir(parents=True)
            (root / "skills/brainstorming/SKILL.md").write_text("---\nname: brainstorming\n---\n")
            manifest = build_manifest(root, tag="v1", commit="a" * 40, tag_object="b" * 40, pack="superpowers")
            with self.assertRaisesRegex(SnapshotError, "critical skill"):
                verify_snapshot(root, manifest, "superpowers")

    def test_a_changed_byte_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "v7.0.0"
            shutil.copytree(SUPERPOWERS, copy)
            target = copy / "skills/using-superpowers/SKILL.md"
            target.write_text(target.read_text() + "\n")
            with self.assertRaises(SnapshotError):
                verify_snapshot(copy, self.manifest(), "superpowers")

    def test_critical_superpowers_change_requires_complex_review(self) -> None:
        current = self.manifest()
        candidate = json.loads(json.dumps(current))
        for item in candidate["skills"]:
            if item["name"] == "executing-plans":
                item["sha256"] = "0" * 64
        self.assertEqual(classify_update(current, candidate)["reasons"], ["critical skill changed: executing-plans"])
