from __future__ import annotations

import base64
import contextlib
from datetime import date
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock

from aisoft_company_delivery import bundle as bundle_module
from aisoft_company_delivery import collector as collector_module
from aisoft_company_delivery import contract as contract_module
from aisoft_company_delivery import secret_scan as secret_scan_module
from aisoft_company_delivery.cli import build_parser, main
from aisoft_company_delivery.contract import (
    EVIDENCE_VERSION,
    FIXED_GITEA_TARGET,
    HANDOFF_VERSION,
    INVENTORY_V1_VERSION,
    INVENTORY_V2_VERSION,
    INVENTORY_V3_VERSION,
    LEGACY_TRANSITION_VERSION,
    SCM_AUTOMATION,
    TRANSITION_VERSION,
    CompanyDeliveryError,
    contains_sensitive_text,
    inventory_sync_timer_unit,
    legacy_baseline_sha256,
    load_compatibility_matrix,
    load_evidence,
    load_gitea_transition,
    load_handoff,
    load_inventory,
    verify_gitea_transition,
    verify_legacy_health,
)
from aisoft_company_delivery.collector import collect_inventory, sync_timer_unit_from_handoff
from aisoft_company_delivery.bundle import build_bundle, verify_bundle
from tests.release_test_support import (
    SHA_A,
    create_archive,
    create_layer_archive_payload,
    create_release,
    sha256,
    update_manifest,
)


