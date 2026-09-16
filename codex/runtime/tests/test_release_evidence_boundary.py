from __future__ import annotations

import importlib.util
from pathlib import Path
import py_compile
import struct
import subprocess
import sys
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


class BytecodeCacheIsolationTests(unittest.TestCase):
    """#301：豁免之所以安全，是因为回归子进程根本读不到工作树里的字节码。

    `PYTHONDONTWRITEBYTECODE` 与 `-B` 只阻止子进程**写** `.pyc`，不阻止它**读**：
    一个 header 的 mtime/size 与源文件对齐的 `__pycache__` 条目会被直接执行，
    源文件连编译都不会发生。没有这层隔离，`current_release_regression: PASS`
    就可能是一份对「与 pin 不同的字节码」成立的证据。
    """

    TAMPERED = "TAMPERED"
    SOURCE = "SOURCE"

    def plant_tampered_bytecode(self, root: Path) -> None:
        """造一个 `.py` 与其 in-tree `.pyc` 字节码不一致的包。

        先把篡改后的源码编译进 `__pycache__`，再还原源码，最后把 pyc header 的
        mtime/size 改写成与还原后的源文件一致，使解释器认为缓存是新鲜的。
        header 布局为 magic(4) flags(4) mtime(4) size(4)，`TIMESTAMP` 模式下
        flags 为 0，因此 mtime 与 size 就是全部校验依据。
        """
        package = root / "pkg"
        package.mkdir()
        (package / "__init__.py").write_bytes(b"")
        source = package / "m.py"
        source.write_text(f'VALUE = "{self.TAMPERED}"\n', encoding="utf-8")
        # 手算树内缓存路径，不用 importlib.util.cache_from_source：那个函数会跟随
        # 当前进程的 sys.pycache_prefix。本模块正是由 current_regression 在已经
        # 设了 PYTHONPYCACHEPREFIX 的子进程里执行的，跟随它会把「树内篡改字节码」
        # 写到树外镜像目录，于是整个用例悄悄地什么都不证明。
        cache = package / "__pycache__" / f"m.{sys.implementation.cache_tag}.pyc"
        cache.parent.mkdir()
        py_compile.compile(str(source), cfile=str(cache), doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
        source.write_text(f'VALUE = "{self.SOURCE}"\n', encoding="utf-8")
        header = bytearray(cache.read_bytes())
        stat_result = source.stat()
        struct.pack_into("<II", header, 8, int(stat_result.st_mtime) & 0xFFFFFFFF,
                         stat_result.st_size & 0xFFFFFFFF)
        cache.write_bytes(bytes(header))

    def imported_value(self, cwd: Path, env: dict[str, str]) -> str:
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import pkg.m; print(pkg.m.VALUE)"],
            cwd=cwd, env=env, capture_output=True, text=True, check=True, timeout=60,
        )
        return result.stdout.strip()

    def test_command_env_moves_the_bytecode_cache_out_of_the_work_tree(self) -> None:
        env = boundary.command_env()
        prefix = env.get("PYTHONPYCACHEPREFIX")
        self.assertIsNotNone(prefix)
        self.assertTrue(Path(prefix).is_absolute())
        self.assertNotIn(ROOT, Path(prefix).parents)
        self.assertEqual(env.get("PYTHONDONTWRITEBYTECODE"), "1")
        self.assertEqual(boundary.command_env().get("PYTHONPYCACHEPREFIX"), prefix)

    def test_tampered_in_tree_bytecode_is_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.plant_tampered_bytecode(root)
            control = dict(boundary.command_env())
            control.pop("PYTHONPYCACHEPREFIX")
            # 反向证明：不重定向缓存时，篡改过的字节码确实顶替了源码。
            self.assertEqual(self.imported_value(root, control), self.TAMPERED)
            self.assertEqual(
                self.imported_value(root, boundary.command_env()), self.SOURCE)
