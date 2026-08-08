import json
from pathlib import Path
import tempfile
import unittest

from aisoft_loop.matt_snapshot import (
    SnapshotError,
    build_manifest,
    classify_update,
    verify_snapshot,
)


ROOT = Path(__file__).parents[3]
VENDOR = ROOT / "codex" / "vendor" / "mattpocock" / "v1.2.2"


class MattSnapshotTests(unittest.TestCase):
    def test_vendored_release_is_complete_and_matches_manifest(self) -> None:
        manifest = json.loads((VENDOR / "manifest.json").read_text())
        verified = verify_snapshot(VENDOR, manifest)
        self.assertEqual(verified["tag"], "v1.2.2")
        self.assertEqual(verified["commit"], "8b36d4fb2635b3c21998dcd8144439c9e5ba7302")
        self.assertEqual(verified["skill_count"], 35)
        self.assertIn("triage", verified["skill_names"])
        self.assertIn("implement", verified["skill_names"])

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