SHA = "1" * 40
DIGEST = "2" * 64
# Project-neutral sync timer instance: the unit name is declared by the
# compatibility matrix / handoff manifest, never by the runtime.
TIMER = "aisoft-inbound-sync@example.timer"
MATRIX_PATH = "operator/compatibility/compatibility-matrix.example.json"


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
            "contract_version": INVENTORY_V1_VERSION,
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
                    TIMER,
                    "docker.service",
                    "gitea.service",
                )
            ],
            "pending": [],
        }

    def inventory_v2(self) -> dict[str, object]:
        value = self.inventory()
        value.update(
            {
                "contract_version": INVENTORY_V2_VERSION,
                "collector_version": "1.1.1",
                "mode": "preflight",
                "scm": {
                    "probe_profile": "greenfield-parallel-replacement-v1",
                    "legacy": {
                        "publish_port_sha256": "sha256:" + DIGEST,
                        "presence": "present",
                        "container_id_sha256": "sha256:" + DIGEST,
                        "health": "healthy",
                        "version": "1.26.4",
                        "baseline_sha256": "sha256:" + DIGEST,
                        "reason": None,
                    },
                    "candidate": {
                        "ports": {
                            "gitea_http": "free",
                            "postgresql": "free",
                        },
                        "resources": {
                            "gitea_binary": "absent",
                            "gitea_config": "absent",
                            "gitea_data": "absent",
                            "gitea_log": "absent",
                            "postgresql_data": "absent",
                        },
                        "services": {
                            "gitea": {"enabled": "not-found", "active": "not-found"},
                            "postgresql": {"enabled": "not-found", "active": "not-found"},
                        },
                    },
                    "automation": {
                        "gitea_ssh": "disabled",
                        "runner": "disabled-inactive",
                        "sync_timer": "disabled-inactive",
                        "actions_auto_deploy": "disabled-inactive",
                        "production_gate": "disabled-inactive",
                        "dns_tls": "NOT RUN",
                        "reverse_proxy": "NOT RUN",
                        "repository_import": "NOT RUN",
                    },
                },
            }
        )
        for tool in value["tools"]:
            if tool["name"] == "gitea":
                tool.update(
                    {"status": "ABSENT", "version": None, "reason": "confirmed-not-installed"}
                )
        for unit in value["units"]:
            if unit["name"] == "gitea.service":
                unit.update({"enabled": "not-found", "active": "not-found"})
        value["scm"]["legacy"]["baseline_sha256"] = legacy_baseline_sha256(
            value["scm"]["legacy"]
        )
        return value

    def appserver_inventory_v2(self) -> dict[str, object]:
        value = self.inventory_v2()
        value["role"] = "appserver-prod"
        value["mode"] = None
        value["scm"] = None
        value["tools"] = [
            {"name": name, "status": "PASS", "version": version, "reason": None}
            for name, version in (
                ("docker-compose", "5.1.4"),
                ("docker-engine", "29.7.1"),
                ("nginx", "1.30.4"),
                ("postgresql-client", "18.4.0"),
                ("python", "3.14.4"),
            )
        ]
        value["units"] = [
            {"name": name, "enabled": "enabled", "active": "active"}
            for name in ("docker.service", "nginx.service", "postgresql.service")
        ]
        return value

    def post_install_inventory_v2(self) -> dict[str, object]:
        value = self.inventory_v2()
        value["mode"] = "post-install"
        value["scm"]["candidate"]["ports"] = {
            "gitea_http": "occupied",
            "postgresql": "occupied",
        }
        value["scm"]["candidate"]["resources"] = {
            key: "occupied" for key in value["scm"]["candidate"]["resources"]
        }
        value["scm"]["candidate"]["services"] = {
            "gitea": {"enabled": "enabled", "active": "active"},
            "postgresql": {"enabled": "enabled", "active": "active"},
        }
        return value

    def inventory_v3(self) -> dict[str, object]:
        value = self.inventory_v2()
        value["contract_version"] = INVENTORY_V3_VERSION
        value["collector_version"] = "1.3.0"
        value["scm"]["probe_profile"] = "greenfield-isolated-install-v1"
        value["scm"].pop("legacy")
        value["scm"]["candidate"]["health"] = {
            "status": "NOT RUN",
            "version": None,
            "reason": "not-run",
        }
        return value

    def appserver_inventory_v3(self) -> dict[str, object]:
        value = self.inventory_v3()
        value["role"] = "appserver-prod"
        value["mode"] = None
        value["scm"] = None
        value["tools"] = self.appserver_inventory_v2()["tools"]
        value["units"] = self.appserver_inventory_v2()["units"]
        return value

    def post_install_inventory_v3(self) -> dict[str, object]:
        value = self.inventory_v3()
        value["mode"] = "post-install"
        value["scm"]["candidate"]["ports"] = {
            "gitea_http": "occupied",
            "postgresql": "occupied",
        }
        value["scm"]["candidate"]["resources"] = {
            key: "occupied" for key in value["scm"]["candidate"]["resources"]
        }
        value["scm"]["candidate"]["services"] = {
            "gitea": {"enabled": "enabled", "active": "active"},
            "postgresql": {"enabled": "enabled", "active": "active"},
        }
        value["scm"]["candidate"]["health"] = {
            "status": "healthy",
            "version": "1.26.4",
            "reason": None,
        }
        return value

    def transition(self, *, decision: str = "greenfield-isolated-install") -> dict[str, object]:
        return {
            "contract_version": TRANSITION_VERSION,
            "operator_version": "1.3.0",
            "recorded_at": "2026-08-17T08:00:00Z",
            "source_git_sha": SHA,
            "handoff_manifest_sha256": "3" * 64,
            "postgresql_package_manifest_sha256": "4" * 64,
            "reviewer_decision_id": "APR-126-STAGE-20-001",
            "decision": decision,
            "outcome": "PASS",
            "inventories": {
                "scm_ci_sha256": DIGEST,
                "appserver_prod_sha256": "3" * 64,
            },
            "public_name_sha256": "sha256:" + "4" * 64,
            "target": {
                "gitea_version": "1.26.4",
                "gitea_artifact": "gitea-1.26.4-linux-amd64",
                "gitea_sha256": "0faa36d151918f8f7d6e0f3ae67597d1c338583d695add146ac393109d0fc44a",
                "postgresql_version": "18.4",
                "postgresql_provenance_artifact": "postgresql-18.4.tar.bz2",
                "postgresql_provenance_sha256": "81a81ec695fb0c7901407defaa1d2f7973617154cf27ba74e3a7ab8e64436094",
                "linux_user": "aisoft-gitea",
                "linux_group": "aisoft-gitea",
                "gitea_unit": "aisoft-gitea.service",
                "gitea_binary": "/opt/aisoft/gitea/1.26.4/gitea",
                "gitea_config": "/etc/aisoft/gitea/app.ini",
                "gitea_data": "/var/lib/aisoft-gitea",
                "gitea_log": "/var/log/aisoft-gitea",
                "postgresql_cluster": "aisoft-gitea",
                "postgresql_unit": "postgresql@18-aisoft-gitea.service",
                "postgresql_data": "/var/lib/postgresql/18/aisoft-gitea",
                "postgresql_database": "aisoft_gitea",
                "postgresql_role": "aisoft_gitea",
                "gitea_http": "127.0.0.1:8888",
                "postgresql_listen": "127.0.0.1:55432",
            },
            "prerequisites": {
                "candidate_namespace_isolated": True,
                "stage50_prerequisite": "candidate-post-install-health",
            },
            "automation": {
                "gitea_ssh": "disabled",
                "runner": "disabled-inactive",
                "sync_timer": "disabled-inactive",
                "actions_auto_deploy": "disabled-inactive",
                "production_gate": "disabled-inactive",
                "dns_tls": "NOT RUN",
                "reverse_proxy": "NOT RUN",
                "repository_import": "NOT RUN",
            },
            "stages": {
                "00": "PASS",
                "10-scm-ci": "PASS",
                "10-appserver-prod": "PASS",
                "20": "PASS",
                "30": "NOT RUN",
                "40": "NOT RUN",
                "50": "NOT RUN",
            },
            "pending": [],
        }

    def legacy_transition(self) -> dict[str, object]:
        value = self.transition()
        value.update(
            {
                "contract_version": LEGACY_TRANSITION_VERSION,
                "operator_version": "1.1.1",
                "decision": "greenfield-parallel-replacement",
                "legacy_baseline_sha256": "sha256:" + DIGEST,
                "prerequisites": {
                    "legacy_backup_required": False,
                    "isolated_restore_required": False,
                    "stage50_prerequisite": "legacy-pre-post-equality",
                },
            }
        )
        return value

    def bound_transition_files(
        self,
        *,
        prefix: str = "bound",
        decision: str = "greenfield-isolated-install",
    ) -> tuple[Path, Path, Path, Path, Path]:
        scm_value = self.inventory_v3()
        appserver_value = self.appserver_inventory_v3()
        scm_path = self.write_json(f"{prefix}-scm.json", scm_value)
        appserver_path = self.write_json(f"{prefix}-appserver.json", appserver_value)
        handoff_path = self.write_handoff_bundle(prefix)
        package_manifest_path = self.root / f"{prefix}-postgresql-packages.sha256"
        package_manifest_path.write_text(
            "5" * 64 + "  postgresql-client.pkg\n",
            encoding="ascii",
        )
        package_manifest_path.chmod(0o600)
        transition = self.transition(decision=decision)
        transition["inventories"] = {
            "scm_ci_sha256": sha256(scm_path),
            "appserver_prod_sha256": sha256(appserver_path),
        }
        transition["handoff_manifest_sha256"] = sha256(handoff_path)
        transition["postgresql_package_manifest_sha256"] = sha256(
            package_manifest_path
        )
        transition_path = self.write_json(f"{prefix}-transition.json", transition)
        return (
            transition_path,
            scm_path,
            appserver_path,
            handoff_path,
            package_manifest_path,
        )

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
                "matrix_path": MATRIX_PATH,
                "matrix_sha256": DIGEST,
                "required_roles": ["scm-ci", "appserver-prod"],
                "sync_timer_unit": TIMER,
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

    def write_handoff_bundle(
        self,
        prefix: str,
        *,
        source_sha: str = SHA,
        operator_version: str = "1.3.0",
    ) -> Path:
        bundle = self.root / f"{prefix}-bundle"
        bundle.mkdir(mode=0o700)
        payload_values = {
            "operator/VERSION": (operator_version + "\n").encode("ascii"),
            MATRIX_PATH: b"{}\n",
            "release/release.json": b"{}\n",
        }
        payloads: list[dict[str, object]] = []
        for relative, content in payload_values.items():
            target = bundle / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            current = target.parent
            while current != bundle:
                current.chmod(0o700)
                current = current.parent
            target.write_bytes(content)
            target.chmod(0o644)
            payloads.append(
                {
                    "path": relative,
                    "sha256": sha256(target),
                    "size_bytes": len(content),
                    "mode": "0644",
                }
            )
        payloads.sort(key=lambda item: str(item["path"]))
        handoff = self.handoff()
        handoff["operator_version"] = operator_version
        handoff["source"]["git_sha"] = source_sha
        handoff["release"]["manifest_sha256"] = sha256(
            bundle / "release/release.json"
        )
        handoff["compatibility"]["matrix_sha256"] = sha256(bundle / MATRIX_PATH)
        handoff["payloads"] = payloads
        manifest = bundle / "handoff-manifest.json"
        manifest.write_text(json.dumps(handoff, sort_keys=True), encoding="utf-8")
        manifest.chmod(0o600)
        checksums = {
            str(item["path"]): str(item["sha256"])
            for item in payloads
        }
        checksums["handoff-manifest.json"] = sha256(manifest)
        checksum_path = bundle / "SHA256SUMS"
        checksum_path.write_text(
            "".join(
                f"{digest}  {relative}\n"
                for relative, digest in sorted(checksums.items())
            ),
            encoding="ascii",
        )
        checksum_path.chmod(0o600)
        return manifest

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
        transition = load_gitea_transition(
            delivery / "templates/gitea-transition.example.json",
            require_protected=False,
        )
        compatibility = load_compatibility_matrix(
            delivery / "templates/compatibility-matrix.example.json"
        )
        self.assertEqual(inventory["outcome"], "NOT RUN")
        self.assertEqual(inventory["contract_version"], INVENTORY_V3_VERSION)
        self.assertEqual(evidence["outcome"], "NOT RUN")
        self.assertEqual(transition["outcome"], "BLOCKED")
        self.assertEqual(handoff["release"]["platform"], "linux/amd64")
        self.assertEqual(compatibility["topology"]["company_vm_count"], 2)
        self.assertEqual(compatibility["sync_timer_unit"], TIMER)
        self.assertEqual(handoff["compatibility"]["sync_timer_unit"], TIMER)
        self.assertEqual(
            handoff["compatibility"]["matrix_path"],
            "operator/compatibility/compatibility-matrix.example.json",
        )
        self.assertEqual(handoff["operator_version"], contract_module.OPERATOR_VERSION)
        self.assertEqual(transition["operator_version"], contract_module.OPERATOR_VERSION)
        self.assertEqual(
            compatibility["policy"]["intranet_rebuild_without_isolated_test"],
            "BLOCKED",
        )
        # #239: the template matrix is project-neutral structure, not pilot data.
        rendered = json.dumps(compatibility, ensure_ascii=False).lower()
        self.assertIn("example", rendered)
        self.assertNotIn("stage_map", compatibility)
        schemas = {
            path.name: json.loads(path.read_text(encoding="utf-8"))
            for path in (delivery / "schema").glob("*.schema.json")
        }
        self.assertEqual(
            schemas["inventory-v2.schema.json"]["properties"]["contract_version"]["const"],
            INVENTORY_V2_VERSION,
        )
        self.assertEqual(
            schemas["gitea-transition-v1.schema.json"]["properties"]["contract_version"]["const"],
            LEGACY_TRANSITION_VERSION,
        )
        self.assertEqual(
            schemas["inventory-v3.schema.json"]["properties"]["contract_version"]["const"],
            INVENTORY_V3_VERSION,
        )
        self.assertEqual(
            schemas["gitea-transition-v2.schema.json"]["properties"]["contract_version"]["const"],
            TRANSITION_VERSION,
        )
        self.assertEqual(
            schemas["compatibility-v1.schema.json"]["properties"]["contract_version"]["const"],
            contract_module.COMPATIBILITY_VERSION,
        )
        self.assertEqual(
            schemas["handoff-v1.schema.json"]["properties"]["compatibility"]["properties"][
                "sync_timer_unit"
            ]["pattern"],
            contract_module.SYNC_TIMER_UNIT.pattern,
        )
        for name in ("inventory-v1", "inventory-v2", "inventory-v3"):
            unit_name = schemas[f"{name}.schema.json"]["$defs"]["unit"]["properties"]["name"]
            with self.subTest(schema=name):
                self.assertEqual(
                    unit_name["anyOf"][1]["pattern"], contract_module.SYNC_TIMER_UNIT.pattern
                )
                self.assertEqual(
                    unit_name["anyOf"][0]["enum"],
                    sorted(contract_module.UNIT_NAMES),
                )

    def test_inventory_accepts_any_sync_timer_instance_exactly_once(self) -> None:
        # #239: the inventory contract binds the timer by pattern, not by a
        # project-specific constant; scm-ci must record exactly one instance.
        for version_builder in (self.inventory, self.inventory_v3):
            renamed = version_builder()
            for unit in renamed["units"]:
                if unit["name"].endswith(".timer"):
                    unit["name"] = "aisoft-inbound-sync@another.project_1.timer"
            loaded = load_inventory(self.write_json(f"renamed-{version_builder.__name__}.json", renamed))
            self.assertEqual(
                inventory_sync_timer_unit(loaded), "aisoft-inbound-sync@another.project_1.timer"
            )
        self.assertIsNone(inventory_sync_timer_unit(self.appserver_inventory_v3()))

        variants: list[tuple[str, dict[str, object]]] = []
        missing = self.inventory()
        missing["units"] = [unit for unit in missing["units"] if not unit["name"].endswith(".timer")]
        variants.append(("missing-timer", missing))
        doubled = self.inventory()
        doubled["units"].append(
            {"name": "aisoft-inbound-sync@second.timer", "enabled": "disabled", "active": "inactive"}
        )
        variants.append(("two-timers", doubled))
        for bad_name in ("aisoft-inbound-sync@.timer", "aisoft-inbound-sync@x.service", "other@x.timer"):
            malformed = self.inventory()
            for unit in malformed["units"]:
                if unit["name"].endswith(".timer"):
                    unit["name"] = bad_name
            variants.append((f"malformed-{bad_name}", malformed))
        appserver = self.appserver_inventory_v3()
        appserver["units"].append({"name": TIMER, "enabled": "disabled", "active": "inactive"})
        variants.append(("appserver-with-timer", appserver))
        armed = self.inventory()
        for unit in armed["units"]:
            if unit["name"].endswith(".timer"):
                unit.update({"enabled": "enabled", "active": "active"})
        variants.append(("armed-timer-pass", armed))
        for name, value in variants:
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError) as rejected:
                load_inventory(self.write_json(f"timer-{name}.json", value))
            self.assertEqual(rejected.exception.code, "INVALID_CONTRACT")

    def test_handoff_sync_timer_unit_is_required_from_operator_1_3(self) -> None:
        # #239: operator >= 1.3.0 handoffs declare the sync timer unit; older
        # handoffs stay readable as archived evidence without it.
        legacy = self.handoff()
        legacy["operator_version"] = "1.2.0"
        legacy["compatibility"].pop("sync_timer_unit")
        loaded = load_handoff(
            self.write_json("legacy-handoff.json", legacy), bundle_root=None, verify_payloads=False
        )
        self.assertNotIn("sync_timer_unit", loaded["compatibility"])

        for version in ("1.3.0", "1.4.2", "2.0.0"):
            current = self.handoff()
            current["operator_version"] = version
            current["compatibility"].pop("sync_timer_unit")
            with self.subTest(version=version), self.assertRaises(CompanyDeliveryError) as rejected:
                load_handoff(
                    self.write_json(f"undeclared-{version}.json", current),
                    bundle_root=None,
                    verify_payloads=False,
                )
            self.assertEqual(rejected.exception.code, "INVALID_CONTRACT")

        declared = self.handoff()
        declared["operator_version"] = "1.3.0"
        loaded = load_handoff(
            self.write_json("declared-handoff.json", declared), bundle_root=None, verify_payloads=False
        )
        self.assertEqual(loaded["compatibility"]["sync_timer_unit"], TIMER)
        malformed = self.handoff()
        malformed["compatibility"]["sync_timer_unit"] = "aisoft-inbound-sync@.timer"
        with self.assertRaises(CompanyDeliveryError):
            load_handoff(
                self.write_json("malformed-timer-handoff.json", malformed),
                bundle_root=None,
                verify_payloads=False,
            )

    def test_compatibility_matrix_binds_only_contract_version_and_timer(self) -> None:
        matrix = {
            "contract_version": "company-delivery-compatibility/v1",
            "sync_timer_unit": TIMER,
            "topology": {"company_vm_count": 2},
            "anything_else": ["project data the runtime ignores"],
        }
        loaded = load_compatibility_matrix(self.write_json("matrix.json", matrix, mode=0o644))
        self.assertEqual(loaded["sync_timer_unit"], TIMER)
        variants = {
            "wrong-contract": {**matrix, "contract_version": "company-delivery-compatibility/v2"},
            "missing-timer": {key: value for key, value in matrix.items() if key != "sync_timer_unit"},
            "malformed-timer": {**matrix, "sync_timer_unit": "aisoft-inbound-sync@x.service"},
            "sensitive": {**matrix, "token": "never-print-this-value"},
        }
        for name, value in variants.items():
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError):
                load_compatibility_matrix(self.write_json(f"matrix-{name}.json", value, mode=0o644))
        with self.assertRaises(CompanyDeliveryError):
            load_compatibility_matrix(self.write_json("array.json", [matrix], mode=0o644))

    def test_transition_verifier_cross_checks_sync_timer_with_handoff(self) -> None:
        transition_path, scm_path, appserver_path, handoff_path, package_path = (
            self.bound_transition_files(prefix="timer-ok")
        )
        self.assertEqual(
            verify_gitea_transition(
                transition_path, scm_path, appserver_path, handoff_path, package_path
            )["outcome"],
            "PASS",
        )
        # Same handoff, but the scm-ci host recorded a different timer instance.
        scm_value = self.inventory_v3()
        for unit in scm_value["units"]:
            if unit["name"].endswith(".timer"):
                unit["name"] = "aisoft-inbound-sync@other.timer"
        drifted_scm = self.write_json("timer-drift-scm.json", scm_value)
        transition = json.loads(transition_path.read_text(encoding="utf-8"))
        transition["inventories"]["scm_ci_sha256"] = sha256(drifted_scm)
        drifted_transition = self.write_json("timer-drift-transition.json", transition)
        with self.assertRaises(CompanyDeliveryError) as rejected:
            verify_gitea_transition(
                drifted_transition, drifted_scm, appserver_path, handoff_path, package_path
            )
        self.assertEqual(rejected.exception.code, "INVALID_CONTRACT")
        self.assertIn("sync timer", rejected.exception.safe_message)
        self.assertNotIn("other", rejected.exception.safe_message)

    def test_sync_timer_unit_resolves_only_from_a_verified_handoff(self) -> None:
        manifest = self.write_handoff_bundle("resolve", operator_version="1.3.0")
        self.assertEqual(sync_timer_unit_from_handoff(manifest), TIMER)
        with self.assertRaises(CompanyDeliveryError) as relative:
            sync_timer_unit_from_handoff(Path("relative/handoff-manifest.json"))
        self.assertEqual(relative.exception.code, "UNSAFE_PATH")
        legacy = self.write_handoff_bundle("resolve-legacy", operator_version="1.2.0")
        stripped = json.loads(legacy.read_text(encoding="utf-8"))
        stripped["compatibility"].pop("sync_timer_unit")
        legacy.write_text(json.dumps(stripped, sort_keys=True), encoding="utf-8")
        checksums = legacy.parent / "SHA256SUMS"
        lines = [
            line
            for line in checksums.read_text(encoding="ascii").splitlines()
            if not line.endswith("  handoff-manifest.json")
        ]
        lines.append(f"{sha256(legacy)}  handoff-manifest.json")
        checksums.write_text("".join(f"{line}\n" for line in sorted(lines)), encoding="ascii")
        with self.assertRaises(CompanyDeliveryError) as undeclared:
            sync_timer_unit_from_handoff(legacy)
        self.assertEqual(undeclared.exception.code, "INVALID_CONTRACT")
        tampered = self.write_handoff_bundle("resolve-tampered", operator_version="1.3.0")
        (tampered.parent / "operator/VERSION").write_text("9.9.9\n", encoding="ascii")
        with self.assertRaises(CompanyDeliveryError) as mismatch:
            sync_timer_unit_from_handoff(tampered)
        self.assertEqual(mismatch.exception.code, "CHECKSUM_MISMATCH")

    def test_inventory_v2_models_scm_greenfield_facts_without_raw_values(self) -> None:
        value = load_inventory(self.write_json("inventory-v2.json", self.inventory_v2()))
        self.assertEqual(value["mode"], "preflight")
        self.assertEqual(value["scm"]["legacy"]["presence"], "present")
        self.assertEqual(value["scm"]["candidate"]["ports"]["gitea_http"], "free")

        appserver = self.appserver_inventory_v2()
        self.assertIsNone(
            load_inventory(self.write_json("inventory-v2-appserver.json", appserver))["scm"]
        )

    def test_inventory_v2_role_mode_and_scm_enums_are_strict(self) -> None:
        variants: list[tuple[str, dict[str, object]]] = []
        appserver_with_scm = self.inventory_v2()
        appserver_with_scm["role"] = "appserver-prod"
        variants.append(("appserver-with-scm", appserver_with_scm))
        missing_mode = self.inventory_v2()
        missing_mode.pop("mode")
        variants.append(("missing-mode", missing_mode))
        wrong_port_state = self.inventory_v2()
        wrong_port_state["scm"]["candidate"]["ports"]["gitea_http"] = "available"
        variants.append(("wrong-port-state", wrong_port_state))
        raw_port = self.inventory_v2()
        raw_port["scm"]["legacy"]["publish_port"] = 3000
        variants.append(("raw-port", raw_port))
        wrong_baseline = self.inventory_v2()
        wrong_baseline["scm"]["legacy"]["baseline_sha256"] = "sha256:" + "9" * 64
        variants.append(("wrong-baseline", wrong_baseline))
        for name, value in variants:
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError):
                load_inventory(self.write_json(f"{name}.json", value))

    def test_inventory_v3_has_no_legacy_projection_and_rejects_legacy_fields(self) -> None:
        value = load_inventory(self.write_json("inventory-v3.json", self.inventory_v3()))
        self.assertEqual(value["scm"]["probe_profile"], "greenfield-isolated-install-v1")
        self.assertNotIn("legacy", value["scm"])

        injected = self.inventory_v3()
        injected["scm"]["legacy"] = {"health": "healthy"}
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(self.write_json("inventory-v3-legacy.json", injected))

    def test_transition_contract_locks_greenfield_stage_map_and_target(self) -> None:
        value = load_gitea_transition(self.write_json("transition.json", self.transition()))
        self.assertEqual(value["decision"], "greenfield-isolated-install")
        self.assertEqual(value["stages"]["30"], "NOT RUN")

        variants: list[tuple[str, dict[str, object]]] = []
        fake_backup = self.transition()
        fake_backup["stages"]["30"] = "PASS"
        variants.append(("fake-skipped-pass", fake_backup))
        drift = self.transition()
        drift["target"]["gitea_http"] = "127.0.0.1:3001"
        variants.append(("target-drift", drift))
        wrong_checksum = self.transition()
        wrong_checksum["inventories"]["scm_ci_sha256"] = "short"
        variants.append(("wrong-checksum", wrong_checksum))
        wrong_prerequisite = self.transition()
        wrong_prerequisite["prerequisites"]["legacy_backup_required"] = False
        variants.append(("wrong-prerequisite", wrong_prerequisite))
        unknown = self.transition()
        unknown["target"]["unexpected"] = "value"
        variants.append(("unknown-target-field", unknown))
        for name, transition in variants:
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError):
                load_gitea_transition(self.write_json(f"transition-{name}.json", transition))

    def test_current_transition_rejects_controlled_upgrade_and_legacy_prerequisites(self) -> None:
        controlled = self.transition(decision="controlled-upgrade-candidate")
        with self.assertRaises(CompanyDeliveryError):
            load_gitea_transition(self.write_json("controlled.json", controlled))

        legacy = self.transition()
        legacy["legacy_baseline_sha256"] = "sha256:" + DIGEST
        with self.assertRaises(CompanyDeliveryError):
            load_gitea_transition(self.write_json("legacy-field.json", legacy))

    def test_transition_verifier_cli_surface_is_explicit(self) -> None:
        args = build_parser().parse_args(
            [
                "verify-gitea-transition",
                "--input",
                str(self.root / "transition.json"),
                "--scm-inventory",
                str(self.root / "scm.json"),
                "--appserver-inventory",
                str(self.root / "appserver.json"),
                "--handoff-manifest",
                str(self.root / "handoff-manifest.json"),
                "--postgresql-package-manifest",
                str(self.root / "postgresql-packages.sha256"),
            ]
        )
        self.assertEqual(args.command, "verify-gitea-transition")
        self.assertEqual(args.handoff_manifest, self.root / "handoff-manifest.json")
        self.assertEqual(
            args.postgresql_package_manifest,
            self.root / "postgresql-packages.sha256",
        )
        for forbidden in ("--url", "--container-id", "--unit", "--command", "--credential"):
            with self.subTest(argument=forbidden), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                build_parser().parse_args(
                    [
                        "verify-gitea-transition",
                        "--input",
                        str(self.root / "transition.json"),
                        "--scm-inventory",
                        str(self.root / "scm.json"),
                        "--appserver-inventory",
                        str(self.root / "appserver.json"),
                        "--handoff-manifest",
                        str(self.root / "handoff-manifest.json"),
                        "--postgresql-package-manifest",
                        str(self.root / "postgresql-packages.sha256"),
                        forbidden,
                        "rejected",
                    ]
                )

    def test_transition_contract_requires_stage00_and_package_manifest_bindings(self) -> None:
        transition = self.transition()
        transition["handoff_manifest_sha256"] = "3" * 64
        transition["postgresql_package_manifest_sha256"] = "4" * 64
        value = load_gitea_transition(self.write_json("transition-bindings.json", transition))
        self.assertEqual(value["handoff_manifest_sha256"], "3" * 64)
        self.assertEqual(value["postgresql_package_manifest_sha256"], "4" * 64)

    def test_inventory_schema_pass_branches_use_explicit_properties(self) -> None:
        schema = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "company-delivery/schema/inventory-v3.schema.json"
            ).read_text(encoding="utf-8")
        )
        for branch_index in (3, 4):
            candidate = schema["allOf"][branch_index]["then"]["properties"]["scm"][
                "properties"
            ]["candidate"]["properties"]
            self.assertEqual(
                set(candidate["resources"]["properties"]),
                {
                    "gitea_binary",
                    "gitea_config",
                    "gitea_data",
                    "gitea_log",
                    "postgresql_data",
                },
            )
            self.assertEqual(
                set(candidate["services"]["properties"]),
                {"gitea", "postgresql"},
            )

    def test_protected_checksum_rejects_oversize_before_hashing(self) -> None:
        oversized = self.root / "oversized-inventory.json"
        oversized.write_bytes(b"0" * (contract_module.MAX_JSON_BYTES + 1))
        oversized.chmod(0o600)
        with mock.patch.object(contract_module, "sha256_file") as digest:
            with self.assertRaises(CompanyDeliveryError):
                contract_module._protected_file_sha256(oversized, "oversized inventory")
        digest.assert_not_called()

    def test_transition_verifier_binds_two_inventory_v3_files(self) -> None:
        transition_path, scm_path, appserver_path, handoff_path, package_path = (
            self.bound_transition_files()
        )
        value = verify_gitea_transition(
            transition_path,
            scm_path,
            appserver_path,
            handoff_path,
            package_path,
        )
        self.assertEqual(value["decision"], "greenfield-isolated-install")
        self.assertEqual(value["outcome"], "PASS")
        self.assertEqual(value["scm_inventory_sha256"], sha256(scm_path))
        self.assertEqual(value["handoff_manifest_sha256"], sha256(handoff_path))
        self.assertEqual(
            value["postgresql_package_manifest_sha256"],
            sha256(package_path),
        )

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "verify-gitea-transition",
                    "--input",
                    str(transition_path),
                    "--scm-inventory",
                    str(scm_path),
                    "--appserver-inventory",
                    str(appserver_path),
                    "--handoff-manifest",
                    str(handoff_path),
                    "--postgresql-package-manifest",
                    str(package_path),
                ]
            )
        self.assertEqual(result, 0)
        rendered = json.loads(stdout.getvalue())
        self.assertTrue(rendered["ok"])
        self.assertEqual(rendered["outcome"], "PASS")
        self.assertNotIn(str(scm_path), stdout.getvalue())

    def test_transition_verifier_rejects_1_1_0_inventory_reuse(self) -> None:
        for role in ("scm-ci", "appserver-prod"):
            with self.subTest(role=role):
                transition_path, scm_path, appserver_path, handoff_path, package_path = (
                    self.bound_transition_files(prefix=f"old-inventory-{role}")
                )
                target_path = scm_path if role == "scm-ci" else appserver_path
                inventory = json.loads(target_path.read_text(encoding="utf-8"))
                inventory["collector_version"] = "1.1.0"
                target_path.write_text(
                    json.dumps(inventory, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                transition = json.loads(transition_path.read_text(encoding="utf-8"))
                transition["inventories"][
                    "scm_ci_sha256" if role == "scm-ci" else "appserver_prod_sha256"
                ] = sha256(target_path)
                transition_path.write_text(
                    json.dumps(transition, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(CompanyDeliveryError) as caught:
                    verify_gitea_transition(
                        transition_path,
                        scm_path,
                        appserver_path,
                        handoff_path,
                        package_path,
                    )
                self.assertEqual(caught.exception.code, "INVALID_CONTRACT")

    def test_transition_verifier_rejects_handoff_source_version_and_package_drift(self) -> None:
        transition_path, scm_path, appserver_path, _handoff_path, package_path = (
            self.bound_transition_files(prefix="source-binding")
        )
        transition = json.loads(transition_path.read_text(encoding="utf-8"))

        wrong_source_handoff = self.write_handoff_bundle(
            "wrong-source",
            source_sha="9" * 40,
        )
        transition["handoff_manifest_sha256"] = sha256(wrong_source_handoff)
        wrong_source_transition = self.write_json(
            "wrong-source-transition.json",
            transition,
        )
        with self.assertRaises(CompanyDeliveryError) as source_error:
            verify_gitea_transition(
                wrong_source_transition,
                scm_path,
                appserver_path,
                wrong_source_handoff,
                package_path,
            )
        self.assertEqual(source_error.exception.code, "CHECKSUM_MISMATCH")

        old_handoff = self.write_handoff_bundle(
            "old-operator",
            operator_version="1.0.1",
        )
        transition["handoff_manifest_sha256"] = sha256(old_handoff)
        old_transition = self.write_json("old-operator-transition.json", transition)
        with self.assertRaises(CompanyDeliveryError) as version_error:
            verify_gitea_transition(
                old_transition,
                scm_path,
                appserver_path,
                old_handoff,
                package_path,
            )
        self.assertEqual(version_error.exception.code, "CHECKSUM_MISMATCH")

        package_transition, package_scm, package_app, package_handoff, package_manifest = (
            self.bound_transition_files(prefix="package-binding")
        )
        package_manifest.write_text(
            "6" * 64 + "  postgresql-client.pkg\n",
            encoding="ascii",
        )
        with self.assertRaises(CompanyDeliveryError) as package_error:
            verify_gitea_transition(
                package_transition,
                package_scm,
                package_app,
                package_handoff,
                package_manifest,
            )
        self.assertEqual(package_error.exception.code, "CHECKSUM_MISMATCH")

    def test_transition_verifier_rejects_invalid_package_manifest_content(self) -> None:
        invalid_manifests = {
            "empty": "",
            "malformed": "not-a-sha256-manifest\n",
            "duplicate": (
                "5" * 64
                + "  postgresql-client.pkg\n"
                + "5" * 64
                + "  postgresql-client.pkg\n"
            ),
            "unsorted": (
                "5" * 64
                + "  z-postgresql.pkg\n"
                + "6" * 64
                + "  a-postgresql.pkg\n"
            ),
            "unsafe-path": "5" * 64 + "  ../postgresql.pkg\n",
        }
        for name, content in invalid_manifests.items():
            with self.subTest(name=name):
                transition_path, scm_path, appserver_path, handoff_path, package_path = (
                    self.bound_transition_files(prefix=f"invalid-package-{name}")
                )
                package_path.write_text(content, encoding="ascii")
                transition = json.loads(transition_path.read_text(encoding="utf-8"))
                transition["postgresql_package_manifest_sha256"] = sha256(package_path)
                transition_path.write_text(json.dumps(transition), encoding="utf-8")
                with self.assertRaises(CompanyDeliveryError) as caught:
                    verify_gitea_transition(
                        transition_path,
                        scm_path,
                        appserver_path,
                        handoff_path,
                        package_path,
                    )
                self.assertEqual(caught.exception.code, "INVALID_CONTRACT")

    def test_transition_verifier_rejects_checksum_role_mode_and_outcome_drift(self) -> None:
        transition_path, scm_path, appserver_path, handoff_path, package_path = (
            self.bound_transition_files(prefix="checksum")
        )
        appserver_value = json.loads(appserver_path.read_text(encoding="utf-8"))
        appserver_path.write_text(
            json.dumps(appserver_value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(CompanyDeliveryError) as checksum_error:
            verify_gitea_transition(
                transition_path,
                scm_path,
                appserver_path,
                handoff_path,
                package_path,
            )
        self.assertEqual(checksum_error.exception.code, "CHECKSUM_MISMATCH")

        (
            wrong_role_transition,
            _wrong_scm,
            wrong_appserver,
            wrong_handoff,
            wrong_package,
        ) = self.bound_transition_files(prefix="wrong-role")
        transition = json.loads(wrong_role_transition.read_text(encoding="utf-8"))
        transition["inventories"]["scm_ci_sha256"] = sha256(wrong_appserver)
        wrong_role_transition.write_text(json.dumps(transition), encoding="utf-8")
        with self.assertRaises(CompanyDeliveryError):
            verify_gitea_transition(
                wrong_role_transition,
                wrong_appserver,
                wrong_appserver,
                wrong_handoff,
                wrong_package,
            )

        blocked_scm = self.inventory_v3()
        blocked_scm["outcome"] = "BLOCKED"
        blocked_scm["pending"] = ["CANDIDATE_PORT_STATE_GITEA_HTTP"]
        blocked_scm["scm"]["candidate"]["ports"]["gitea_http"] = "occupied"
        blocked_scm_path = self.write_json("blocked-scm.json", blocked_scm)
        blocked_transition = self.transition()
        blocked_transition["inventories"] = {
            "scm_ci_sha256": sha256(blocked_scm_path),
            "appserver_prod_sha256": sha256(wrong_appserver),
        }
        blocked_transition_path = self.write_json("blocked-transition.json", blocked_transition)
        with self.assertRaises(CompanyDeliveryError):
            verify_gitea_transition(
                blocked_transition_path,
                blocked_scm_path,
                wrong_appserver,
                wrong_handoff,
                wrong_package,
            )

    def test_legacy_health_verifier_accepts_only_greenfield_post_install_equality(self) -> None:
        post = self.post_install_inventory_v2()
        transition = self.legacy_transition()
        transition["legacy_baseline_sha256"] = post["scm"]["legacy"]["baseline_sha256"]
        transition_path = self.write_json("legacy-transition.json", transition)
        post_path = self.write_json("legacy-post.json", post)
        value = verify_legacy_health(transition_path, post_path)
        self.assertEqual(value["legacy_invariant"], "PASS")
        self.assertEqual(value["stages_30_40"], "NOT RUN")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "verify-legacy-health",
                    "--transition",
                    str(transition_path),
                    "--post-inventory",
                    str(post_path),
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(stdout.getvalue())["legacy_invariant"], "PASS")

        drift = self.post_install_inventory_v2()
        drift["scm"]["legacy"]["version"] = "1.26.3"
        drift["scm"]["legacy"]["baseline_sha256"] = legacy_baseline_sha256(
            drift["scm"]["legacy"]
        )
        drift_path = self.write_json("legacy-drift.json", drift)
        with self.assertRaises(CompanyDeliveryError) as drift_error:
            verify_legacy_health(transition_path, drift_path)
        self.assertEqual(drift_error.exception.code, "LEGACY_INVARIANT_FAILED")

        controlled = self.legacy_transition()
        controlled["decision"] = "controlled-upgrade-candidate"
        controlled["prerequisites"] = {
            "legacy_backup_required": True,
            "isolated_restore_required": True,
            "stage50_prerequisite": "stage-30-40-pass",
        }
        controlled_path = self.write_json("controlled-health.json", controlled)
        with self.assertRaises(CompanyDeliveryError):
            verify_legacy_health(controlled_path, post_path)

    def test_transition_cli_rejects_sensitive_tamper_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        transition_path, scm_path, appserver_path, handoff_path, package_path = (
            self.bound_transition_files(prefix="sensitive")
        )
        transition = json.loads(transition_path.read_text(encoding="utf-8"))
        transition["token"] = sentinel
        transition_path.write_text(json.dumps(transition), encoding="utf-8")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(
                [
                    "verify-gitea-transition",
                    "--input",
                    str(transition_path),
                    "--scm-inventory",
                    str(scm_path),
                    "--appserver-inventory",
                    str(appserver_path),
                    "--handoff-manifest",
                    str(handoff_path),
                    "--postgresql-package-manifest",
                    str(package_path),
                ]
            )
        self.assertEqual(result, 2)
        self.assertEqual(json.loads(stderr.getvalue())["error_code"], "SENSITIVE_CONTENT")
        self.assertNotIn(sentinel, stderr.getvalue())

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
            ("act_runner", "--version"): (0, "act_runner version v0.2.13\n", ""),
            ("docker", "version", "--format", "{{.Server.Version}}"): (0, "29.7.1\n", ""),
            ("docker", "compose", "version", "--short"): (0, "5.1.4\n", ""),
        }
        for unit in ("act_runner.service", "docker.service"):
            self.responses[("systemctl", "is-enabled", unit)] = (0, "enabled\n", "")
            self.responses[("systemctl", "is-active", unit)] = (0, "active\n", "")
        for unit in (
            "gitea.service",
            "aisoft-gitea.service",
            "postgresql@18-aisoft-gitea.service",
        ):
            self.responses[("systemctl", "is-enabled", unit)] = (4, "", "")
            self.responses[("systemctl", "is-active", unit)] = (4, "", "")
        self.responses[("systemctl", "is-enabled", TIMER)] = (1, "disabled\n", "")
        self.responses[("systemctl", "is-active", TIMER)] = (3, "inactive\n", "")
        self.port_calls: list[int] = []
        self.candidate_http_calls = 0
        # The real company scm-ci already has an unrelated application on 3000.
        # The greenfield Gitea contract must probe only its fixed 8888 target.
        self.port_states = {3000: "occupied", 8888: "free", 55432: "free"}
        self.resource_states: dict[Path, str] = {}

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

    def port_probe(self, port: int) -> str:
        self.port_calls.append(port)
        return self.port_states[port]

    def resource_probe(self, path: Path) -> str:
        return self.resource_states.get(path, "absent")

    def candidate_http_get(self) -> tuple[int, str] | None:
        self.candidate_http_calls += 1
        return (200, '{"version":"1.26.4"}')

    def collect_scm(
        self,
        output: Path,
        *,
        mode: str = "preflight",
        runner=None,
        candidate_http_get=None,
        port_probe=None,
        resource_probe=None,
    ) -> dict[str, object]:
        return collect_inventory(
            "scm-ci",
            output,
            mode=mode,
            sync_timer_unit=TIMER,
            runner=runner or self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-17T08:00:00Z",
            candidate_http_get=candidate_http_get or self.candidate_http_get,
            port_probe=port_probe or self.port_probe,
            resource_probe=resource_probe or self.resource_probe,
        )

    def test_scm_inventory_requires_typed_mode(self) -> None:
        with self.assertRaises(CompanyDeliveryError):
            collect_inventory(
                "scm-ci",
                self.root / "missing-scm-options.json",
                runner=self.runner,
                read_text=self.read_text,
                now=lambda: "2026-08-17T08:00:00Z",
            )

    def test_scm_inventory_uses_only_fixed_read_only_probes(self) -> None:
        output = self.root / "inventory.json"
        value = self.collect_scm(output)
        self.assertEqual(value["outcome"], "PASS")
        self.assertEqual(value["contract_version"], INVENTORY_V3_VERSION)
        self.assertEqual(value["mode"], "preflight")
        self.assertEqual(self.candidate_http_calls, 0)
        self.assertEqual(
            value["scm"]["probe_profile"], "greenfield-isolated-install-v1"
        )
        self.assertNotIn("legacy", value["scm"])
        self.assertEqual(self.port_calls, [8888, 55432])
        self.assertNotIn(3000, self.port_calls)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        parsed = load_inventory(output)
        rendered = output.read_text(encoding="utf-8")
        self.assertEqual(parsed["host"]["architecture"], "amd64")
        self.assertNotIn("company-scm-01", rendered)
        self.assertNotIn("machine-id-never-emitted", rendered)
        self.assertTrue(str(parsed["host"]["hostname_sha256"]).startswith("sha256:"))
        self.assertNotIn("aaaaaaaaaaaa", rendered)
        flattened = "\n".join(" ".join(command) for command in self.calls)
        for forbidden in (
            "docker ps",
            "docker inspect",
            "docker logs",
            "docker network",
            "docker volume",
            "curl",
            "ssh",
            "journalctl",
            " start ",
            " enable ",
            " restart ",
            " stop ",
        ):
            self.assertNotIn(forbidden, flattened)
        self.assertEqual(
            [item for item in parsed["units"] if item["name"].endswith(".timer")],
            [
                {
                    "name": TIMER,
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
        value = self.collect_scm(output)
        self.assertEqual(value["outcome"], "BLOCKED")
        gitea = next(item for item in value["tools"] if item["name"] == "gitea")
        self.assertEqual(gitea["status"], "BLOCKED")
        self.assertEqual(gitea["reason"], "sensitive-output-rejected")
        self.assertNotIn(sentinel, output.read_text(encoding="utf-8"))

    def test_missing_required_tool_probe_is_not_projected_as_pass(self) -> None:
        self.responses.pop(("git", "--version"))
        output = self.root / "missing-tool-inventory.json"
        value = self.collect_scm(output)
        self.assertEqual(value["outcome"], "BLOCKED")
        self.assertIn("TOOL_PROBE_MISSING_GIT", value["pending"])
        git = next(item for item in value["tools"] if item["name"] == "git")
        self.assertEqual(git["status"], "NOT RUN")
        self.assertEqual(git["reason"], "command-missing")

    def test_unrelated_semver_in_tool_error_banner_is_not_accepted(self) -> None:
        self.responses[("gitea", "--version")] = (
            0,
            "dependency 9.9.9 failed before Gitea version detection\n",
            "",
        )
        output = self.root / "wrong-banner-inventory.json"
        value = self.collect_scm(output)
        self.assertEqual(value["outcome"], "BLOCKED")
        gitea = next(item for item in value["tools"] if item["name"] == "gitea")
        self.assertEqual(gitea["status"], "BLOCKED")
        self.assertEqual(gitea["reason"], "version-output-unrecognized")

    def test_greenfield_inventory_never_probes_or_projects_legacy_gitea(self) -> None:
        output = self.root / "greenfield-only.json"
        value = self.collect_scm(output)
        rendered = output.read_text(encoding="utf-8")

        self.assertEqual(value["outcome"], "PASS")
        self.assertNotIn("legacy", value["scm"])
        self.assertNotIn("legacy", rendered.lower())
        self.assertFalse(any(command[:2] == ("docker", "ps") for command in self.calls))
        self.assertEqual(self.candidate_http_calls, 0)
        self.assertEqual(self.port_calls, [8888, 55432])

    def test_fixed_resource_probe_reports_state_without_names_or_contents(self) -> None:
        missing = self.root / "missing"
        empty = self.root / "empty"
        empty.mkdir()
        occupied_dir = self.root / "occupied"
        occupied_dir.mkdir()
        (occupied_dir / "do-not-render-this-name").write_text("content", encoding="utf-8")
        occupied_file = self.root / "binary"
        occupied_file.write_text("bytes", encoding="utf-8")
        link = self.root / "link"
        link.symlink_to(occupied_file)
        self.assertEqual(collector_module._resource_state(missing), "absent")
        self.assertEqual(collector_module._resource_state(empty), "expected-empty")
        self.assertEqual(collector_module._resource_state(occupied_dir), "occupied")
        self.assertEqual(collector_module._resource_state(occupied_file), "occupied")
        self.assertEqual(collector_module._resource_state(link), "unsafe")

    def test_candidate_port_resource_and_service_collisions_block_preflight(self) -> None:
        self.port_states[8888] = "occupied"
        candidate_binary = Path("/opt/aisoft/gitea/1.26.4/gitea")
        self.resource_states[candidate_binary] = "unsafe"
        self.responses[("systemctl", "is-enabled", "aisoft-gitea.service")] = (0, "enabled\n", "")
        self.responses[("systemctl", "is-active", "aisoft-gitea.service")] = (0, "active\n", "")
        output = self.root / "candidate-collision.json"
        value = self.collect_scm(output)
        self.assertEqual(value["outcome"], "BLOCKED")
        self.assertEqual(value["scm"]["candidate"]["ports"]["gitea_http"], "occupied")
        self.assertEqual(value["scm"]["candidate"]["resources"]["gitea_binary"], "unsafe")
        self.assertIn("CANDIDATE_PORT_STATE_GITEA_HTTP", value["pending"])
        self.assertIn("CANDIDATE_RESOURCE_STATE_GITEA_BINARY", value["pending"])
        self.assertIn("CANDIDATE_SERVICE_STATE_GITEA", value["pending"])

    def test_ubuntu_missing_units_and_safe_postgresql_template_pass_preflight(self) -> None:
        self.responses.pop(("act_runner", "--version"))
        for unit in (
            "act_runner.service",
            "gitea.service",
            TIMER,
            "aisoft-gitea.service",
        ):
            self.responses[("systemctl", "is-enabled", unit)] = (4, "not-found\n", "")
            self.responses[("systemctl", "is-active", unit)] = (3, "inactive\n", "")
        postgresql = "postgresql@18-aisoft-gitea.service"
        self.responses[("systemctl", "is-enabled", postgresql)] = (1, "disabled\n", "")
        self.responses[("systemctl", "is-active", postgresql)] = (3, "inactive\n", "")

        output = self.root / "ubuntu-systemd-preflight.json"
        value = self.collect_scm(output)

        self.assertEqual(value["outcome"], "PASS")
        tools = {item["name"]: item for item in value["tools"]}
        self.assertEqual(tools["act-runner"]["status"], "ABSENT")
        self.assertEqual(tools["gitea"]["status"], "ABSENT")
        units = {item["name"]: item for item in value["units"]}
        self.assertEqual(
            units[TIMER],
            {
                "name": TIMER,
                "enabled": "not-found",
                "active": "not-found",
            },
        )
        self.assertEqual(
            value["scm"]["candidate"]["services"],
            {
                "gitea": {"enabled": "not-found", "active": "not-found"},
                "postgresql": {"enabled": "disabled", "active": "inactive"},
            },
        )

    def test_unsafe_candidate_unit_pairs_remain_blocked(self) -> None:
        variants = (
            ("gitea-disabled", "aisoft-gitea.service", "disabled", "inactive", "gitea"),
            (
                "postgresql-masked",
                "postgresql@18-aisoft-gitea.service",
                "masked",
                "inactive",
                "postgresql",
            ),
            (
                "postgresql-active",
                "postgresql@18-aisoft-gitea.service",
                "disabled",
                "active",
                "postgresql",
            ),
        )
        for name, unit, enabled, active, resource in variants:
            with self.subTest(name=name):
                self.responses[("systemctl", "is-enabled", unit)] = (0, enabled + "\n", "")
                self.responses[("systemctl", "is-active", unit)] = (0, active + "\n", "")
                output = self.root / f"unsafe-unit-{name}.json"
                value = self.collect_scm(output)
                self.assertEqual(value["outcome"], "BLOCKED")
                self.assertIn(
                    "CANDIDATE_SERVICE_STATE_" + resource.upper(),
                    value["pending"],
                )

    def test_post_install_mode_requires_only_fixed_candidate_state(self) -> None:
        self.port_states = {3000: "occupied", 8888: "occupied", 55432: "occupied"}
        for unit in ("aisoft-gitea.service", "postgresql@18-aisoft-gitea.service"):
            self.responses[("systemctl", "is-enabled", unit)] = (0, "enabled\n", "")
            self.responses[("systemctl", "is-active", unit)] = (0, "active\n", "")
        output = self.root / "post-install.json"
        value = self.collect_scm(
            output,
            mode="post-install",
            resource_probe=lambda _path: "occupied",
        )
        self.assertEqual(value["outcome"], "PASS")
        self.assertEqual(value["mode"], "post-install")
        self.assertEqual(self.candidate_http_calls, 1)
        self.assertEqual(
            value["scm"]["candidate"]["health"],
            {"status": "healthy", "version": "1.26.4", "reason": None},
        )
        self.assertNotIn("legacy", value["scm"])
        self.assertEqual(
            value["scm"]["candidate"]["services"]["postgresql"],
            {"enabled": "enabled", "active": "active"},
        )

    def test_post_install_candidate_health_is_fixed_bounded_and_no_echo(self) -> None:
        self.port_states = {3000: "occupied", 8888: "occupied", 55432: "occupied"}
        for unit in ("aisoft-gitea.service", "postgresql@18-aisoft-gitea.service"):
            self.responses[("systemctl", "is-enabled", unit)] = (0, "enabled\n", "")
            self.responses[("systemctl", "is-active", unit)] = (0, "active\n", "")
        sentinel = "never-print-this-candidate-secret"
        variants = (
            ("legacy-version", lambda: (200, '{"version":"1.26.3"}'), "version-mismatch"),
            ("unavailable", lambda: (503, "service unavailable"), "http-status-5xx"),
            ("sensitive", lambda: (200, f'{{"version":"1.26.4","token":"{sentinel}"}}'), "sensitive-output-rejected"),
            ("duplicate", lambda: (200, '{"version":"1.26.4","version":"9.9.9"}'), "response-invalid"),
        )
        for name, getter, reason in variants:
            output = self.root / f"candidate-health-{name}.json"
            with self.subTest(name=name):
                value = self.collect_scm(
                    output,
                    mode="post-install",
                    candidate_http_get=getter,
                    resource_probe=lambda _path: "occupied",
                )
                rendered = output.read_text(encoding="utf-8")
                self.assertEqual(value["outcome"], "BLOCKED")
                self.assertEqual(value["scm"]["candidate"]["health"]["reason"], reason)
                for raw in (sentinel, "service unavailable", "9.9.9"):
                    self.assertNotIn(raw, rendered)
                self.assertNotIn("legacy", rendered.lower())

    def test_legacy_port_option_is_removed_and_mode_is_rejected_for_appserver(self) -> None:
        args = build_parser().parse_args(
            [
                "collect-inventory",
                "--role",
                "scm-ci",
                "--mode",
                "preflight",
                "--output",
                str(self.root / "typed.json"),
            ]
        )
        self.assertEqual(args.mode, "preflight")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build_parser().parse_args(
                [
                    "collect-inventory",
                    "--role",
                    "scm-ci",
                    "--mode",
                    "preflight",
                    "--legacy-gitea-http-port",
                    "8080",
                    "--output",
                    str(self.root / "rejected.json"),
                ]
            )
        with self.assertRaises(CompanyDeliveryError):
            collect_inventory(
                "appserver-prod",
                self.root / "appserver-with-scm-options.json",
                mode="preflight",
                runner=self.runner,
                read_text=self.read_text,
            )
        with self.assertRaises(CompanyDeliveryError) as timer_rejected:
            collect_inventory(
                "appserver-prod",
                self.root / "appserver-with-timer.json",
                sync_timer_unit=TIMER,
                runner=self.runner,
                read_text=self.read_text,
            )
        self.assertEqual(timer_rejected.exception.code, "INVALID_ARGUMENT")

    def test_scm_inventory_records_the_declared_sync_timer_instance(self) -> None:
        # #239: the timer instance is project data. Any allowlisted instance
        # name is collected verbatim; a missing or malformed name never falls
        # back to a runtime default.
        other = "aisoft-inbound-sync@other-project.timer"
        self.responses[("systemctl", "is-enabled", other)] = (1, "disabled\n", "")
        self.responses[("systemctl", "is-active", other)] = (3, "inactive\n", "")
        value = collect_inventory(
            "scm-ci",
            self.root / "other-timer.json",
            mode="preflight",
            sync_timer_unit=other,
            runner=self.runner,
            read_text=self.read_text,
            now=lambda: "2026-08-17T08:00:00Z",
            candidate_http_get=self.candidate_http_get,
            port_probe=self.port_probe,
            resource_probe=self.resource_probe,
        )
        self.assertEqual(value["outcome"], "PASS")
        timers = [item["name"] for item in value["units"] if item["name"].endswith(".timer")]
        self.assertEqual(timers, [other])
        self.assertNotIn(("systemctl", "is-enabled", TIMER), self.calls)
        for name in (None, "", "aisoft-inbound-sync@.timer", "docker.service", "../x.timer"):
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError) as rejected:
                collect_inventory(
                    "scm-ci",
                    self.root / f"bad-timer-{abs(hash(name))}.json",
                    mode="preflight",
                    sync_timer_unit=name,
                    runner=self.runner,
                    read_text=self.read_text,
                )
            self.assertEqual(rejected.exception.code, "INVALID_ARGUMENT")

    def test_tool_present_with_missing_unit_is_blocked_before_write(self) -> None:
        self.responses[("gitea", "--version")] = (
            0,
            "Gitea version 1.26.4 built with GNU Make\n",
            "",
        )
        output = self.root / "tool-unit-conflict.json"
        value = self.collect_scm(output)
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
            now=lambda: "2026-08-17T08:00:00Z",
        )
        self.assertEqual(value["outcome"], "PASS")
        versions = {item["name"]: item["version"] for item in value["tools"]}
        self.assertEqual(versions["nginx"], "1.30.4")
        self.assertEqual(versions["postgresql-client"], "18.4.0")
        self.assertNotIn(("gitea", "--version"), self.calls)
        self.assertNotIn(("act_runner", "--version"), self.calls)
        self.assertIsNone(value["mode"])
        self.assertIsNone(value["scm"])
        self.assertEqual(
            [item["name"] for item in value["units"]],
            ["docker.service", "nginx.service", "postgresql.service"],
        )

    def test_output_must_be_new_and_parent_mode_0700(self) -> None:
        output = self.root / "inventory.json"
        output.write_text("existing", encoding="utf-8")
        with self.assertRaises(CompanyDeliveryError):
            self.collect_scm(output)
        output.unlink()
        self.root.chmod(0o755)
        with self.assertRaises(CompanyDeliveryError):
            self.collect_scm(output)


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
        # #239: the compatibility matrix is caller-supplied project data that
        # lives outside the platform repository.
        self.matrix = self.write_matrix("compatibility-matrix.example.json")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_matrix(
        self,
        name: str,
        *,
        sync_timer_unit: str | None = TIMER,
        contract_version: str = "company-delivery-compatibility/v1",
        mode: int = 0o644,
    ) -> Path:
        value: dict[str, object] = {
            "contract_version": contract_version,
            "matrix_revision": "test",
            "topology": {"company_vm_count": 2},
        }
        if sync_timer_unit is not None:
            value["sync_timer_unit"] = sync_timer_unit
        path = self.root / name
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        path.chmod(mode)
        return path

    def output_dir(self, name: str) -> Path:
        path = self.root / name
        path.mkdir(mode=0o700)
        return path

    def build(self, output: Path, *, compatibility_matrix: Path | None = None) -> dict[str, object]:
        return build_bundle(
            repository_root=self.source,
            source_sha=self.source_sha,
            release_root=self.release_root,
            release_id=SHA_A,
            output_directory=output,
            created_at="2026-08-16T08:00:00Z",
            source_transport="approved-bundle",
            compatibility_matrix=compatibility_matrix or self.matrix,
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

    def test_restrictive_umask_preserves_allowlisted_payload_modes(self) -> None:
        previous_umask = os.umask(0o077)
        try:
            built = self.build(self.output_dir("out-restrictive-umask"))
        finally:
            os.umask(previous_umask)
        executable = (
            Path(built["bundle_root"])
            / "operator/bin/aisoft-company-delivery"
        )
        self.assertEqual(stat.S_IMODE(executable.stat().st_mode), 0o755)

    def test_operator_version_and_handoff_contract_remain_compatible(self) -> None:
        built = self.build(self.output_dir("out-version-contract"))
        manifest = load_handoff(
            Path(built["bundle_root"]) / "handoff-manifest.json",
            bundle_root=Path(built["bundle_root"]),
        )
        self.assertEqual(manifest["operator_version"], "1.3.0")
        self.assertEqual(
            (self.repository_root / "company-delivery/VERSION").read_text(encoding="ascii").strip(),
            "1.3.0",
        )
        self.assertEqual(contract_module.OPERATOR_VERSION, "1.3.0")
        self.assertTrue(str(built["archive_name"]).startswith("aisoft-company-delivery-1.3.0-"))
        self.assertEqual(manifest["contract_version"], HANDOFF_VERSION)
        self.assertEqual(HANDOFF_VERSION, "company-delivery-handoff/v1")
        self.assertEqual(manifest["compatibility"]["sync_timer_unit"], TIMER)

    def test_builder_carries_the_callers_matrix_and_binds_no_project_path(self) -> None:
        # #239: the matrix path and the timer unit are declared by the
        # caller's matrix; the runtime holds no project-specific constant.
        self.assertFalse(hasattr(bundle_module, "COMPATIBILITY_PATH"))
        package = self.repository_root / "codex/runtime/aisoft_company_delivery"
        for source in sorted(package.glob("*.py")):
            with self.subTest(module=source.name):
                text = source.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"aisoft-inbound-sync@[A-Za-z0-9]", text))
                self.assertNotIn("operator/compatibility/", text.replace(
                    'COMPATIBILITY_DIRECTORY = "operator/compatibility"', ""
                ))
        self.assertFalse(any(name.endswith(".timer") for names in contract_module.ROLE_UNIT_NAMES.values() for name in names))

        other = self.write_matrix(
            "project-matrix.json", sync_timer_unit="aisoft-inbound-sync@other-project.timer"
        )
        built = self.build(self.output_dir("out-other-matrix"), compatibility_matrix=other)
        bundle = Path(built["bundle_root"])
        carried = bundle / "operator/compatibility/project-matrix.json"
        self.assertEqual(carried.read_bytes(), other.read_bytes())
        self.assertEqual(stat.S_IMODE(carried.stat().st_mode), 0o644)
        manifest = load_handoff(bundle / "handoff-manifest.json", bundle_root=bundle)
        self.assertEqual(
            manifest["compatibility"],
            {
                "matrix_path": "operator/compatibility/project-matrix.json",
                "matrix_sha256": sha256(other),
                "required_roles": ["scm-ci", "appserver-prod"],
                "sync_timer_unit": "aisoft-inbound-sync@other-project.timer",
            },
        )
        self.assertIn(
            "operator/compatibility/project-matrix.json",
            [item["path"] for item in manifest["payloads"]],
        )
        self.assertTrue(verify_bundle(bundle / "handoff-manifest.json", bundle)["ok"])
        # Same inputs, same matrix bytes: still byte-identical.
        again = self.build(self.output_dir("out-other-matrix-again"), compatibility_matrix=other)
        self.assertEqual(again["archive_sha256"], built["archive_sha256"])
        # Different matrix bytes change the handoff identity.
        self.assertNotEqual(
            self.build(self.output_dir("out-default-matrix"))["archive_sha256"],
            built["archive_sha256"],
        )

    def test_builder_rejects_unusable_matrix_before_output(self) -> None:
        rejected: dict[str, tuple[Path, str]] = {
            "relative": (Path("relative/matrix.json"), "UNSAFE_PATH"),
            "missing": (self.root / "missing.json", "UNSAFE_PATH"),
            "not-json-name": (self.write_matrix("matrix.txt"), "UNSAFE_PATH"),
            "unsafe-name": (self.write_matrix(".hidden.json"), "UNSAFE_PATH"),
            "wrong-contract": (
                self.write_matrix("wrong.json", contract_version="company-delivery-compatibility/v2"),
                "INVALID_CONTRACT",
            ),
            "missing-timer": (self.write_matrix("untimed.json", sync_timer_unit=None), "INVALID_CONTRACT"),
            "malformed-timer": (
                self.write_matrix("malformed.json", sync_timer_unit="aisoft-inbound-sync@.timer"),
                "INVALID_CONTRACT",
            ),
            "unsafe-mode": (self.write_matrix("wide.json", mode=0o666), "UNSAFE_MODE"),
        }
        link = self.root / "linked.json"
        link.symlink_to(self.matrix.name)
        rejected["symlink"] = (link, "UNSAFE_PATH")
        for name, (matrix, code) in rejected.items():
            output = self.output_dir(f"out-matrix-{name}")
            with self.subTest(name=name), self.assertRaises(CompanyDeliveryError) as caught:
                self.build(output, compatibility_matrix=matrix)
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(list(output.iterdir()), [])

        # A matrix whose basename collides with a tracked operator file is refused.
        tracked = self.source / "company-delivery/compatibility/collide.json"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_text(json.dumps({"contract_version": "x"}) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "collide"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        colliding = self.write_matrix("collide.json")
        output = self.output_dir("out-matrix-collide")
        with self.assertRaises(CompanyDeliveryError) as caught:
            self.build(output, compatibility_matrix=colliding)
        self.assertEqual(caught.exception.code, "SOURCE_INVALID")
        self.assertEqual(list(output.iterdir()), [])

    def test_cli_requires_matrix_for_build_and_handoff_for_scm_collection(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build_parser().parse_args(
                [
                    "build-bundle",
                    "--repository-root", str(self.source),
                    "--source-sha", self.source_sha,
                    "--release-root", str(self.release_root),
                    "--release-id", SHA_A,
                    "--output-directory", str(self.root / "cli-out"),
                    "--created-at", "2026-08-16T08:00:00Z",
                    "--source-transport", "approved-bundle",
                ]
            )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "build-bundle",
                    "--repository-root", str(self.source),
                    "--source-sha", self.source_sha,
                    "--release-root", str(self.release_root),
                    "--release-id", SHA_A,
                    "--output-directory", str(self.output_dir("cli-out")),
                    "--created-at", "2026-08-16T08:00:00Z",
                    "--source-transport", "approved-bundle",
                    "--compatibility-matrix", str(self.matrix),
                ]
            )
        self.assertEqual(result, 0)
        rendered = json.loads(stdout.getvalue())
        self.assertTrue(rendered["ok"])
        self.assertTrue(str(rendered["bundle_name"]).startswith("aisoft-company-delivery-1.3.0-"))
        manifest = self.root / "cli-out" / str(rendered["bundle_name"]) / "handoff-manifest.json"

        captured: dict[str, object] = {}

        def fake_collect(role, output, *, mode=None, sync_timer_unit=None):
            captured.update({"role": role, "mode": mode, "sync_timer_unit": sync_timer_unit})
            return {"contract_version": INVENTORY_V3_VERSION}

        with mock.patch("aisoft_company_delivery.cli.collect_inventory", fake_collect):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "collect-inventory",
                            "--role", "scm-ci",
                            "--mode", "preflight",
                            "--output", str(self.root / "cli-scm.json"),
                            "--handoff-manifest", str(manifest),
                        ]
                    ),
                    0,
                )
        self.assertEqual(captured, {"role": "scm-ci", "mode": "preflight", "sync_timer_unit": TIMER})

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(
                main(
                    [
                        "collect-inventory",
                        "--role", "appserver-prod",
                        "--output", str(self.root / "cli-appserver.json"),
                        "--handoff-manifest", str(manifest),
                    ]
                ),
                2,
            )
        self.assertEqual(json.loads(stderr.getvalue())["error_code"], "INVALID_ARGUMENT")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(
                main(
                    [
                        "collect-inventory",
                        "--role", "scm-ci",
                        "--mode", "preflight",
                        "--output", str(self.root / "cli-scm-undeclared.json"),
                    ]
                ),
                2,
            )
        self.assertEqual(json.loads(stderr.getvalue())["error_code"], "INVALID_ARGUMENT")
        self.assertFalse((self.root / "cli-scm-undeclared.json").exists())

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
                compatibility_matrix=self.matrix,
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
                compatibility_matrix=self.matrix,
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

    def test_sensitive_operator_is_rejected_but_verified_image_is_opaque(self) -> None:
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

        release_dir = self.release_root / SHA_A
        archive = release_dir / "images.tar"
        manifest = json.loads(
            (release_dir / "release.json").read_text(encoding="utf-8")
        )
        create_archive(
            archive,
            manifest["images"],
            layer_files=[("etc/app.env", f"password={sentinel}\n".encode())],
        )
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
        built = self.build(self.output_dir("out-opaque-archive"))
        result = verify_bundle(
            Path(built["bundle_root"]) / "handoff-manifest.json",
            Path(built["bundle_root"]),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["docker_calls"], 0)
        self.assertEqual(result["target_facts"], "NOT_READ")

    def test_top_level_scan_distinguishes_material_from_incomplete_examples(self) -> None:
        source_fixture = (
            self.source / "company-delivery/scanner-source-example.txt"
        )
        source_fixture.write_text(
            "-----BEGIN PRIVATE KEY-----\n"
            "Authorization: Bearer example-placeholder\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", str(source_fixture)], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "safe source fixture"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        built = self.build(self.output_dir("out-safe-incomplete-source"))
        self.assertTrue(
            verify_bundle(
                Path(built["bundle_root"]) / "handoff-manifest.json",
                Path(built["bundle_root"]),
            )["ok"]
        )

        header = base64.urlsafe_b64encode(
            b'{"alg":"HS256","typ":"JWT"}'
        ).rstrip(b"=")
        payload = base64.urlsafe_b64encode(
            b'{"sub":"synthetic-test"}'
        ).rstrip(b"=")
        signature = base64.urlsafe_b64encode(b"x" * 32).rstrip(b"=")
        token = b".".join((header, payload, signature)).decode("ascii")
        source_fixture.write_text(token + "\n", encoding="ascii")
        subprocess.run(["git", "add", str(source_fixture)], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "credential fixture"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        with self.assertRaises(CompanyDeliveryError) as caught:
            self.build(self.output_dir("out-sensitive-top-level-jwt"))
        self.assertEqual(caught.exception.code, "SENSITIVE_CONTENT")
        self.assertNotIn(token, str(caught.exception))

    def test_oversized_top_level_payload_fails_closed_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        source_fixture = self.source / "company-delivery/oversized-payload.txt"
        source_fixture.write_bytes(
            b"x" * secret_scan_module.MAX_JSON_BYTES
            + f"\npassword={sentinel}\n".encode("ascii")
        )
        subprocess.run(["git", "add", str(source_fixture)], cwd=self.source, check=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "oversized fixture"],
            cwd=self.source,
            check=True,
        )
        self.source_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.source, text=True
        ).strip()
        output = self.output_dir("out-oversized-top-level")
        with self.assertRaises(CompanyDeliveryError) as caught:
            self.build(output)
        self.assertEqual(caught.exception.code, "SENSITIVE_SCAN_BLOCKED")
        self.assertNotIn(sentinel, str(caught.exception))
        self.assertEqual(list(output.iterdir()), [])

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
                        compatibility_matrix=self.matrix,
                    )
                self.assertEqual(caught.exception.code, "ARTIFACT_INVALID")


