from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "release_evidence_boundary", ROOT / "codex/tests/check-release-evidence-boundary.py"
)
boundary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(boundary)


class ReleaseEvidenceBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        old_runner = b"# fixture\n" + boundary.ANCHOR
        self.expected_runner = old_runner.replace(
            boundary.ANCHOR, boundary.ANCHOR + boundary.ADDITION
        )
        self.files = {
            boundary.RUNNER: old_runner,
            "codex/runtime/aisoft_release/transport.py": b"# transport\n",
            "docker-release/README.md": b"docs\n",
            "docker-release/install.sh": b"installer\n",
            "docker-release/compatibility/image-stores-v1.json": b"{}\n",
            boundary.EVIDENCE: b'{"result":"PASS"}\n',
            boundary.HISTORICAL_TEST: b"exit 0\n",
            "codex/tests/fixtures/docker-release-v2-lifecycle/migrate.sh": b"fixture\n",
        }
        for name, content in self.files.items():
            self.write(name, content)
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "baseline")
        self.baseline = self.git("rev-parse", "HEAD").decode().strip()
        for name, value in {
            "BASELINE": self.baseline,
            "CURRENT_SOURCE_PINS": {},
            "SCOPES": ("codex/runtime/aisoft_release", "docker-release", boundary.EVIDENCE,
                       boundary.HISTORICAL_TEST, "codex/tests/fixtures/docker-release-v2-lifecycle"),
            "RUNNER_BEFORE": boundary.digest(old_runner),
            "RUNNER_AFTER": boundary.digest(self.expected_runner),
            "EVIDENCE_SHA256": boundary.digest(self.files[boundary.EVIDENCE]),
        }.items():
            context = patch.object(boundary, name, value)
            context.start()
            self.addCleanup(context.stop)
        self.write(boundary.RUNNER, self.expected_runner)
        self.git("add", "--", boundary.RUNNER)

    def git(self, *args: str) -> bytes:
        return boundary.git(self.root, *args)

    def write(self, name: str, content: bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def rejected(self) -> None:
        with self.assertRaises((boundary.BoundaryError, OSError)):
            boundary.validate(self.root)

    def test_exact_revision_passes_and_document_exceptions_are_bounded(self) -> None:
        result = boundary.validate(self.root)
        self.assertEqual(result["runner_sha256"], boundary.digest(self.expected_runner))
        self.write("docker-release/README.md", b"updated docs\n")
        self.write("docker-release/install.sh", b"updated installer\n")
        self.assertEqual(boundary.validate(self.root)["historical_evidence_sha256"],
                         boundary.digest(self.files[boundary.EVIDENCE]))
        self.write("docker-release/new-file", b"not exempt")
        self.rejected()

    def test_all_pinned_files_reject_a_single_extra_byte(self) -> None:
        for name in set(self.files) - boundary.CONTENT_EXEMPT:
            with self.subTest(path=name):
                before = (self.root / name).read_bytes()
                self.write(name, before + b" ")
                self.rejected()
                self.write(name, before)

    def test_current_amendment_pins_require_exact_disk_and_index_bytes(self) -> None:
        changed = {boundary.RUNNER: self.expected_runner + b"# reviewed identity fix\n",
                   boundary.TRANSPORT: b"# reviewed graph verification\n",
                   boundary.MATRIX: b'{"revision":"reviewed"}\n'}
        with patch.object(boundary, "CURRENT_SOURCE_PINS", {
            name: boundary.digest(value) for name, value in changed.items()
        }):
            for name, value in changed.items():
                self.write(name, value)
                self.git("add", "--", name)
            boundary.validate(self.root)
            for name, value in changed.items():
                with self.subTest(path=name):
                    self.write(name, value + b"# drift")
                    self.rejected()
                    self.git("add", "--", name)
                    self.write(name, value)
                    self.rejected()
                    self.git("add", "--", name)
            self.write(boundary.EVIDENCE, b"replacement history")
            self.rejected()

    def test_current_pins_cannot_exempt_other_paths_or_use_invalid_hashes(self) -> None:
        for pins in ({boundary.EVIDENCE: boundary.digest(self.files[boundary.EVIDENCE])},
                     {boundary.TRANSPORT: ""}, {boundary.TRANSPORT: "g" * 64}):
            with self.subTest(pins=pins), patch.object(boundary, "CURRENT_SOURCE_PINS", pins):
                self.rejected()

    def test_production_and_unknown_action_widening_are_rejected(self) -> None:
        for before, after in ((b'== "test"', b'== "production"'),
                              (b"roles is not None", b"True")):
            with self.subTest(change=before):
                self.write(boundary.RUNNER, self.expected_runner.replace(before, after))
                self.rejected()

    def test_ignored_and_untracked_files_including_bytecode_are_rejected(self) -> None:
        self.write(".gitignore", b"*.pyc\nhidden.py\n")
        for name in ("extra.py", "hidden.py", "__pycache__/runner.cpython-313.pyc"):
            with self.subTest(name=name):
                path = "codex/runtime/aisoft_release/" + name
                self.write(path, b"unexpected")
                self.rejected()
                (self.root / path).unlink()

    def test_missing_renamed_and_symlink_paths_are_rejected(self) -> None:
        path = self.root / boundary.RUNNER
        path.unlink()
        self.rejected()
        self.write(boundary.RUNNER, self.expected_runner)
        renamed = path.with_name("renamed.py")
        path.rename(renamed)
        self.rejected()
        path.symlink_to(renamed)
        self.rejected()

    def test_symlink_ancestor_is_rejected(self) -> None:
        directory = self.root / "codex/runtime/aisoft_release"
        moved = self.root / "moved"
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        self.rejected()

    def test_disk_and_index_modes_are_independently_checked(self) -> None:
        path = self.root / boundary.RUNNER
        path.chmod(0o755)
        self.rejected()
        path.chmod(0o644)
        self.git("update-index", "--chmod=+x", "--", boundary.RUNNER)
        self.rejected()

    def test_staged_tamper_is_rejected_even_if_disk_was_restored(self) -> None:
        self.write(boundary.RUNNER, self.expected_runner + b"# staged drift\n")
        self.git("add", "--", boundary.RUNNER)
        self.write(boundary.RUNNER, self.expected_runner)
        self.rejected()

    def test_deleted_index_entry_is_rejected(self) -> None:
        self.git("update-index", "--force-remove", "--", boundary.RUNNER)
        self.rejected()

    def test_missing_baseline_or_wrong_pins_fail_closed(self) -> None:
        for field, value in (("BASELINE", "0" * 40), ("RUNNER_BEFORE", "0" * 64),
                             ("RUNNER_AFTER", "0" * 64), ("EVIDENCE_SHA256", "0" * 64)):
            with self.subTest(field=field), patch.object(boundary, field, value):
                self.rejected()

    def test_success_requires_history_and_current_regressions(self) -> None:
        with patch.object(boundary, "historical_regression") as history, \
                patch.object(boundary, "current_regression") as current:
            result = boundary.check(self.root)
        history.assert_called_once()
        current.assert_called_once()
        self.assertEqual(result["current_real_e2e"], "NOT_RUN")
        self.assertEqual(result["current_release_regression"], "PASS")

    def test_any_regression_failure_fails_the_combined_check(self) -> None:
        for failed in ("historical_regression", "current_regression"):
            with self.subTest(failed=failed), \
                    patch.object(boundary, "historical_regression"), \
                    patch.object(boundary, "current_regression"), \
                    patch.object(boundary, failed, side_effect=boundary.BoundaryError("failure")):
                with self.assertRaises(boundary.BoundaryError):
                    boundary.check(self.root)

    def test_drift_during_either_regression_fails(self) -> None:
        for phase in ("historical_regression", "current_regression"):
            with self.subTest(phase=phase), patch.object(boundary, "historical_regression"), \
                    patch.object(boundary, "current_regression"), \
                    patch.object(boundary, phase, side_effect=lambda *_: self.write(
                        boundary.RUNNER, self.expected_runner + b"# drift\n")):
                with self.assertRaises(boundary.BoundaryError):
                    boundary.check(self.root)
                self.write(boundary.RUNNER, self.expected_runner)

    def test_nonzero_command_is_not_reported_as_pass(self) -> None:
        records = []
        with self.assertRaises(boundary.BoundaryError):
            boundary.run_checked(self.root, ["python3", "-c", "raise SystemExit(7)"], records)
        self.assertEqual(records[0]["exit_code"], 7)

    def test_history_runs_only_fixed_local_snapshot_and_cleans_it(self) -> None:
        seen = []

        def inspect(snapshot, argv, records):
            seen.append(snapshot)
            self.assertNotEqual(snapshot, self.root)
            self.assertEqual(boundary.git(snapshot, "rev-parse", "HEAD").decode().strip(), self.baseline)
            self.assertEqual((snapshot / boundary.RUNNER).read_bytes(), self.files[boundary.RUNNER])
            self.assertEqual(argv, ["bash", boundary.HISTORICAL_TEST])

        with patch.object(boundary, "run_checked", side_effect=inspect):
            boundary.historical_regression(self.root, [])
        self.assertEqual(len(seen), 1)
        self.assertFalse(seen[0].exists())

    def test_cli_accepts_no_override(self) -> None:
        with patch.object(boundary.sys, "argv", ["check", "--baseline", self.baseline]), \
                patch.object(boundary, "check") as check:
            self.assertEqual(boundary.main(), 1)
        check.assert_not_called()
