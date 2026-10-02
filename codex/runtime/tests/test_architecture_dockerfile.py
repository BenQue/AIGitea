"""Real source-input regressions for #288; no Docker daemon or registry."""

from datetime import date
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import canonical_bytes, load_json
from aisoft_architecture.lockfile import build_lock


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
CLI = ARCH / "bin/aisoft-architecture"
NODE22 = "node:22.22.3-bookworm-slim@sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644"
NODE24 = "node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d"


class DockerfileInputTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve()
        (self.repo / ".aisoft").mkdir()
        (self.repo / "docs/deploy").mkdir(parents=True)
        self.project_path = self.repo / ".aisoft/architecture.json"
        self.project = load_json(ARCH / "fixtures/valid/node-sqlite-container-project.json")
        self.project["dockerfiles"] = ["docs/deploy/Dockerfile"]
        self.dockerfile = self.repo / "docs/deploy/Dockerfile"
        self.dockerfile.write_text(f"FROM {NODE22}\n", encoding="utf-8")
        self.lock_path = self.repo / ".aisoft/architecture.lock.json"
        self.save()

    def save(self) -> None:
        self.project_path.write_bytes(canonical_bytes(self.project))

    def cli(self, command: str = "validate", *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([
            str(CLI), command, "--catalog", str(ARCH / "catalog.json"),
            "--profiles-dir", str(ARCH / "profiles"), "--schema-dir", str(ARCH / "schemas"),
            "--project", str(self.project_path), "--today", "2026-09-05", *extra,
        ], cwd="/", capture_output=True, text=True, check=False)

    def error(self, code: str, command: str = "validate", *extra: str) -> None:
        result = self.cli(command, *extra)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        payload = json.loads(result.stderr)
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["diagnostics"][0]["code"], code, result.stderr)
        self.assertNotIn("16d364", result.stderr)
        self.assertNotIn("sensitive-payload", result.stderr)
        self.assertNotIn(str(self.repo), result.stderr)

    def valid(self) -> None:
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def library(self, *, root=None) -> dict:
        return build_lock(
            load_json(ARCH / "catalog.json"), load_json(ARCH / "schemas/catalog-v1.schema.json"),
            load_json(ARCH / f"profiles/{self.project['profile_id']}.json"),
            load_json(ARCH / "schemas/profile-v1.schema.json"), self.project,
            load_json(ARCH / "schemas/project-architecture-v1.schema.json"),
            date(2026, 9, 5), repo_root=root,
        )

    def test_four_original_false_greens_at_all_three_cli_seams(self) -> None:
        self.valid()
        result = self.cli("lock", "--output", str(self.lock_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        baseline = self.lock_path.read_bytes()
        cases = [
            (f"FROM {NODE22[:-1]}0\n", "DOCKERFILE_DIGEST_MISMATCH"),
            (f"FROM {NODE24}\n", "DOCKERFILE_DIGEST_MISMATCH"),
            ("FROM node:22.22.3-bookworm-slim\n", "DOCKERFILE_DIGEST_REQUIRED"),
            (None, "DOCKERFILE_READ_FAILED"),
        ]
        for content, code in cases:
            with self.subTest(code=code, content=content):
                if content is None:
                    self.dockerfile.unlink()
                else:
                    self.dockerfile.write_text(content)
                self.error(code)
                self.error(code, "validate", "--lock", str(self.lock_path))
                self.error(code, "lock", "--output", str(self.lock_path))
                self.assertEqual(self.lock_path.read_bytes(), baseline)
                absent = self.repo / "absent.lock"
                self.error(code, "lock", "--output", str(absent))
                self.assertFalse(absent.exists())

    def test_root_inference_explicit_root_and_library_cannot_bypass(self) -> None:
        self.valid()  # cwd is /; direct .aisoft parent supplies root
        with self.assertRaises(ArchitectureError) as caught:
            self.library()
        self.assertEqual(caught.exception.diagnostic.code, "DOCKERFILE_ROOT_REQUIRED")
        with patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            self.library(root=self.repo)
        self.project_path = self.repo / "architecture.json"
        self.save()
        self.error("DOCKERFILE_ROOT_REQUIRED")
        result = self.cli("validate", "--repo-root", str(self.repo))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_repeat_lock_is_identical(self) -> None:
        result = self.cli("lock", "--output", str(self.lock_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        first = self.lock_path.read_bytes()
        self.assertEqual(self.cli("lock", "--output", str(self.lock_path)).returncode, 0)
        self.assertEqual(first, self.lock_path.read_bytes())

    def test_existing_project_checker_detects_source_drift_read_only(self) -> None:
        result = self.cli("lock", "--output", str(self.lock_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        for arguments in (["init", "-b", "main"], ["add", "."],
                          ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                           "commit", "-m", "synthetic architecture inputs"]):
            result = subprocess.run(["git", "-C", str(self.repo), *arguments], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        checker = ROOT / "codex/tools/aisoft-project-check.sh"

        def check() -> str:
            inputs = {path: path.read_bytes() for path in (self.project_path, self.lock_path, self.dockerfile)}
            result = subprocess.run(["bash", str(checker), "--repo", str(self.repo), "--today", "2026-09-05"],
                                    cwd="/", capture_output=True, text=True, check=False)
            # Minimal fixture intentionally lacks other platform onboarding inputs.
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(inputs, {path: path.read_bytes() for path in inputs})
            return result.stdout

        self.assertIn("PASS: architecture-lock\n", check())
        self.dockerfile.write_text(f"FROM {NODE24}\n")
        output = check()
        self.assertIn("GAP: architecture-lock — strict JSON 或 architecture lock 校验失败", output)
        self.assertNotIn("PASS: architecture-lock\n", output)

    def test_continuation_edges_and_case_insensitive_stage_reuse(self) -> None:
        self.dockerfile.write_text(f"FROM {NODE22} AS builder\nFROM BuIlDeR\n")
        self.valid()
        for content in (f"FROM {NODE22} \\\n", "# syntax=docker/dockerfile:1\n# syntax=docker/dockerfile:1\n"):
            with self.subTest(content=content):
                self.dockerfile.write_text(content)
                self.error("DOCKERFILE_SYNTAX_UNSUPPORTED")

    def test_multistage_comments_continuations_platform_and_escape(self) -> None:
        for escape in ("\\", "`"):
            with self.subTest(escape=escape):
                content = (
                    f"# syntax=docker/dockerfile:1.7\n# escape={escape}\n"
                    f"  fRoM --platform=$BUILDPLATFORM {escape}\n"
                    f"# FROM sensitive-payload\n {NODE22} aS Build\n"
                    "RUN echo example\nFROM BUILD AS final\nFROM scratch\n"
                )
                self.dockerfile.write_bytes(content.replace("\n", "\r\n").encode())
                self.valid()
        # A directive following an ordinary comment is ignored by Docker.
        self.dockerfile.write_text(f"# ordinary comment\n# escape=`\nFROM {NODE22}\n")
        self.valid()

    def test_unsupported_and_malformed_syntax_fail_closed(self) -> None:
        cases = [
            ("# syntax=custom/frontend:1\n", "DOCKERFILE_SYNTAX_UNSUPPORTED"),
            ("# syntax=docker/dockerfile:1-labs\n", "DOCKERFILE_SYNTAX_UNSUPPORTED"),
            ("# escape=x\n", "DOCKERFILE_SYNTAX_UNSUPPORTED"),
            ("# escape=\\\n# escape=`\n", "DOCKERFILE_SYNTAX_UNSUPPORTED"),
            ("RUN <<EOF\nFROM sensitive-payload\nEOF\n", "DOCKERFILE_SYNTAX_UNSUPPORTED"),
            ("UNKNOWN sensitive-payload\n", "DOCKERFILE_SYNTAX_UNSUPPORTED"),
            ("FROM\n", "DOCKERFILE_FROM_INVALID"),
            ("FROM --platform=linux --platform=linux node:22\n", "DOCKERFILE_FROM_INVALID"),
            (f"FROM {NODE22} AS x junk\n", "DOCKERFILE_FROM_INVALID"),
            (f"FROM {NODE22} AS a\nFROM {NODE22} AS A\n", "DOCKERFILE_FROM_INVALID"),
            ("FROM future\nFROM scratch AS future\n", "DOCKERFILE_FROM_INVALID"),
            ("FROM self AS self\n", "DOCKERFILE_FROM_INVALID"),
            ("FROM 0\n", "DOCKERFILE_FROM_INVALID"),
            (f"FROM {NODE22} AS _invalid\n", "DOCKERFILE_FROM_INVALID"),
            ("FROM ubuntu\n", "DOCKERFILE_DIGEST_REQUIRED"),
            (f"FROM node//:22@{NODE22.split('@')[1]}\n", "DOCKERFILE_DIGEST_REQUIRED"),
            (f"ARG BASE={NODE22}\nFROM ${{BASE}}\n", "DOCKERFILE_FROM_VARIABLE_UNSUPPORTED"),
            ("FROM $BASE\n", "DOCKERFILE_FROM_VARIABLE_UNSUPPORTED"),
            (f"FROM node@{NODE22.split('@')[1]}\n", "DOCKERFILE_DIGEST_REQUIRED"),
            (f"FROM {NODE22.upper()}\n", "DOCKERFILE_DIGEST_REQUIRED"),
            ("RUN echo sensitive-payload\n", "DOCKERFILE_FROM_REQUIRED"),
            ("FROM scratch\n", "DOCKERFILE_BASE_IMAGE_UNUSED"),
        ]
        for content, code in cases:
            with self.subTest(content=content):
                self.dockerfile.write_text(content)
                self.error(code)

    def test_multiple_files_and_reverse_digest_coverage(self) -> None:
        second = self.repo / "second.Dockerfile"
        second.write_text(f"FROM {NODE24}\n")
        self.project["dockerfiles"].append("second.Dockerfile")
        self.project["components"].append({
            "component_id": "oci.node.24-bookworm-slim", "version": "24.18.0-bookworm-slim",
            "digest": NODE24.split("@")[1],
        })
        self.save()
        self.valid()

        second.write_text("FROM scratch\n")
        self.error("DOCKERFILE_BASE_IMAGE_UNUSED")
        second.write_text("FROM node:24\n")
        self.error("DOCKERFILE_DIGEST_REQUIRED")
        second.write_text(f"FROM {NODE24}\n")
        self.dockerfile.write_text(f"FROM {NODE22} AS builder\nFROM {NODE24}\n")
        self.valid()

    def test_registry_ports_and_nested_names(self) -> None:
        self.dockerfile.write_text(f"FROM registry.example:5000/team/node:22@{NODE22.split('@')[1]}\n")
        self.valid()

    def test_paths_presence_duplicates_and_secret_names(self) -> None:
        self.project.pop("dockerfiles")
        self.save()
        self.error("DOCKERFILE_DECLARATION_REQUIRED")
        for value in ([], [""], ["/Dockerfile"], ["../Dockerfile"], ["a/./Dockerfile"],
                      ["a//Dockerfile"], ["a\\Dockerfile"], ["a\x00Dockerfile"],
                      [".env"], [".git/config"], ["auth.json"],
                      ["Dockerfile", "Dockerfile"]):
            with self.subTest(value=value):
                self.project["dockerfiles"] = value
                self.save()
                self.error("DOCKERFILE_PATH_INVALID")

    def test_symlink_directory_encoding_size_fifo_and_permissions(self) -> None:
        actual = self.repo / "actual"
        actual.write_text(f"FROM {NODE22}\n")
        self.dockerfile.unlink()
        self.dockerfile.symlink_to(actual)
        self.error("DOCKERFILE_PATH_INVALID")
        self.dockerfile.unlink()
        self.project["dockerfiles"] = ["linked/actual"]
        (self.repo / "linked").symlink_to(self.repo, target_is_directory=True)
        self.save()
        self.error("DOCKERFILE_PATH_INVALID")
        self.project["dockerfiles"] = ["docs/deploy/Dockerfile"]
        self.save()
        self.dockerfile.mkdir()
        self.error("DOCKERFILE_READ_FAILED")
        self.dockerfile.rmdir()
        for data in (b"\xffsensitive-payload", b"x" * (1024 * 1024 + 1)):
            self.dockerfile.write_bytes(data)
            self.error("DOCKERFILE_READ_FAILED")
        self.dockerfile.chmod(0)
        self.error("DOCKERFILE_READ_FAILED")
        self.dockerfile.chmod(0o600)
        self.dockerfile.unlink()
        os.mkfifo(self.dockerfile)
        self.error("DOCKERFILE_READ_FAILED")

    def test_noncontainer_bytes_and_no_dockerfile_read(self) -> None:
        for name in ("node-sqlite-native-project", "sqlite-project", "linux-systemd-project", "windows-project"):
            with self.subTest(name=name):
                self.project = load_json(ARCH / f"fixtures/valid/{name}.json")
                self.save()
                before = canonical_bytes(self.library())
                with patch("os.open", side_effect=AssertionError("Dockerfile opened")):
                    self.assertEqual(before, canonical_bytes(self.library(root=self.repo)))
                self.valid()
                self.project["dockerfiles"] = ["missing.Dockerfile"]
                self.save()
                self.error("DOCKERFILE_DECLARATION_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