class CompanyDeliveryArchiveScannerTests(unittest.TestCase):
    setUp = CompanyDeliveryBundleTests.setUp
    write_matrix = CompanyDeliveryBundleTests.write_matrix
    tearDown = CompanyDeliveryBundleTests.tearDown
    output_dir = CompanyDeliveryBundleTests.output_dir

    def build(self, output: Path) -> dict[str, object]:
        """Exercise the optional deep scanner without making it a handoff gate."""

        files = bundle_module._verified_release(
            self.release_root,
            SHA_A,
            bundle_module._utc_today(),
        )
        graph = bundle_module._verified_archive_graph(files)
        secret_scan_module.scan_image_archive(files.archive_path, graph)
        return CompanyDeliveryBundleTests.build(self, output)

    def replace_archive(
        self,
        *,
        layer_files: list[tuple[str, bytes]] | None = None,
        layer_archive_payload: bytes | None = None,
        config_environment: list[str] | None = None,
    ) -> None:
        release_dir = self.release_root / SHA_A
        archive = release_dir / "images.tar"
        manifest = json.loads(
            (release_dir / "release.json").read_text(encoding="utf-8")
        )
        create_archive(
            archive,
            manifest["images"],
            layer_files=layer_files,
            layer_archive_payload=layer_archive_payload,
            config_environment=config_environment,
        )
        inventory_path = release_dir / "images.inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["archive_sha256"] = sha256(archive)
        inventory_path.write_text(
            json.dumps(
                inventory,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        update_manifest(
            release_dir,
            lambda value: value["offline_bundle"].update(
                {
                    "archive_sha256": sha256(archive),
                    "inventory_sha256": sha256(inventory_path),
                }
            ),
        )

    def assert_bundle_error(self, code: str, output_name: str) -> CompanyDeliveryError:
        output = self.output_dir(output_name)
        with self.assertRaises(CompanyDeliveryError) as caught:
            self.build(output)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(list(output.iterdir()), [])
        return caught.exception

    def test_verified_graph_is_scanned_without_docker(self) -> None:
        self.replace_archive(
            layer_files=[
                (
                    "src/schema.json",
                    b'{"properties":{"password":{"type":"string"}}}\n',
                ),
                ("src/example.js", b"const password = input;\n"),
                ("src/block.js", b"{ function fixture() { return true; } }\n"),
                (
                    "src/object.js",
                    b'{"handler": function () { return true; }}\n',
                ),
                ("src/array.js", b'{"items": [fixture, other]}\n'),
                ("src/trailing.jsonc", b'{"safe": true,}\n'),
                ("etc/service.conf", b"[Unit]\nDescription=fixture\n"),
                ("bin/app", b"\x00\x7fELF\x00ordinary-binary\xff"),
            ]
        )
        built = self.build(self.output_dir("out-safe-archive"))
        result = verify_bundle(
            Path(built["bundle_root"]) / "handoff-manifest.json",
            Path(built["bundle_root"]),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["docker_calls"], 0)
        self.assertEqual(result["target_facts"], "NOT_READ")

    def test_image_config_and_layer_secrets_are_rejected_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        self.replace_archive(config_environment=[f"PASSWORD={sentinel}"])
        config_error = self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-sensitive-config"
        )
        self.assertNotIn(sentinel, str(config_error))

        self.replace_archive(
            layer_files=[("etc/app.env", f"PASSWORD={sentinel}\n".encode())]
        )
        layer_error = self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-sensitive-layer"
        )
        self.assertNotIn(sentinel, str(layer_error))

        self.replace_archive(
            layer_files=[
                (
                    "etc/app.conf",
                    b"[database]\n"
                    b"database_url="
                    b"postgres://example:placeholder@localhost/db\n",
                )
            ]
        )
        self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-sensitive-layer-yaml"
        )

        self.replace_archive(
            layer_files=[("ambiguous-config", b"password: concrete-value\n")]
        )
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-ambiguous-runtime-text"
        )

    def test_material_aware_byte_signatures_cross_chunk_without_echo(self) -> None:
        pem_header = b"-----BEGIN PRIVATE KEY-----"
        encoded = base64.b64encode(b"fixture-private-key-material" * 4)
        pem_material = (
            pem_header + b"\n" + encoded + b"\n-----END PRIVATE KEY-----"
        )
        payload = b"\x00" * (1024 * 1024 - 10) + pem_material + b"\x00"
        self.replace_archive(layer_files=[("bin/payload", payload)])
        caught = self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-sensitive-binary"
        )
        self.assertNotIn(pem_header.decode("ascii"), str(caught))

        self.replace_archive(
            layer_files=[
                (
                    "bin/source-signatures",
                    b"\x00-----BEGIN PRIVATE KEY-----\x00"
                    b"Authorization: Bearer example-placeholder\x00"
                    b"Authorization: Basic\x00"
                    b"postgres://example:placeholder@localhost/db\x00"
                    b"postgres://localhost/example\x00"
                    b"abcdefgh.ijklmnop.qrstuvwxyz012345\x00",
                ),
                (
                    "source-regex",
                    b"password: ^(?=.*[A-Z])(?=.*\\d).{12,}$\n",
                ),
            ]
        )
        built = self.build(self.output_dir("out-safe-source-signatures"))
        self.assertTrue(
            verify_bundle(
                Path(built["bundle_root"]) / "handoff-manifest.json",
                Path(built["bundle_root"]),
            )["ok"]
        )

        for name, signature in (
            ("known-token", b"ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"),
            (
                "authorization-block",
                b"Authorization: Bearer concrete-value",
            ),
            (
                "authorization-basic-block",
                b"Authorization: Basic Y29uY3JldGU6dmFsdWU=",
            ),
            (
                "credential-url-userinfo",
                b"postgres://service:concrete-value@db.invalid/app",
            ),
            (
                "https-credential-url-userinfo",
                b"https://service:concrete-value@example.invalid/app",
            ),
            (
                "jwt-material",
                b"Authorization: Bearer "
                b"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaXh0dXJlIn0."
                b"YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYQ",
            ),
        ):
            with self.subTest(name=name):
                self.replace_archive(layer_files=[("bin/payload", signature)])
                self.assert_bundle_error(
                    "SENSITIVE_CONTENT", f"out-sensitive-{name}"
                )

        incomplete = pem_header + b"\n" + encoded
        self.replace_archive(layer_files=[("source-incomplete-pem", incomplete)])
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-ambiguous-incomplete-pem"
        )

        invalid_complete = (
            pem_header
            + b"\n"
            + b"not-valid-base64-material" * 2
            + b"\n-----END PRIVATE KEY-----"
        )
        self.replace_archive(layer_files=[("source-invalid-pem", invalid_complete)])
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-ambiguous-invalid-pem"
        )

        escaped_pem = json.dumps(
            {"example": pem_material.decode("ascii")},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.replace_archive(layer_files=[("source-json", escaped_pem)])
        self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-sensitive-decoded-pem"
        )

    def test_json_context_rejects_runtime_material_and_blocks_ambiguity(self) -> None:
        safe_documents = (
            b'{"$schema":"https://example.invalid/schema",'
            b'"properties":{"password":{"type":"string"}}}\n',
            b'{"locale":"en","messages":{"password":"Password"}}\n',
            b'{"kind":"source",'
            b'"source":{'
            b'"authorization":"Basic",'
            b'"database_url":"postgres://localhost/example",'
            b'"password":"^(?=.*[A-Z])(?=.*\\\\d).{12,}$"}}\n',
            b'{"name":"fixture","lockfileVersion":3,"packages":{'
            b'"":{"password":"example-placeholder"}}}\n',
            b'{"name":"fixture","version":"1.0.0","scripts":{'
            b'"password":"example-placeholder"}}\n',
        )
        self.replace_archive(
            layer_files=[
                (f"safe-{index}", payload)
                for index, payload in enumerate(safe_documents)
            ]
        )
        built = self.build(self.output_dir("out-safe-json-contexts"))
        self.assertTrue(
            verify_bundle(
                Path(built["bundle_root"]) / "handoff-manifest.json",
                Path(built["bundle_root"]),
            )["ok"]
        )

        runtime_values = {
            "authorization": "Bearer example-placeholder",
            "database_url": "postgres://example:placeholder@localhost/db",
            "password": "example-placeholder",
        }
        for key, value in runtime_values.items():
            with self.subTest(runtime_key=key):
                payload = json.dumps(
                    {"runtime": {key: value}},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                self.replace_archive(layer_files=[("runtime-config", payload)])
                self.assert_bundle_error(
                    "SENSITIVE_CONTENT", f"out-runtime-json-{key}"
                )

        self.replace_archive(
            layer_files=[("ambiguous-json", b'{"password":"example"}\n')]
        )
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-ambiguous-json-context"
        )

        self.replace_archive(
            layer_files=[
                (
                    "source-ambiguous-json",
                    b'{"kind":"source","source":{'
                    b'"password":"concrete-value"}}\n',
                )
            ]
        )
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-ambiguous-source-json"
        )

        for name, payload in (
            (
                "source-authorization",
                b'{"kind":"source","source":{'
                b'"authorization":"Bearer concrete-value"}}\n',
            ),
            (
                "source-basic-authorization",
                b'{"kind":"source","source":{'
                b'"authorization":"Basic Y29uY3JldGU6dmFsdWU="}}\n',
            ),
            (
                "source-userinfo",
                b'{"kind":"source","source":{'
                b'"database_url":"https://service:concrete-value@example.invalid/app"}}\n',
            ),
        ):
            with self.subTest(source_material=name):
                self.replace_archive(layer_files=[("source-json", payload)])
                self.assert_bundle_error(
                    "SENSITIVE_CONTENT", f"out-{name}"
                )

    def test_package_metadata_maps_are_source_but_runtime_and_material_block(self) -> None:
        safe_package = {
            "name": "fixture",
            "version": "1.0.0",
            "scripts": {
                "generate-token": "node tools/generate-token.js",
            },
            "dependencies": {
                "auth-token": "1.2.3",
                "credential-provider": "4.5.6",
            },
        }
        self.replace_archive(
            layer_files=[
                (
                    "package-metadata",
                    json.dumps(
                        safe_package, sort_keys=True, separators=(",", ":")
                    ).encode("utf-8"),
                )
            ]
        )
        built = self.build(self.output_dir("out-safe-package-metadata"))
        self.assertTrue(
            verify_bundle(
                Path(built["bundle_root"]) / "handoff-manifest.json",
                Path(built["bundle_root"]),
            )["ok"]
        )

        pem_body = base64.b64encode(b"package-private-key-material" * 4)
        pem_material = (
            b"-----BEGIN PRIVATE KEY-----\n"
            + pem_body
            + b"\n-----END PRIVATE KEY-----"
        ).decode("ascii")
        material_values = {
            "known-token": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
            "valid-pem": pem_material,
            "credential-url": (
                "https://service:concrete-value@example.invalid/app"
            ),
            "authorization": "Authorization: Bearer concrete-value",
        }
        for name, material in material_values.items():
            with self.subTest(material=name):
                payload = dict(safe_package)
                payload["scripts"] = {"generate-token": material}
                self.replace_archive(
                    layer_files=[
                        (
                            "package-metadata",
                            json.dumps(
                                payload,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8"),
                        )
                    ]
                )
                caught = self.assert_bundle_error(
                    "SENSITIVE_CONTENT", f"out-package-{name}"
                )
                self.assertNotIn(material, str(caught))

        runtime_payload = dict(safe_package)
        runtime_payload["config"] = {"password": "runtime-concrete-value"}
        self.replace_archive(
            layer_files=[
                (
                    "package-metadata",
                    json.dumps(
                        runtime_payload,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8"),
                )
            ]
        )
        self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-package-runtime-concrete"
        )

        ambiguous_payload = dict(safe_package)
        ambiguous_payload["password"] = "unclassified-concrete-value"
        self.replace_archive(
            layer_files=[
                (
                    "package-metadata",
                    json.dumps(
                        ambiguous_payload,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8"),
                )
            ]
        )
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-package-ambiguous-field"
        )

    def test_unsafe_duplicate_and_unsupported_layer_fail_closed(self) -> None:
        variants: dict[str, bytes] = {}
        unsafe = io.BytesIO()
        with tarfile.open(fileobj=unsafe, mode="w") as archive:
            member = tarfile.TarInfo("../escape")
            member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
        variants["unsafe"] = unsafe.getvalue()

        duplicate = io.BytesIO()
        with tarfile.open(fileobj=duplicate, mode="w") as archive:
            for payload in (b"one", b"two"):
                member = tarfile.TarInfo("etc/config")
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        variants["duplicate"] = duplicate.getvalue()
        variants["unsupported-compression"] = create_layer_archive_payload(
            [("etc/config", b"SAFE=value\n")], compression="bz2"
        )

        for name, payload in variants.items():
            with self.subTest(name=name):
                self.replace_archive(layer_archive_payload=payload)
                self.assert_bundle_error(
                    "SENSITIVE_SCAN_BLOCKED", f"out-blocked-{name}"
                )

    def test_manual_archive_scan_is_fixed_no_echo_and_keeps_output_empty(self) -> None:
        sentinel = "never-print-this-value"
        unsafe = io.BytesIO()
        with tarfile.open(fileobj=unsafe, mode="w") as archive:
            member = tarfile.TarInfo(f"../{sentinel}")
            member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
        self.replace_archive(layer_archive_payload=unsafe.getvalue())
        output = self.output_dir("out-blocked-cli")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(CompanyDeliveryError) as caught:
                self.build(output)
        self.assertEqual(caught.exception.code, "SENSITIVE_SCAN_BLOCKED")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn(sentinel, stderr.getvalue())
        self.assertEqual(list(output.iterdir()), [])

    def test_json_reason_remains_internal_to_manual_archive_scan(self) -> None:
        sentinel = "never-print-json-reason-value"
        self.replace_archive(
            layer_files=[
                (
                    "ambiguous-json",
                    json.dumps(
                        {
                            "kind": "source",
                            "source": {"password": sentinel},
                        },
                        separators=(",", ":"),
                    ).encode("utf-8"),
                )
            ]
        )
        output = self.output_dir("out-json-reason-cli")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(CompanyDeliveryError) as caught:
                self.build(output)
        self.assertEqual(caught.exception.code, "SENSITIVE_SCAN_BLOCKED")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn(sentinel, stderr.getvalue())
        self.assertNotIn("reason", stderr.getvalue())
        self.assertNotIn("JSON_CONTEXT", stderr.getvalue())
        self.assertNotIn("source_role", stderr.getvalue())
        self.assertEqual(list(output.iterdir()), [])

    def test_image_scan_resource_bounds_fail_closed(self) -> None:
        cases = (
            ("MAX_INNER_MEMBERS", 1, [("a", b"x"), ("b", b"y")]),
            ("MAX_INNER_MEMBER_BYTES", 3, [("large", b"four")]),
            ("MAX_EXPANDED_BYTES", 3, [("large", b"four")]),
            ("MAX_JSON_BYTES", 8, [("data", b'{"safe":"bounded"}\n')]),
        )
        for constant, limit, files in cases:
            with self.subTest(constant=constant):
                self.replace_archive(layer_files=files)
                with mock.patch(
                    f"aisoft_company_delivery.secret_scan.{constant}", limit
                ):
                    self.assert_bundle_error(
                        "SENSITIVE_SCAN_BLOCKED", f"out-bound-{constant.lower()}"
                    )

        self.replace_archive(
            layer_files=[("data", b'{"safe":1,"safe":2}\n')]
        )
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-duplicate-json-key"
        )

    def test_source_literal_secret_is_rejected_but_ambiguous_text_blocks(self) -> None:
        sentinel = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
        self.replace_archive(
            layer_files=[
                (
                    "source",
                    f'{{"password": "{sentinel}", trailing: true}}\n'.encode(),
                )
            ]
        )
        caught = self.assert_bundle_error(
            "SENSITIVE_CONTENT", "out-source-literal"
        )
        self.assertNotIn(sentinel, str(caught))

        self.replace_archive(
            layer_files=[
                (
                    "safe-source",
                    b'{"password": "example-placeholder", trailing: true}\n',
                )
            ]
        )
        built = self.build(self.output_dir("out-safe-source-literal"))
        self.assertTrue(
            verify_bundle(
                Path(built["bundle_root"]) / "handoff-manifest.json",
                Path(built["bundle_root"]),
            )["ok"]
        )

        self.replace_archive(layer_files=[("ambiguous", b'{"safe": ???}\n')])
        self.assert_bundle_error(
            "SENSITIVE_SCAN_BLOCKED", "out-ambiguous-structured-text"
        )


