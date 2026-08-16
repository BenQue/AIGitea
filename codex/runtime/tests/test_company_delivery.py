from __future__ import annotations

import contextlib
from datetime import date
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock

from aisoft_company_delivery import bundle as bundle_module
from aisoft_company_delivery.cli import main
from aisoft_company_delivery.contract import (
    EVIDENCE_VERSION,
    HANDOFF_VERSION,
    INVENTORY_VERSION,
    CompanyDeliveryError,
    contains_sensitive_text,
    load_evidence,
    load_handoff,
    load_inventory,
)
from aisoft_company_delivery.collector import collect_inventory
from aisoft_company_delivery.bundle import build_bundle, verify_bundle
from tests.release_test_support import SHA_A, create_release, sha256, update_manifest


SHA = "1" * 40
DIGEST = "2" * 64


class CompanyDeliveryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_json(self, name: str, value: object, *, mode: int = 0o600) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        path.chmod(mode)
        return path

    def inventory(self) -> dict[str, object]:
        return {
            "contract_version": INVENTORY_VERSION,
            "collector_version": "1.0.0",
            "collected_at": "2026-08-16T08:00:00Z",
            "role": "scm-ci",
            "scope": "company-candidate",
            "outcome": "PASS",
            "host": {
                "hostname_sha256": "sha256:" + DIGEST,
                "machine_id_sha256": "sha256:" + DIGEST,
                "os_id": "ubuntu",
                "os_version": "24.04",
                "kernel_version": "6.8.0",
                "architecture": "amd64",
                "cpu_count": 4,
                "memory_bytes": 8_589_934_592,
                "root_free_bytes": 53_687_091_200,
            },
            "tools": [
                {
                    "name": name,
                    "status": "PASS",
                    "version": version,
                    "reason": None,
                }
                for name, version in (
                    ("act-runner", "0.2.13"),
                    ("docker-compose", "5.1.4"),
                    ("docker-engine", "29.7.1"),
                    ("git", "2.50.1"),
                    ("gitea", "1.26.4"),
                    ("python", "3.14.4"),
                )
            ],
            "units": [
                {
                    "name": name,
                    "enabled": "disabled" if name.endswith(".timer") else "enabled",
                    "active": "inactive" if name.endswith(".timer") else "active",
                }
                for name in (
                    "act_runner.service",
                    "aisoft-inbound-sync@newemaint.timer",
                    "docker.service",
                    "gitea.service",
                )
            ],
            "pending": [],
        }

    def evidence(self) -> dict[str, object]:
        return {
            "contract_version": EVIDENCE_VERSION,
            "evidence_id": "CDP-120-STAGE-00-001",
            "stage": "00",
            "scope": "local-fake",
            "recorded_at": "2026-08-16T08:00:00Z",
            "operator_version": "1.0.0",
            "source_git_sha": SHA,
            "release_id": SHA,
            "outcome": "PASS",
            "observed": [
                {
                    "code": "BUNDLE_PRESENT",
                    "status": "PASS",
                    "detail": "Fake bundle exists.",
                    "artifacts": ["handoff-manifest.json"],
                }
            ],
            "changed": [],
            "verified": [],
            "pending": [],
        }

    def handoff(self) -> dict[str, object]:
        return {
            "contract_version": HANDOFF_VERSION,
            "operator_version": "1.0.0",
            "created_at": "2026-08-16T08:00:00Z",
            "source": {
                "repository": "admin/aisoft-platform",
                "git_sha": SHA,
                "transport": "approved-bundle",
            },
            "release": {
                "contract_version": "docker-release/v2",
                "release_id": SHA,
                "manifest_path": "release/release.json",
                "manifest_sha256": DIGEST,
                "platform": "linux/amd64",
                "transport": "offline-bundle",
            },
            "compatibility": {
                "matrix_path": "operator/compatibility/newemaint-company-pilot-v1.json",
                "matrix_sha256": DIGEST,
                "required_roles": ["scm-ci", "appserver-prod"],
            },
            "payloads": [
                {
                    "path": "operator/VERSION",
                    "sha256": DIGEST,
                    "size_bytes": 6,
                    "mode": "0644",
                }
            ],
        }

    def test_valid_contract_documents(self) -> None:
        self.assertEqual(load_inventory(self.write_json("inventory.json", self.inventory()))["role"], "scm-ci")
        self.assertEqual(load_evidence(self.write_json("evidence.json", self.evidence()))["stage"], "00")
        self.assertEqual(
            load_handoff(
                self.write_json("handoff.json", self.handoff()),
                bundle_root=None,
                verify_payloads=False,
            )["source"]["git_sha"],
            SHA,
        )

    def test_repository_templates_and_compatibility_are_parseable(self) -> None:
        repository = Path(__file__).resolve().parents[3]
        delivery = repository / "company-delivery"
        inventory = load_inventory(
            delivery / "templates/inventory.example.json",
            require_protected=False,
        )
        evidence = load_evidence(
            delivery / "templates/evidence.not-run.example.json",
            require_protected=False,
        )
        handoff = load_handoff(
            delivery / "templates/handoff-manifest.example.json",
            bundle_root=None,
            verify_payloads=False,
            require_protected=False,
        )
        compatibility = json.loads(
            (delivery / "compatibility/newemaint-company-pilot-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(inventory["outcome"], "NOT RUN")
        self.assertEqual(evidence["outcome"], "NOT RUN")
        self.assertEqual(handoff["release"]["platform"], "linux/amd64")
        self.assertEqual(compatibility["topology"]["company_vm_count"], 2)
        self.assertEqual(
            compatibility["policy"]["intranet_rebuild_without_isolated_test"],
            "BLOCKED",
        )

    def test_unknown_fields_short_sha_and_unsafe_payload_paths_fail(self) -> None:
        inventory = self.inventory()
        inventory["unexpected"] = True
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(self.write_json("unknown.json", inventory))

        evidence = self.evidence()
        evidence["source_git_sha"] = "1234"
        with self.assertRaises(CompanyDeliveryError):
            load_evidence(self.write_json("short-sha.json", evidence))

        for index, unsafe in enumerate(("/absolute", "../escape", "nested/../../escape")):
            handoff = self.handoff()
            handoff["payloads"][0]["path"] = unsafe
            with self.subTest(path=unsafe), self.assertRaises(CompanyDeliveryError):
                load_handoff(
                    self.write_json(f"unsafe-{index}.json", handoff),
                    bundle_root=None,
                    verify_payloads=False,
                )

    def test_sensitive_content_is_rejected_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        for field, value in (
            ("token", sentinel),
            ("detail", f"Authorization: Bearer {sentinel}"),
            ("detail", f"postgresql://user:{sentinel}@db/app"),
            ("detail", f"-----BEGIN PRIVATE KEY----- {sentinel}"),
        ):
            evidence = self.evidence()
            if field == "token":
                evidence[field] = value
            else:
                evidence["observed"][0][field] = value
            path = self.write_json(f"sensitive-{len(list(self.root.iterdir()))}.json", evidence)
            with self.subTest(field=field), self.assertRaises(CompanyDeliveryError) as caught:
                load_evidence(path)
            self.assertNotIn(sentinel, str(caught.exception))

    def test_evidence_outcome_sections_and_stage_scope_are_fail_closed(self) -> None:
        invalid_documents: list[tuple[str, dict[str, object]]] = []

        passing_with_pending = self.evidence()
        passing_with_pending["pending"] = [
            {
                "code": "EXAMPLE_INPUT_UNKNOWN",
                "status": "BLOCKED",
                "detail": "Example input is unknown.",
                "artifacts": [],
            }
        ]
        invalid_documents.append(("pass-with-pending", passing_with_pending))

        passing_with_failed_verification = self.evidence()
        passing_with_failed_verification["verified"] = [
            {
                "code": "EXAMPLE_VERIFICATION_FAILED",
                "status": "FAIL",
                "detail": "Example verification failed.",
                "artifacts": [],
            }
        ]
        invalid_documents.append(("pass-with-fail", passing_with_failed_verification))

        failed_without_failure = self.evidence()
        failed_without_failure["outcome"] = "FAIL"
        invalid_documents.append(("fail-without-fail-fact", failed_without_failure))

        blocked_without_blocker = self.evidence()
        blocked_without_blocker["outcome"] = "BLOCKED"
        blocked_without_blocker["pending"] = [
            {
                "code": "EXAMPLE_STAGE_NOT_RUN",
                "status": "NOT RUN",
                "detail": "Example stage was not run.",
                "artifacts": [],
            }
        ]
        invalid_documents.append(("blocked-without-blocked-fact", blocked_without_blocker))

        not_run_with_observation = self.evidence()
        not_run_with_observation["outcome"] = "NOT RUN"
        not_run_with_observation["pending"] = [
            {
                "code": "EXAMPLE_STAGE_NOT_RUN",
                "status": "NOT RUN",
                "detail": "Example stage was not run.",
                "artifacts": [],
            }
        ]
        invalid_documents.append(("not-run-with-observation", not_run_with_observation))

        production_stage_with_local_scope = self.evidence()
        production_stage_with_local_scope["stage"] = "100"
        invalid_documents.append(("production-stage-local-scope", production_stage_with_local_scope))

        for name, document in invalid_documents:
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError):
                load_evidence(self.write_json(f"{name}.json", document))

    def test_failed_evidence_can_preserve_pending_manual_actions(self) -> None:
        evidence = self.evidence()
        evidence["outcome"] = "FAIL"
        evidence["verified"] = [
            {
                "code": "EXAMPLE_ACTION_FAILED",
                "status": "FAIL",
                "detail": "Example approved action failed.",
                "artifacts": [],
            }
        ]
        evidence["pending"] = [
            {
                "code": "EXAMPLE_ROLLBACK_NOT_RUN",
                "status": "NOT RUN",
                "detail": "Example rollback awaits separate approval.",
                "artifacts": [],
            }
        ]
        loaded = load_evidence(self.write_json("fail-with-pending.json", evidence))
        self.assertEqual(loaded["outcome"], "FAIL")

    def test_inventory_pass_cannot_hide_incomplete_or_blocked_facts(self) -> None:
        variants: list[tuple[str, object]] = []
        pending = self.inventory()
        pending["pending"] = ["EXAMPLE_FACT_UNKNOWN"]
        variants.append(("pending", pending))

        blocked_tool = self.inventory()
        blocked_tool["tools"][0].update(
            {"status": "BLOCKED", "version": None, "reason": "probe-failed"}
        )
        variants.append(("blocked-tool", blocked_tool))

        incomplete = self.inventory()
        incomplete["tools"] = incomplete["tools"][:-1]
        variants.append(("incomplete", incomplete))

        unknown_host = self.inventory()
        unknown_host["host"]["architecture"] = "unknown"
        variants.append(("unknown-host", unknown_host))

        for name, inventory in variants:
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError):
                load_inventory(self.write_json(f"inventory-{name}.json", inventory))

    def test_protected_file_mode_and_symlink_are_fail_closed(self) -> None:
        permissive = self.write_json("permissive.json", self.inventory(), mode=0o644)
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(permissive)

        target = self.write_json("target.json", self.inventory())
        link = self.root / "link.json"
        link.symlink_to(target)
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(link)

    def test_cli_failure_is_machine_readable_and_sanitized(self) -> None:
        sentinel = "never-print-this-value"
        evidence = self.evidence()
        evidence["observed"][0]["detail"] = f"password={sentinel}"
        path = self.write_json("cli-sensitive.json", evidence)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["verify-evidence", "--input", str(path)])
        self.assertEqual(result, 2)
        value = json.loads(stderr.getvalue())
        self.assertFalse(value["ok"])
        self.assertEqual(value["error_code"], "SENSITIVE_CONTENT")
        self.assertNotIn(sentinel, stderr.getvalue())


class CompanyDeliveryCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.calls: list[tuple[str, ...]] = []
        self.responses = {
            ("hostname",): (0, "company-scm-01\n", ""),
            ("uname", "-r"): (0, "6.8.0-90-generic\n", ""),
            ("uname", "-m"): (0, "x86_64\n", ""),
            ("getconf", "_NPROCESSORS_ONLN"): (0, "4\n", ""),
            ("df", "-Pk", "/"): (0, "Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/root 100 50 50 50% /\n", ""),
            ("git", "--version"): (0, "git version 2.50.1\n", ""),
            ("python3", "--version"): (0, "Python 3.14.4\n", ""),
            ("gitea", "--version"): (0, "Gitea version 1.26.4 built with GNU Make\n", ""),
            ("act_runner", "--version"): (0, "act_runner version v0.2.13\n", ""),
            ("docker", "version", "--format", "{{.Server.Version}}"): (0, "29.7.1\n", ""),
            ("docker", "compose", "version", "--short"): (0, "5.1.4\n", ""),
        }
        for unit in (
            "act_runner.service",
            "docker.service",
            "gitea.service",
        ):
            self.responses[("systemctl", "is-enabled", unit)] = (0, "enabled\n", "")
            self.responses[("systemctl", "is-active", unit)] = (0, "active\n", "")
        timer = "aisoft-inbound-sync@newemaint.timer"
        self.responses[("systemctl", "is-enabled", timer)] = (1, "disabled\n", "")
        self.responses[("systemctl", "is-active", timer)] = (3, "inactive\n", "")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def runner(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        command = tuple(argv)
        self.calls.append(command)
        if command not in self.responses:
            raise FileNotFoundError(command[0])
        code, stdout, stderr = self.responses[command]
        return subprocess.CompletedProcess(argv, code, stdout, stderr)

    def read_text(self, path: Path) -> str:
        values = {
            Path("/etc/os-release"): 'NAME="Ubuntu"\nID=ubuntu\nVERSION_ID="24.04"\n',
            Path("/etc/machine-id"): "machine-id-never-emitted\n",
            Path("/proc/meminfo"): "MemTotal:        8388608 kB\nMemFree:         1024 kB\n",
        }
        return values[path]

    def test_scm_inventory_uses_only_fixed_read_only_probes(self) -> None:
        output = self.root / "inventory.json"
        value = collect_inventory(
            "scm-ci",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "PASS")
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        parsed = load_inventory(output)
        rendered = output.read_text(encoding="utf-8")
        self.assertEqual(parsed["host"]["architecture"], "amd64")
        self.assertNotIn("company-scm-01", rendered)
        self.assertNotIn("machine-id-never-emitted", rendered)
        self.assertTrue(str(parsed["host"]["hostname_sha256"]).startswith("sha256:"))
        flattened = "\n".join(" ".join(command) for command in self.calls)
        for forbidden in ("curl", "ssh", "journalctl", " start ", " enable ", " restart ", " stop "):
            self.assertNotIn(forbidden, flattened)
        self.assertEqual(
            [item for item in parsed["units"] if item["name"].endswith(".timer")],
            [
                {
                    "name": "aisoft-inbound-sync@newemaint.timer",
                    "enabled": "disabled",
                    "active": "inactive",
                }
            ],
        )

    def test_sensitive_probe_output_is_blocked_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        self.responses[("gitea", "--version")] = (
            0,
            f"Gitea version 1.26.4 token={sentinel}\n",
            "",
        )
        output = self.root / "sensitive-inventory.json"
        value = collect_inventory(
            "scm-ci",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "BLOCKED")
        gitea = next(item for item in value["tools"] if item["name"] == "gitea")
        self.assertEqual(gitea["status"], "BLOCKED")
        self.assertEqual(gitea["reason"], "sensitive-output-rejected")
        self.assertNotIn(sentinel, output.read_text(encoding="utf-8"))

    def test_missing_tool_probe_is_not_projected_as_pass(self) -> None:
        self.responses.pop(("gitea", "--version"))
        output = self.root / "missing-tool-inventory.json"
        value = collect_inventory(
            "scm-ci",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "BLOCKED")
        self.assertIn("TOOL_PROBE_MISSING_GITEA", value["pending"])
        gitea = next(item for item in value["tools"] if item["name"] == "gitea")
        self.assertEqual(gitea["status"], "NOT RUN")
        self.assertEqual(gitea["reason"], "command-missing")

    def test_unrelated_semver_in_tool_error_banner_is_not_accepted(self) -> None:
        self.responses[("gitea", "--version")] = (
            0,
            "dependency 9.9.9 failed before Gitea version detection\n",
            "",
        )
        output = self.root / "wrong-banner-inventory.json"
        value = collect_inventory(
            "scm-ci",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "BLOCKED")
        gitea = next(item for item in value["tools"] if item["name"] == "gitea")
        self.assertEqual(gitea["status"], "BLOCKED")
        self.assertEqual(gitea["reason"], "version-output-unrecognized")

    def test_confirmed_absent_scm_tools_allow_side_by_side_inventory(self) -> None:
        for command in (("gitea", "--version"), ("act_runner", "--version")):
            self.responses.pop(command)
        for unit in ("gitea.service", "act_runner.service"):
            self.responses[("systemctl", "is-enabled", unit)] = (4, "", "")
            self.responses[("systemctl", "is-active", unit)] = (4, "", "")
        output = self.root / "fresh-scm-inventory.json"
        value = collect_inventory(
            "scm-ci",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "PASS")
        tools = {item["name"]: item for item in value["tools"]}
        for name in ("gitea", "act-runner"):
            self.assertEqual(tools[name]["status"], "ABSENT")
            self.assertEqual(tools[name]["reason"], "confirmed-not-installed")
            self.assertIsNone(tools[name]["version"])
        self.assertNotIn("TOOL_PROBE_MISSING_GITEA", value["pending"])
        self.assertNotIn("TOOL_PROBE_MISSING_ACT_RUNNER", value["pending"])

    def test_tool_present_with_missing_unit_is_blocked_before_write(self) -> None:
        self.responses[("systemctl", "is-enabled", "gitea.service")] = (4, "", "")
        self.responses[("systemctl", "is-active", "gitea.service")] = (4, "", "")
        output = self.root / "tool-unit-conflict.json"
        value = collect_inventory(
            "scm-ci",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "BLOCKED")
        self.assertIn("TOOL_UNIT_STATE_CONFLICT_GITEA", value["pending"])
        self.assertEqual(load_inventory(output)["outcome"], "BLOCKED")

    def test_appserver_inventory_uses_only_prod_role_probes(self) -> None:
        self.responses[("nginx", "-v")] = (0, "", "nginx version: nginx/1.30.4\n")
        self.responses[("psql", "--version")] = (0, "psql (PostgreSQL) 18.4\n", "")
        for unit in ("docker.service", "nginx.service", "postgresql.service"):
            self.responses[("systemctl", "is-enabled", unit)] = (0, "enabled\n", "")
            self.responses[("systemctl", "is-active", unit)] = (0, "active\n", "")
        output = self.root / "appserver-inventory.json"
        value = collect_inventory(
            "appserver-prod",
            output,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-16T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "PASS")
        versions = {item["name"]: item["version"] for item in value["tools"]}
        self.assertEqual(versions["nginx"], "1.30.4")
        self.assertEqual(versions["postgresql-client"], "18.4.0")
        self.assertNotIn(("gitea", "--version"), self.calls)
        self.assertNotIn(("act_runner", "--version"), self.calls)
        self.assertEqual(
            [item["name"] for item in value["units"]],
            ["docker.service", "nginx.service", "postgresql.service"],
        )

    def test_output_must_be_new_and_parent_mode_0700(self) -> None:
        output = self.root / "inventory.json"
        output.write_text("existing", encoding="utf-8")
        with self.assertRaises(CompanyDeliveryError):
            collect_inventory(
                "scm-ci",
                output,
                runner=self.runner,
                read_text=self.read_text,
                now=lambda: "2026-08-16T08:00:00Z",
            )
        output.unlink()
        self.root.chmod(0o755)
        with self.assertRaises(CompanyDeliveryError):
            collect_inventory(
                "scm-ci",
                output,
                runner=self.runner,
                read_text=self.read_text,
                now=lambda: "2026-08-16T08:00:00Z",
            )


class CompanyDeliveryBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository_root = Path(__file__).resolve().parents[3]
        self.source = self.root / "source"
        self.source.mkdir(mode=0o700)
        for relative in (
            "company-delivery",
            "codex/runtime/aisoft_company_delivery",
            "codex/runtime/aisoft_release",
            "sync",
            "docker-release",
            "codex/config/host-capabilities.json",
            "codex/config/host-role.schema.json",
            "codex/tools/verify-host-role.sh",
        ):
            source = self.repository_root / relative
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(
                    source,
                    target,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
            else:
                shutil.copy2(source, target)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.source, check=True)
        subprocess.run(["git", "config", "user.name", "Company Delivery Test"], cwd=self.source, check=True)
        subprocess.run(["git", "config", "user.email", "company-delivery@test.invalid"], cwd=self.source, check=True)
        subprocess.run(["git", "add", "."], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        fixture = self.root / "release-fixture"
        create_release(fixture)
        self.release_root = fixture / "releases"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def output_dir(self, name: str) -> Path:
        path = self.root / name
        path.mkdir(mode=0o700)
        return path

    def build(self, output: Path) -> dict[str, object]:
        return build_bundle(
            repository_root=self.source,
            source_sha=self.source_sha,
            release_root=self.release_root,
            release_id=SHA_A,
            output_directory=output,
            created_at="2026-08-16T08:00:00Z",
            source_transport="approved-bundle",
        )

    def test_repeat_build_is_byte_identical_and_self_verifying(self) -> None:
        first = self.build(self.output_dir("out-one"))
        second = self.build(self.output_dir("out-two"))
        self.assertEqual(first["archive_sha256"], second["archive_sha256"])
        self.assertEqual(first["archive_name"], second["archive_name"])
        manifest = Path(first["bundle_root"]) / "handoff-manifest.json"
        verified = verify_bundle(manifest, Path(first["bundle_root"]))
        self.assertTrue(verified["ok"])
        self.assertEqual(verified["release_id"], SHA_A)
        self.assertEqual(verified["docker_calls"], 0)
        sums = (Path(first["bundle_root"]) / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertIn("  handoff-manifest.json\n", sums)
        self.assertNotIn("  SHA256SUMS\n", sums)
        extracted = self.root / "extracted"
        extracted.mkdir(mode=0o700)
        previous_umask = os.umask(0o077)
        try:
            with tarfile.open(first["archive_path"], mode="r:gz") as archive:
                archive.extractall(extracted, filter="data")
        finally:
            os.umask(previous_umask)
        extracted_root = extracted / str(first["bundle_name"])
        portable = verify_bundle(extracted_root / "handoff-manifest.json", extracted_root)
        self.assertTrue(portable["ok"])

    def test_payload_tamper_and_unsafe_mode_fail_closed(self) -> None:
        built = self.build(self.output_dir("out-tamper"))
        bundle = Path(built["bundle_root"])
        version = bundle / "operator/VERSION"
        version.write_text("9.9.9\n", encoding="utf-8")
        with self.assertRaises(CompanyDeliveryError) as tampered:
            verify_bundle(bundle / "handoff-manifest.json", bundle)
        self.assertEqual(tampered.exception.code, "CHECKSUM_MISMATCH")

        built = self.build(self.output_dir("out-mode"))
        bundle = Path(built["bundle_root"])
        (bundle / "operator/VERSION").chmod(0o666)
        with self.assertRaises(CompanyDeliveryError) as unsafe:
            verify_bundle(bundle / "handoff-manifest.json", bundle)
        self.assertEqual(unsafe.exception.code, "UNSAFE_MODE")

        built = self.build(self.output_dir("out-parent-link"))
        bundle = Path(built["bundle_root"])
        operator = bundle / "operator"
        relocated = bundle / ".operator-real"
        operator.rename(relocated)
        operator.symlink_to(relocated.name, target_is_directory=True)
        with self.assertRaises(CompanyDeliveryError) as linked:
            verify_bundle(bundle / "handoff-manifest.json", bundle)
        self.assertEqual(linked.exception.code, "UNSAFE_PATH")

    def test_short_sha_dirty_source_and_wrong_release_fail_before_output(self) -> None:
        with self.assertRaises(CompanyDeliveryError):
            build_bundle(
                repository_root=self.source,
                source_sha="1234",
                release_root=self.release_root,
                release_id=SHA_A,
                output_directory=self.output_dir("out-short"),
                created_at="2026-08-16T08:00:00Z",
                source_transport="approved-bundle",
            )
        (self.source / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaises(CompanyDeliveryError):
            self.build(self.output_dir("out-dirty"))
        (self.source / "dirty.txt").unlink()
        with self.assertRaises(CompanyDeliveryError):
            build_bundle(
                repository_root=self.source,
                source_sha=self.source_sha,
                release_root=self.release_root,
                release_id="b" * 40,
                output_directory=self.output_dir("out-release"),
                created_at="2026-08-16T08:00:00Z",
                source_transport="approved-bundle",
            )

    def test_sensitive_release_metadata_is_rejected_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        compose = self.release_root / SHA_A / "compose.yaml"
        compose.write_text(f"# password={sentinel}\n", encoding="utf-8")
        update_manifest(
            self.release_root / SHA_A,
            lambda value: value["compose"].update({"sha256": sha256(compose)}),
        )
        with self.assertRaises(CompanyDeliveryError) as caught:
            self.build(self.output_dir("out-sensitive"))
        self.assertEqual(caught.exception.code, "SENSITIVE_CONTENT")
        self.assertNotIn(sentinel, str(caught.exception))

    def test_sensitive_operator_and_image_archive_payloads_are_rejected(self) -> None:
        sentinel = "never-print-this-value"
        operator_secret = self.source / "company-delivery/operator-secret.txt"
        operator_secret.write_text(f"password={sentinel}\n", encoding="utf-8")
        subprocess.run(["git", "add", str(operator_secret)], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "sensitive fixture"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        with self.assertRaises(CompanyDeliveryError) as operator_error:
            self.build(self.output_dir("out-sensitive-operator"))
        self.assertEqual(operator_error.exception.code, "SENSITIVE_CONTENT")
        self.assertNotIn(sentinel, str(operator_error.exception))

        operator_secret.unlink()
        subprocess.run(["git", "add", "-u"], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "remove fixture"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()

        archive = self.release_root / SHA_A / "images.tar"
        payload = f"password={sentinel}\n".encode("utf-8")
        rewritten_archive = archive.with_suffix(".rewritten")
        with tarfile.open(archive, mode="r") as source_archive, tarfile.open(
            rewritten_archive, mode="w"
        ) as target_archive:
            for member in source_archive:
                if member.isfile():
                    source_handle = source_archive.extractfile(member)
                    self.assertIsNotNone(source_handle)
                    assert source_handle is not None
                    member_payload = source_handle.read()
                    if member.name == "layers/0/layer.tar":
                        member_payload += payload
                    member.size = len(member_payload)
                    target_archive.addfile(member, io.BytesIO(member_payload))
                else:
                    target_archive.addfile(member)
        rewritten_archive.replace(archive)
        inventory_path = self.release_root / SHA_A / "images.inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["archive_sha256"] = sha256(archive)
        inventory_path.write_text(
            json.dumps(inventory, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        update_manifest(
            self.release_root / SHA_A,
            lambda value: value["offline_bundle"].update(
                {
                    "archive_sha256": sha256(archive),
                    "inventory_sha256": sha256(inventory_path),
                }
            ),
        )
        with self.assertRaises(CompanyDeliveryError) as archive_error:
            self.build(self.output_dir("out-sensitive-archive"))
        self.assertEqual(archive_error.exception.code, "SENSITIVE_CONTENT")
        self.assertNotIn(sentinel, str(archive_error.exception))

    def test_artifact_freshness_uses_runtime_utc_date_not_created_at(self) -> None:
        runtime_date = date(2030, 1, 2)
        with mock.patch(
            "aisoft_company_delivery.bundle._utc_today",
            return_value=runtime_date,
        ), mock.patch(
            "aisoft_company_delivery.bundle._verified_release",
            wraps=bundle_module._verified_release,
        ) as verified:
            self.build(self.output_dir("out-runtime-date"))
        self.assertTrue(verified.call_args_list)
        self.assertTrue(all(call.args[2] == runtime_date for call in verified.call_args_list))

    def test_source_placeholder_mask_cannot_hide_literal_secret_values(self) -> None:
        sentinel = "never-print-this-value"
        for unsafe in (
            f"password=${{PASSWORD:-{sentinel}}}",
            f"password=$(printf {sentinel})",
        ):
            with self.subTest(value=unsafe):
                masked = bundle_module._mask_source_placeholders(unsafe)
                self.assertTrue(contains_sensitive_text(masked))
        for safe in (
            'token="$(<"$GITEA_TOKEN_FILE")"',
            "Authorization: token %s",
            "password=$PASSWORD",
            "password=${PASSWORD}",
        ):
            with self.subTest(value=safe):
                masked = bundle_module._mask_source_placeholders(safe)
                self.assertFalse(contains_sensitive_text(masked))

    def test_compose_external_reference_grammar(self) -> None:
        release_dir = self.release_root / SHA_A
        compose = release_dir / "compose.yaml"
        model_path = release_dir / "compose.model.json"
        for index, reference in enumerate(("${PASSWORD}", "${PASSWORD:?required}")):
            with self.subTest(reference=reference):
                model = json.loads(model_path.read_text(encoding="utf-8"))
                model["services"]["web"]["environment"] = {
                    "password": reference,
                }
                model_path.write_text(
                    json.dumps(
                        model,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n",
                    encoding="utf-8",
                )
                compose.write_text(
                    "services:\n"
                    "  web:\n"
                    "    environment:\n"
                    f"      password: \"{reference}\"\n",
                    encoding="utf-8",
                )
                update_manifest(
                    release_dir,
                    lambda value: value["compose"].update(
                        {
                            "sha256": sha256(compose),
                            "model_sha256": sha256(model_path),
                        }
                    ),
                )
                built = self.build(self.output_dir(f"out-external-reference-{index}"))
                self.assertTrue(
                    verify_bundle(
                        Path(built["bundle_root"]) / "handoff-manifest.json",
                        Path(built["bundle_root"]),
                    )["ok"]
                )

    def test_compose_default_and_command_substitution_fail_closed(self) -> None:
        sentinel = "never-print-this-value"
        release_dir = self.release_root / SHA_A
        compose = release_dir / "compose.yaml"
        unsafe_values = (
            f"${{PASSWORD:-{sentinel}}}",
            f"${{PASSWORD-{sentinel}}}",
            f"${{PASSWORD:+{sentinel}}}",
            f"prefix-${{PASSWORD}}-{sentinel}",
            f"$(printf {sentinel})",
            sentinel,
        )
        for index, value in enumerate(unsafe_values):
            with self.subTest(index=index):
                compose.write_text(f"# password={value}\n", encoding="utf-8")
                update_manifest(
                    release_dir,
                    lambda manifest: manifest["compose"].update(
                        {"sha256": sha256(compose)}
                    ),
                )
                output = self.output_dir(f"out-unsafe-compose-{index}")
                with self.assertRaises(CompanyDeliveryError) as caught:
                    self.build(output)
                self.assertEqual(caught.exception.code, "SENSITIVE_CONTENT")
                self.assertNotIn(sentinel, str(caught.exception))
                self.assertEqual(list(output.iterdir()), [])

    def test_wrong_digest_merge_sha_and_architecture_are_blocked(self) -> None:
        variants = {
            "digest": lambda release_dir: release_dir.joinpath("images.tar").write_bytes(
                release_dir.joinpath("images.tar").read_bytes() + b"tampered"
            ),
            "merge-sha": lambda release_dir: update_manifest(
                release_dir,
                lambda value: value.update({"merge_sha": "b" * 40}),
            ),
            "architecture": lambda release_dir: update_manifest(
                release_dir,
                lambda value: value.update({"platform": "linux/arm64"}),
            ),
        }
        for name, mutate in variants.items():
            with self.subTest(name=name):
                fixture = self.root / f"release-{name}"
                create_release(fixture)
                release_root = fixture / "releases"
                mutate(release_root / SHA_A)
                with self.assertRaises(CompanyDeliveryError) as caught:
                    build_bundle(
                        repository_root=self.source,
                        source_sha=self.source_sha,
                        release_root=release_root,
                        release_id=SHA_A,
                        output_directory=self.output_dir(f"out-{name}"),
                        created_at="2026-08-16T08:00:00Z",
                        source_transport="approved-bundle",
                    )
                self.assertEqual(caught.exception.code, "ARTIFACT_INVALID")


class CompanyDeliveryRunbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_root = Path(__file__).resolve().parents[3]

    def test_runbook_has_every_stage_and_required_stop_contract(self) -> None:
        runbook = (self.repository_root / "company-delivery/runbook.md").read_text(encoding="utf-8")
        stages = [
            line.split()[2]
            for line in runbook.splitlines()
            if line.startswith("## Stage ")
        ]
        expected = ["00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "110"]
        self.assertEqual(stages, expected)
        markers = (
            "| 前置输入 |",
            "| 人工批准记录 |",
            "| 执行位置 / role |",
            "| 允许动作 |",
            "| 预期输出 |",
            "| PASS |",
            "| FAIL |",
            "| BLOCKED / 停止点 |",
            "| Evidence |",
            "| 回滚边界 |",
        )
        for stage in expected:
            section = runbook.split(f"## Stage {stage} ", 1)[1].split("\n## Stage ", 1)[0]
            for marker in markers:
                with self.subTest(stage=stage, marker=marker):
                    self.assertIn(marker, section)
        self.assertIn("任何时刻只有一个 stage 处于已批准且可执行状态", runbook)

    def test_runbook_pins_fail_closed_company_boundaries(self) -> None:
        runbook = (self.repository_root / "company-delivery/runbook.md").read_text(encoding="utf-8")
        required = (
            "公司要求内网重建且无隔离测试环境",
            "不同 bytes 不得继承本地测试结论",
            "DB、`app.ini` 与实例 keys、repositories、LFS、packages、attachments、avatars、external storage",
            "`pg_restore --list` 不是 restore PASS",
            "sync/inbound-sync.sh reconcile <allowlisted-profile>",
            "aisoft-docker-release-gate <action> newemaint-prod <full-sha>",
            "sync timer、Actions auto deploy 与 production gate 均为 `disabled/inactive`",
            "普通 Runner 无 production SSH、sudo、业务 DB 或任意 shell 权限",
            "公司侧 Stage 10–110：`NOT RUN`",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runbook)
        matrix = json.loads(
            (self.repository_root / "company-delivery/compatibility/newemaint-company-pilot-v1.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(matrix["topology"]["company_vm_count"], 2)
        self.assertEqual(matrix["policy"]["different_release_bytes"], "BLOCKED")
        self.assertEqual(matrix["policy"]["intranet_rebuild_without_isolated_test"], "BLOCKED")

    def test_all_outcome_templates_are_strict_and_non_live_examples(self) -> None:
        templates = self.repository_root / "company-delivery/templates"
        expected = {
            "evidence.pass.example.json": "PASS",
            "evidence.fail.example.json": "FAIL",
            "evidence.blocked.example.json": "BLOCKED",
            "evidence.not-run.example.json": "NOT RUN",
        }
        for name, outcome in expected.items():
            with self.subTest(name=name):
                value = load_evidence(templates / name, require_protected=False)
                self.assertEqual(value["outcome"], outcome)
                serialized = json.dumps(value, ensure_ascii=False)
                self.assertIn("example", serialized.lower())


class CompanyDeliveryTopologyDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_root = Path(__file__).resolve().parents[3]

    def read(self, name: str) -> str:
        return (self.repository_root / name).read_text(encoding="utf-8")

    def test_authoritative_docs_link_two_vm_newemaint_override(self) -> None:
        names = (
            "README.md",
            "07-内网与生产平移路线.md",
            "12-Linux-GitHub-Gitea-双服务器自动部署方案.md",
            "13-项目结果迁移与内网切换实施手册.md",
        )
        for name in names:
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("company-delivery/runbook.md", text)
                self.assertIn("NewEmaint", text)
                self.assertIn("两台公司", text)
                self.assertIn("本地 OrbStack", text)

    def test_newemaint_never_reuses_company_rebuild_as_local_evidence(self) -> None:
        for name in (
            "07-内网与生产平移路线.md",
            "12-Linux-GitHub-Gitea-双服务器自动部署方案.md",
            "13-项目结果迁移与内网切换实施手册.md",
        ):
            with self.subTest(name=name):
                text = self.read(name)
                self.assertIn("公司要求内网重建", text)
                self.assertIn("BLOCKED", text)
                self.assertIn("exact `docker-release/v2` bytes", text)
        linux = self.read("12-Linux-GitHub-Gitea-双服务器自动部署方案.md")
        self.assertNotIn(
            "合同至少要求 `scm-ci`、`appserver-test`、`appserver-prod` 三个隔离 machine identity",
            linux,
        )

    def test_smoke_covers_company_delivery_shell_json_and_runtime(self) -> None:
        smoke = self.read("codex/tests/smoke.sh")
        self.assertIn('"$ROOT/company-delivery/bin/aisoft-company-delivery"', smoke)
        self.assertIn('find "$ROOT/company-delivery" -type f -name \'*.json\'', smoke)
        self.assertIn("python3 -m unittest discover", smoke)
        self.assertIn("rg -q -i", smoke)
        self.assertNotIn("rg -n -i", smoke)


if __name__ == "__main__":
    unittest.main()
