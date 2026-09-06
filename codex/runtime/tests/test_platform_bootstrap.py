"""Public contract regressions; all source/target data are isolated local fixtures."""
from __future__ import annotations

import copy
import gzip
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from aisoft_platform_bootstrap import bundle as bundle_module
from aisoft_platform_bootstrap.bundle import ARCHIVE, MAPPINGS, build, verify
from aisoft_platform_bootstrap.contract import (ACTIONS, BootstrapError, SCHEMAS, canonical,
    digest, document, load, parse)
from aisoft_platform_bootstrap.workflow import adoption_plan, operation_request, readback


ROOT = Path(__file__).resolve().parents[3]


class PlatformBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aisoft-bootstrap-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "source"
        self.repo.mkdir()
        for source in MAPPINGS:
            destination = self.repo / source
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source, destination)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Bootstrap fixture")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture platform source")
        self.sha = self.git("rev-parse", "HEAD").strip()
        self.approval = load((self.repo / "platform-bootstrap/templates/approval.example.json"), "approval")
        self.approval["source_sha"] = self.sha
        self.approval_path = self.root / "approval.json"
        self.approval_path.write_bytes(canonical(self.approval))
        self.inventory = load(self.repo / "platform-bootstrap/templates/inventory.example.json", "inventory")
        self.target = load(self.repo / "platform-bootstrap/templates/target.example.json", "target")
        for action in ("repo-bootstrap", "one-shot-inbound"):
            self.target["action_inputs"][action]["staging_ref"] = "refs/heads/sync/platform-" + self.sha
        self.output = self.root / "output"
        self.output.mkdir(mode=0o700)

    def git(self, *args):
        return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
            "-C", str(self.repo), *args], stderr=subprocess.DEVNULL, text=True)

    def bundle(self):
        receipt = build(self.repo, self.approval_path, self.output)
        manifest = verify(self.output / "handoff.json", self.output / ARCHIVE, receipt["handoff_sha256"])
        return receipt, manifest

    def error(self, code, function, *args, **kwargs):
        with self.assertRaises(BootstrapError) as raised:
            function(*args, **kwargs)
        self.assertEqual(code, raised.exception.code)

    def cli(self, *args, bundled=False):
        executable = (self.root / "unpacked" / "bin/aisoft-platform-bootstrap" if bundled
                      else self.repo / "platform-bootstrap/bin/aisoft-platform-bootstrap")
        return subprocess.run([sys.executable, str(executable), *map(str, args)],
                              capture_output=True, timeout=30)

    def plan(self):
        receipt, manifest = self.bundle()
        return adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)

    def present(self, manifest):
        self.inventory.update(gitea_state="present", gitea_version="1.26.4",
            gitea_identity_sha256="c" * 64, gitea_healthy=True,
            repository_identity_sha256=self.target["repository_identity_sha256"], source_sha=self.sha,
            runner_state="enabled", runner_scope="platform-only", inbound_state="one-shot",
            backup_verified=True, restore_verified=True)
        self.inventory["protection"] = dict(direct_push_denied=True, force_push_denied=True,
            human_merge_only=True, required_ci=self.target["required_ci"])
        self.inventory["rollback"] = dict(kind="snapshot", identity_sha256="d" * 64, source_sha=self.sha)
        manifest["rollback"] = copy.deepcopy(self.inventory["rollback"])

    def observation(self, request):
        return dict(contract_version="platform-bootstrap-observation/v1",
            request_sha256=digest(canonical(request)), target_identity_sha256=request["target_identity_sha256"],
            gitea_identity_sha256=request["gitea_identity_sha256"],
            repository_identity_sha256=request["repository_identity_sha256"],
            source_sha=request["source_sha"] if request["direction"] == "apply" else request["rollback"]["source_sha"],
            company_merge_sha="e" * 40, evidence_layer="local", result="PASS", checks=["identity", "no-op",
            "negative-permission", "deliberate-failure", "recovery", "required-ci", "human-merge", "provenance"],
            evidence_sha256="f" * 64)

    def test_two_builds_byte_identical_without_application_inputs(self):
        first, _ = self.bundle()
        second_output = self.root / "second"
        second_output.mkdir(mode=0o700)
        second = build(self.repo, self.approval_path, second_output)
        self.assertEqual(first, second)
        for name in (ARCHIVE, "handoff.json", "handoff.sha256"):
            self.assertEqual((self.output / name).read_bytes(), (second_output / name).read_bytes())
        self.assertEqual("NOT_READ", first["target_facts"])

    def test_archive_corruption_is_rejected_without_extraction(self):
        receipt, _ = self.bundle()
        archive = self.output / ARCHIVE
        archive.write_bytes(archive.read_bytes()[:-1] + b"x")
        self.error("CHECKSUM_MISMATCH", verify, self.output / "handoff.json", archive, receipt["handoff_sha256"])

    def test_external_handoff_pin_required_even_for_self_consistent_bytes(self):
        self.bundle()
        self.error("CHECKSUM_MISMATCH", verify, self.output / "handoff.json", self.output / ARCHIVE, "0" * 64)

    def test_wrong_source_identity_leaves_empty_output(self):
        self.approval["source_sha"] = "0" * 40
        self.approval_path.write_bytes(canonical(self.approval))
        self.error("IDENTITY_MISMATCH", build, self.repo, self.approval_path, self.output)
        self.assertEqual([], list(self.output.iterdir()))

    def test_dirty_and_untracked_source_rejected(self):
        file = self.repo / "untracked"
        file.write_text("fixture")
        self.error("SOURCE_DIRTY", build, self.repo, self.approval_path, self.output)

    def test_closed_source_component_allowlist(self):
        file = self.repo / "platform-bootstrap/unrequested.txt"
        file.write_text("not an allowed component")
        self.git("add", ".")
        self.git("commit", "-qm", "extra fixture component")
        self.approval["source_sha"] = self.git("rev-parse", "HEAD").strip()
        self.approval_path.write_bytes(canonical(self.approval))
        self.error("COMPONENT_ALLOWLIST_MISMATCH", build, self.repo, self.approval_path, self.output)

    def test_secret_like_input_rejected_no_echo(self):
        secret = "DO_NOT_ECHO_FAKE_SECRET"
        self.approval["password"] = secret
        self.approval_path.write_bytes(canonical(self.approval))
        result = self.cli("build-bundle", "--repository-root", self.repo, "--approval", self.approval_path,
                          "--output-directory", self.output)
        self.assertEqual(2, result.returncode)
        self.assertNotIn(secret.encode(), result.stdout + result.stderr)
        self.assertIn(b"SCHEMA_INVALID", result.stderr)

    def test_source_concrete_secret_literal_rejected(self):
        file = self.repo / "platform-bootstrap/README.md"
        file.write_text(file.read_text() + "\npassword=FakeLiteralForNegativeTest\n")
        self.git("add", ".")
        self.git("commit", "-qm", "deliberately unsafe fixture")
        self.approval["source_sha"] = self.git("rev-parse", "HEAD").strip()
        self.approval_path.write_bytes(canonical(self.approval))
        self.error("SENSITIVE_CONTENT", build, self.repo, self.approval_path, self.output)

    def test_duplicate_json_keys_and_nonfinite_are_rejected(self):
        self.error("JSON_INVALID", parse, b'{"password":1,"password":2}', "approval")
        self.error("JSON_INVALID", parse, b'{"value":NaN}', "approval")

    def test_strict_types_unknown_fields_and_empty_ci(self):
        for key, value in [("host_role", "appserver-prod"), ("ai_present", 0), ("hostname", "forbidden")]:
            with self.subTest(key=key):
                bad = copy.deepcopy(self.inventory)
                bad[key] = value
                self.error("SCHEMA_INVALID", document, bad, "inventory")
        self.target["required_ci"] = []
        self.error("SCHEMA_INVALID", document, self.target, "target")

    def test_input_symlink_and_hardlink_refused(self):
        link = self.root / "link.json"
        link.symlink_to(self.approval_path)
        self.error("UNSAFE_PATH", load, link, "approval")
        link.unlink()
        os.link(self.approval_path, link)
        self.error("UNSAFE_PATH", load, link, "approval")

    def test_output_not_empty_or_in_source_refused(self):
        (self.output / "existing").write_text("keep")
        self.error("OUTPUT_INVALID", build, self.repo, self.approval_path, self.output)
        self.assertEqual("keep", (self.output / "existing").read_text())

    def test_schema_files_match_runtime_contract(self):
        for name, schema in SCHEMAS.items():
            stored = json.loads((ROOT / f"platform-bootstrap/schema/{name}-v1.schema.json").read_bytes())
            stored.pop("$schema")
            stored.pop("title")
            self.assertEqual(schema, stored)

    def test_first_install_is_bound_to_uninstalled_identity(self):
        plan = self.plan()
        self.assertEqual("first-install", plan["decision"])
        self.assertEqual(ACTIONS, [entry["action"] for entry in plan["actions"]])

    def test_absent_repository_cannot_skip_protection_or_ci(self):
        receipt, manifest = self.bundle()
        for protection in [dict(direct_push_denied=True, force_push_denied=True,
            human_merge_only=True, required_ci=[]), dict(direct_push_denied=False,
            force_push_denied=False, human_merge_only=False, required_ci=self.target["required_ci"])]:
            with self.subTest(protection=protection):
                self.inventory["protection"] = protection
                plan = adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)
                self.assertEqual("INCONSISTENT_INVENTORY", plan["reason"])

    def test_every_action_requires_negative_permission_evidence(self):
        plan = self.plan()
        for action in ACTIONS:
            with self.subTest(action=action):
                request = operation_request(plan, action, "apply", dry_run=True)
                observation = self.observation(request)
                observation["checks"].remove("negative-permission")
                self.error("EVIDENCE_INCOMPLETE", readback, request, observation)

    def test_exact_action_parameters_are_hashed_and_closed(self):
        plan = self.plan()
        first = operation_request(plan, "runner", "apply", dry_run=True)
        plan["action_inputs"]["runner"]["binary_sha256"] = "0" * 64
        second = operation_request(plan, "runner", "apply", dry_run=True)
        self.assertNotEqual(first["plan_sha256"], second["plan_sha256"])
        self.assertNotEqual(digest(canonical(first)), digest(canonical(second)))
        self.assertEqual("0" * 64, second["exact_inputs"]["binary_sha256"])
        self.assertEqual(ACTIONS[:4], first["predecessor_actions"])
        second["exact_inputs"]["shell"] = "forbidden"
        self.error("SCHEMA_INVALID", document, second, "request")

    def test_wrong_staging_ref_and_contexts_rejected(self):
        receipt, manifest = self.bundle()
        self.target["action_inputs"]["repo-bootstrap"]["staging_ref"] = "refs/heads/main"
        self.error("SCHEMA_INVALID", document, self.target, "target")
        for action in ("repo-bootstrap", "one-shot-inbound"):
            self.target["action_inputs"][action]["staging_ref"] = "refs/heads/sync/platform-" + "0" * 40
        plan = adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)
        self.assertEqual("IDENTITY_MISMATCH", plan["reason"])
        self.target["action_inputs"]["required-ci"]["contexts"] = ["other-context"]
        self.error("IDENTITY_MISMATCH", document, self.target, "target")

    def test_payload_schema_refuses_absolute_and_dot_paths(self):
        _, manifest = self.bundle()
        for path in ("/absolute", "../escape", "runtime/../escape", "./file", "a//file"):
            with self.subTest(path=path):
                value = copy.deepcopy(manifest)
                value["payloads"][0]["path"] = path
                self.error("SCHEMA_INVALID", document, value, "manifest")

    def test_git_fsmonitor_cannot_execute_during_build(self):
        probe = self.root / "fsmonitor"
        marker = self.root / "executed"
        probe.write_text(f'#!/bin/sh\ntouch "{marker}"\n')
        probe.chmod(0o755)
        self.git("config", "core.fsmonitor", str(probe))
        self.bundle()
        self.assertFalse(marker.exists())

    def test_concurrent_worktree_edit_never_changes_pinned_payload(self):
        original_git = bundle_module.git
        source = self.repo / "platform-bootstrap/README.md"
        original = source.read_bytes()
        changed = False

        def racing_git(repository, *args):
            nonlocal changed
            if args[:2] == ("cat-file", "blob") and not changed:
                changed = True
                source.write_bytes(original + b"\nconcurrent-unapproved-change\n")
            elif args[0] == "status" and changed:
                source.write_bytes(original)
            return original_git(repository, *args)

        with patch.object(bundle_module, "git", racing_git):
            self.bundle()
        self.assertTrue(changed)
        with tarfile.open(self.output / ARCHIVE) as tar:
            self.assertEqual(original, tar.extractfile("README.md").read())

    def test_adopt_is_noop_except_new_canary(self):
        receipt, manifest = self.bundle()
        self.present(manifest)
        plan = adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)
        self.assertEqual("adopt", plan["decision"])
        self.assertTrue(all(item["mode"] == "no-op" for item in plan["actions"][:-1]))
        self.assertEqual("change", plan["actions"][-1]["mode"])

    def test_adopt_with_remediation_keeps_existing_gitea(self):
        receipt, manifest = self.bundle()
        self.present(manifest)
        self.inventory["protection"]["force_push_denied"] = False
        plan = adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)
        self.assertEqual("adopt-with-remediation", plan["decision"])
        self.assertEqual("no-op", plan["actions"][0]["mode"])
        self.assertEqual("change", plan["actions"][2]["mode"])

    def test_controlled_upgrade_always_blocked(self):
        receipt, manifest = self.bundle()
        self.present(manifest)
        for field, value in [("gitea_version", "1.25.0"), ("source_sha", "0" * 40)]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.inventory)
                bad[field] = value
                plan = adoption_plan(manifest, receipt["handoff_sha256"], bad, self.target)
                self.assertEqual(("controlled-upgrade", "BLOCKED", []),
                                 (plan["decision"], plan["status"], plan["actions"]))
                self.error("ADOPTION_BLOCKED", operation_request, plan, "runner", "apply", dry_run=True)

    def test_unknown_unsafe_identity_and_missing_recovery_fail_closed(self):
        receipt, manifest = self.bundle()
        self.present(manifest)
        for field, value, reason in [("target_identity_sha256", "0" * 64, "IDENTITY_MISMATCH"),
            ("repository_identity_sha256", "0" * 64, "IDENTITY_MISMATCH"),
            ("gitea_identity_sha256", "0" * 64, "IDENTITY_MISMATCH"),
            ("gitea_state", "unknown", "UNKNOWN_STATE"), ("ai_present", True, "UNSAFE_HOST"),
            ("inbound_state", "timer", "UNSAFE_HOST"), ("runner_scope", "unknown", "UNSAFE_HOST"),
            ("restore_verified", False, "RECOVERY_MISSING")]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.inventory)
                bad[field] = value
                plan = adoption_plan(manifest, receipt["handoff_sha256"], bad, self.target)
                self.assertEqual(("BLOCKED", reason, []), (plan["status"], plan["reason"], plan["actions"]))

    def test_absent_instance_cannot_hide_existing_repository(self):
        receipt, manifest = self.bundle()
        self.inventory["repository_identity_sha256"] = self.target["repository_identity_sha256"]
        plan = adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)
        self.assertEqual("INCONSISTENT_INVENTORY", plan["reason"])

    def test_all_actions_apply_and_rollback_dryrun(self):
        plan = self.plan()
        for action in ACTIONS:
            for direction in ("apply", "rollback"):
                with self.subTest(action=action, direction=direction):
                    request = operation_request(plan, action, direction, dry_run=True)
                    self.assertEqual(("DRY_RUN", "NOT RUN"), (request["status"], request["execution"]))
                    result = readback(request, self.observation(request))
                    self.assertEqual(("PASS", "local", "declared-observation-only"),
                                     (result["status"], result["evidence_layer"], result["validation_scope"]))

    def test_no_live_apply_or_arbitrary_executor_fallback(self):
        plan = self.plan()
        for direction in ("apply", "rollback"):
            self.error("SITE_EXECUTOR_NOT_BOUND", operation_request, plan, "runner", direction, dry_run=False)

    def test_readback_wrong_identity_and_missing_checks_refused(self):
        request = operation_request(self.plan(), "canary", "apply", dry_run=True)
        for field, value, code in [("source_sha", "0" * 40, "IDENTITY_MISMATCH"),
            ("gitea_identity_sha256", "0" * 64, "IDENTITY_MISMATCH"),
            ("request_sha256", "0" * 64, "IDENTITY_MISMATCH"), ("checks", [], "EVIDENCE_INCOMPLETE"),
            ("company_merge_sha", None, "EVIDENCE_INCOMPLETE")]:
            with self.subTest(field=field):
                observation = self.observation(request)
                observation[field] = value
                self.error(code, readback, request, observation)

    def test_failed_readback_not_promoted_to_pass(self):
        request = operation_request(self.plan(), "canary", "apply", dry_run=True)
        for status in ("FAIL", "BLOCKED", "NOT RUN"):
            observation = self.observation(request)
            observation.update(result=status, checks=[], company_merge_sha=None)
            self.assertEqual(status, readback(request, observation)["status"])

    def test_cli_recomputes_plan_and_refuses_stale_approval(self):
        receipt, manifest = self.bundle()
        plan = adoption_plan(manifest, receipt["handoff_sha256"], self.inventory, self.target)
        for name, value in [("inventory", self.inventory), ("target", self.target)]:
            (self.root / f"{name}.json").write_bytes(canonical(value))
        args = ["apply", "--dry-run", "--action", "repo-bootstrap", "--handoff", self.output / "handoff.json",
            "--archive", self.output / ARCHIVE, "--expected-handoff-sha256", receipt["handoff_sha256"],
            "--inventory", self.root / "inventory.json", "--target", self.root / "target.json",
            "--output", self.root / "request.json", "--expected-plan-sha256", digest(canonical(plan))]
        result = self.cli(*args)
        self.assertEqual(0, result.returncode, result.stderr)
        args[-1] = "0" * 64
        result = self.cli(*args)
        self.assertEqual(2, result.returncode)
        self.assertIn(b"STALE_PLAN", result.stderr)

    def test_bundled_cli_runs_without_repo_runtime_or_network(self):
        receipt, _ = self.bundle()
        # These bytes were created and verified by this test. No untrusted extraction.
        with tarfile.open(self.output / ARCHIVE) as tar:
            tar.extractall(self.root / "unpacked", filter="data")
        shutil.rmtree(self.repo)
        result = self.cli("verify-handoff", "--handoff", self.output / "handoff.json",
            "--archive", self.output / ARCHIVE, "--expected-handoff-sha256", receipt["handoff_sha256"], bundled=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("NOT_READ", json.loads(result.stdout)["target_facts"])

    def test_hostile_archive_members_rejected_even_with_recomputed_outer_hash(self):
        self.bundle()
        handoff = load(self.output / "handoff.json", "handoff")
        original = (self.output / ARCHIVE).read_bytes()
        for name, kind in [("../escape", tarfile.REGTYPE), ("README.md", tarfile.SYMTYPE),
                           ("README.md", tarfile.REGTYPE)]:
            with self.subTest(name=name, kind=kind):
                output = io.BytesIO()
                with tarfile.open(fileobj=output, mode="w:gz") as tar:
                    with tarfile.open(fileobj=io.BytesIO(original), mode="r:gz") as source:
                        for entry in source:
                            tar.addfile(entry, source.extractfile(entry))
                    entry = tarfile.TarInfo(name)
                    entry.type = kind
                    entry.linkname = "/unexpected" if kind == tarfile.SYMTYPE else ""
                    entry.size = 0
                    tar.addfile(entry, io.BytesIO())
                modified = output.getvalue()
                handoff["archive_sha256"] = digest(modified)
                (self.output / ARCHIVE).write_bytes(modified)
                (self.output / "handoff.json").write_bytes(canonical(handoff))
                self.error("ARCHIVE_INVALID", verify, self.output / "handoff.json", self.output / ARCHIVE,
                           digest(canonical(handoff)))
        self.assertFalse((self.root / "escape").exists())

    def test_decompression_limit(self):
        self.bundle()
        archive = gzip.compress(b"\0" * (16 * 1024 * 1024 + 1))
        handoff = load(self.output / "handoff.json", "handoff")
        handoff["archive_sha256"] = digest(archive)
        (self.output / ARCHIVE).write_bytes(archive)
        (self.output / "handoff.json").write_bytes(canonical(handoff))
        self.error("RESOURCE_LIMIT", verify, self.output / "handoff.json", self.output / ARCHIVE,
                   digest(canonical(handoff)))

    def test_field_command_blocks_at_most_50_lines(self):
        for name in ("README.md", "runbook.md"):
            active, lines = False, []
            for line in (ROOT / "platform-bootstrap" / name).read_text().splitlines():
                if line == "```bash":
                    active, lines = True, []
                elif line == "```" and active:
                    self.assertLessEqual(len(lines), 50)
                    active = False
                elif active:
                    lines.append(line)
            self.assertFalse(active)


if __name__ == "__main__":
    unittest.main()