class CompanyDeliveryJsonDiagnosticTests(unittest.TestCase):
    REASONS = (
        "JSON_RESOURCE_LIMIT",
        "JSON_PARSE_UNSAFE",
        "JSON_SOURCE_ASSIGNMENT_AMBIGUOUS",
        "JSON_RUNTIME_ENV_INVALID",
        "JSON_SOURCE_SENSITIVE_AMBIGUOUS",
        "JSON_GENERIC_SENSITIVE_AMBIGUOUS",
        "JSON_REASON_UNAVAILABLE",
    )
    SOURCE_ROLES = (
        "SCHEMA",
        "SOURCE_MAP",
        "PACKAGE_METADATA",
        "I18N",
        "EXAMPLE",
        "OTHER",
    )

    def emit(self, reason: str, sentinel: str) -> CompanyDeliveryError:
        if reason == "JSON_REASON_UNAVAILABLE":
            return CompanyDeliveryError(
                "SENSITIVE_SCAN_BLOCKED",
                "bundle secret scan could not be completed safely",
            )
        with self.assertRaises(CompanyDeliveryError) as caught:
            if reason == "JSON_RESOURCE_LIMIT":
                with mock.patch.object(
                    secret_scan_module, "MAX_JSON_BYTES", 4
                ):
                    secret_scan_module._scan_structured_payload(
                        json.dumps({"safe": sentinel}).encode("utf-8")
                    )
            elif reason == "JSON_PARSE_UNSAFE":
                secret_scan_module._scan_structured_payload(
                    ('{"' + sentinel + '":}').encode("utf-8"),
                    strict_candidate=True,
                )
            elif reason == "JSON_SOURCE_ASSIGNMENT_AMBIGUOUS":
                secret_scan_module._scan_structured_payload(
                    ('{"safe":true,password:"' + sentinel + '"}').encode(
                        "utf-8"
                    )
                )
            elif reason == "JSON_RUNTIME_ENV_INVALID":
                secret_scan_module._scan_structured_payload(
                    json.dumps(
                        {"config": {"Env": [sentinel]}},
                        separators=(",", ":"),
                    ).encode("utf-8"),
                    runtime_context=True,
                )
            elif reason == "JSON_SOURCE_SENSITIVE_AMBIGUOUS":
                secret_scan_module._scan_structured_payload(
                    json.dumps(
                        {"source": {"password": sentinel}},
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
            elif reason == "JSON_GENERIC_SENSITIVE_AMBIGUOUS":
                secret_scan_module._scan_structured_payload(
                    json.dumps(
                        {"password": sentinel}, separators=(",", ":")
                    ).encode("utf-8")
                )
            else:
                self.fail("unexpected synthetic reason")
        return caught.exception

    def test_each_fixed_reason_is_machine_classifiable_without_echo(self) -> None:
        self.assertEqual(
            tuple(sorted(secret_scan_module.JSON_CONTEXT_REASON_CODES)),
            tuple(sorted(self.REASONS)),
        )
        for reason in self.REASONS:
            with self.subTest(reason=reason):
                sentinel = "never-print-" + reason.lower()
                error = self.emit(reason, sentinel)
                self.assertEqual(error.code, "SENSITIVE_SCAN_BLOCKED")
                self.assertEqual(
                    error.safe_message,
                    "bundle secret scan could not be completed safely",
                )
                self.assertEqual(
                    secret_scan_module.json_context_reason_code(error), reason
                )
                self.assertNotIn(sentinel, str(error))
                self.assertNotIn(sentinel, error.safe_message)

    def test_each_fixed_diagnostic_line_has_no_dynamic_input(self) -> None:
        for reason in self.REASONS:
            with self.subTest(reason=reason):
                sentinel = "never-print-" + reason.lower()
                error = self.emit(reason, sentinel)
                output = secret_scan_module.format_json_context_diagnostic(
                    error
                )
                self.assertEqual(
                    output,
                    "SENSITIVE_SCAN_BLOCKED: top_level=images.tar "
                    f"classifier=JSON_CONTEXT reason={reason}"
                    + (
                        " source_role=OTHER"
                        if reason == "JSON_SOURCE_SENSITIVE_AMBIGUOUS"
                        else ""
                    ),
                )
                self.assertNotIn(sentinel, output)

        with self.assertRaisesRegex(
            ValueError,
            "JSON context diagnostic requires SENSITIVE_SCAN_BLOCKED",
        ):
            secret_scan_module.format_json_context_diagnostic(
                CompanyDeliveryError(
                    "SENSITIVE_CONTENT",
                    "bundle contains forbidden sensitive content",
                )
            )

    def emit_source_role(
        self, role: str, sentinel: str
    ) -> CompanyDeliveryError:
        documents = {
            "SCHEMA": {
                "$schema": "https://example.invalid/schema",
                "properties": {"password": sentinel},
            },
            "SOURCE_MAP": {
                "version": 3,
                "sources": [],
                "names": [],
                "mappings": "",
                "password": sentinel,
            },
            "PACKAGE_METADATA": {
                "name": "fixture",
                "version": "1.0.0",
                "scripts": {},
                "password": sentinel,
            },
            "I18N": {
                "locale": "en",
                "messages": {"password": sentinel},
            },
            "EXAMPLE": {
                "kind": "source",
                "source": {"password": sentinel},
            },
            "OTHER": {
                "$schema": "https://example.invalid/schema",
                "locale": "en",
                "password": sentinel,
            },
        }
        with self.assertRaises(CompanyDeliveryError) as caught:
            secret_scan_module._scan_structured_payload(
                json.dumps(
                    documents[role], separators=(",", ":")
                ).encode("utf-8")
            )
        return caught.exception

    def test_each_source_role_is_fixed_and_machine_classifiable(self) -> None:
        self.assertEqual(
            tuple(sorted(secret_scan_module.JSON_SOURCE_ROLES)),
            tuple(sorted(self.SOURCE_ROLES)),
        )
        for role in self.SOURCE_ROLES:
            with self.subTest(role=role):
                sentinel = "never-print-source-role-" + role.lower()
                error = self.emit_source_role(role, sentinel)
                self.assertEqual(
                    secret_scan_module.json_context_reason_code(error),
                    "JSON_SOURCE_SENSITIVE_AMBIGUOUS",
                )
                self.assertEqual(
                    secret_scan_module.json_source_role_code(error), role
                )
                self.assertNotIn(sentinel, str(error))

    def test_each_source_role_diagnostic_line_is_fixed_no_echo(self) -> None:
        for role in self.SOURCE_ROLES:
            with self.subTest(role=role):
                sentinel = "never-print-source-role-" + role.lower()
                error = self.emit_source_role(role, sentinel)
                output = secret_scan_module.format_json_context_diagnostic(
                    error
                )
                self.assertEqual(
                    output,
                    "SENSITIVE_SCAN_BLOCKED: top_level=images.tar "
                    "classifier=JSON_CONTEXT "
                    "reason=JSON_SOURCE_SENSITIVE_AMBIGUOUS "
                    f"source_role={role}",
                )
                self.assertNotIn(sentinel, output)

    def test_unclassified_source_marker_collapses_to_other(self) -> None:
        sentinel = "never-print-unclassified-source-role"
        with self.assertRaises(CompanyDeliveryError) as caught:
            secret_scan_module._scan_structured_payload(
                json.dumps(
                    {"source": {"password": sentinel}},
                    separators=(",", ":"),
                ).encode("utf-8")
            )
        self.assertEqual(
            secret_scan_module.json_source_role_code(caught.exception),
            "OTHER",
        )
        self.assertNotIn(sentinel, str(caught.exception))


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
            "sync/inbound-sync.sh reconcile <allowlisted-profile>",
            "aisoft-docker-release-gate <action> <fixed-target-id> <full-sha>",
            "sync timer、Actions auto deploy 与 production gate 均为 `disabled/inactive`",
            "普通 Runner 无 production SSH、sudo、业务 DB 或任意 shell 权限",
            "公司侧 Stage 10–110：`NOT RUN`",
            "greenfield-isolated-install",
            "collect-inventory --role scm-ci --mode preflight --output",
            "verify-gitea-transition --input",
            "candidate-post-install-health",
            "不得运行 legacy Docker/HTTP probe",
            "controlled upgrade 不属于本合同",
            "Stage 30=`NOT RUN`",
            "legacy observation=`NOT RUN`",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runbook)
        matrix = load_compatibility_matrix(
            self.repository_root / "company-delivery/templates/compatibility-matrix.example.json"
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

    def test_authoritative_docs_link_two_vm_reference_runbook(self) -> None:
        # #237: the two-VM path is a de-projected reference implementation.
        # Authoritative docs must link the runbook and describe the topology
        # without naming a pilot project or pinning its stage progress.
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
                self.assertIn("两台公司", text)
                self.assertIn("本地 OrbStack", text)
                self.assertIn("exact `docker-release/v2` bytes", text)
        for name in ("README.md", "07-内网与生产平移路线.md"):
            with self.subTest(name=name):
                self.assertNotIn("NewEmaint 公司交付 runbook", self.read(name))

    def test_docs_never_reuse_company_rebuild_as_local_evidence(self) -> None:
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
