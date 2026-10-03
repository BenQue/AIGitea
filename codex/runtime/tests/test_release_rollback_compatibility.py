from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import shutil
import stat
import unittest
from unittest.mock import patch

from aisoft_release.errors import ReleaseError, StateError
from aisoft_release.contract import load_target_profile
from aisoft_release.runner import ReleaseRuntime
from aisoft_release.state import StateStore
from tests.release_test_support import (
    FakeDocker, SHA_A, SHA_B, create_release, migration_identity, install_rollback_evidence, write_json, update_manifest,
)


class RollbackCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name).resolve()
        self.profile, model, manifest = create_release(self.root, SHA_A)
        self.docker = FakeDocker()
        self.docker.register(SHA_A, model, manifest)
        _, model, manifest = create_release(self.root, SHA_B)
        self.docker.register(SHA_B, model, manifest)
        self.runtime = ReleaseRuntime(self.docker, hostname="test-host")
        self.store = StateStore(self.root / "state", "newemaint-test")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_migration_records_database_position_and_noop_preserves_it(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.assertEqual(self.store.load()["database_revision"], {
            "status": "known", "migration_identity": migration_identity(SHA_A),
            "generation": 1,
        })
        self.runtime.stage(self.profile, SHA_B)
        self.runtime.migrate(self.profile, SHA_B)
        before = self.store.load()
        self.assertEqual(before["database_revision"]["generation"], 2)
        self.assertEqual(self.runtime.migrate(self.profile, SHA_A)["action"], "migration-noop")
        after = self.store.load()
        self.assertEqual(after["database_revision"], before["database_revision"])
        self.assertEqual(after["migrations"], before["migrations"])

    def test_activation_failure_blocks_old_image_after_different_migration(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.stage(self.profile, SHA_B)
        self.runtime.migrate(self.profile, SHA_B)
        self.docker.unhealthy_for.add(SHA_B)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.activate(self.profile, SHA_B)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual([e[1] for e in self.docker.mutations if e[0] == "up"], [SHA_B])
        state = self.store.load()
        self.assertEqual(state["last_result"], "activation-rollback-blocked")
        self.assertEqual(state["current_release"], SHA_A)
        self.assertEqual(state["database_revision"]["migration_identity"], migration_identity(SHA_B))
        self.assertFalse(self.runtime.status(self.profile, SHA_A)["ok"])

    def test_exact_operator_evidence_allows_explicit_rollback_without_database_restore(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        revision = self.store.load()["database_revision"]
        install_rollback_evidence(self.root, SHA_B, SHA_A)
        self.docker.events.clear()
        self.assertEqual(self.runtime.rollback(self.profile, SHA_A)["action"], "rolled-back")
        self.assertEqual([e[0] for e in self.docker.mutations], ["up"])
        self.assertEqual(self.store.load()["database_revision"], revision)

    def test_interrupted_migration_persists_uncertain_before_call_and_blocks_other_migration(self) -> None:
        self.runtime.stage(self.profile, SHA_A)
        store = self.store
        seen = []
        class InterruptedDocker(FakeDocker):
            def run_migration(self, *args: object) -> None:
                seen.append(store.load()["database_revision"])
                raise KeyboardInterrupt
        interrupted = InterruptedDocker()
        interrupted.models = self.docker.models
        interrupted.images = self.docker.images
        interrupted.manifests = self.docker.manifests
        with self.assertRaises(KeyboardInterrupt):
            ReleaseRuntime(interrupted, hostname="test-host").migrate(self.profile, SHA_A)
        self.assertEqual(seen, [{"status": "uncertain", "migration_identity": migration_identity(SHA_A), "generation": 1}])
        self.runtime.stage(self.profile, SHA_B)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError):
            self.runtime.migrate(self.profile, SHA_B)
        self.assertEqual(self.docker.mutations, [])

        self.assertEqual(self.store.load()["database_revision"], seen[0])

    def test_matching_evidence_is_rejected_for_each_binding_time_and_shape_violation(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        path = install_rollback_evidence(self.root, SHA_B, SHA_A)
        original = json.loads(path.read_text())
        changes = {
            "profile_id": "other", "environment": "production", "expected_hostname": "other-host",
            "compose_project": "other", "source_repository": "admin/other",
            "candidate_release": "c" * 40, "rollback_release": "d" * 40,
            "candidate_manifest_sha256": "0" * 64, "rollback_manifest_sha256": "0" * 64,
            "candidate_migration_identity": migration_identity(SHA_A),
            "rollback_migration_identity": migration_identity(SHA_B),
            "database_migration_identity": migration_identity(SHA_A),
            "database_state_sha256": "0" * 64,
            "verified_at": "2098-01-01T00:00:00Z", "expires_at": "2021-01-01T00:00:00Z",
            "result": "incompatible", "evidence_id": "unsafe/path",
            "unknown": "do-not-echo-secret",
        }
        self.runtime = ReleaseRuntime(self.docker, hostname="test-host", now=datetime(2026, 10, 2, tzinfo=timezone.utc))
        for field, value in changes.items():
            with self.subTest(field=field):
                envelope = deepcopy(original)
                envelope["records"][0][field] = value
                write_json(path, envelope, mode=0o600)
                self.docker.events.clear()
                with self.assertRaises(ReleaseError) as caught:
                    self.runtime.rollback(self.profile, SHA_A)
                self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
                self.assertEqual(self.docker.mutations, [])
                self.assertNotIn(str(path), str(caught.exception))
                self.assertNotIn("do-not-echo-secret", str(caught.exception))

    def test_evidence_duplicate_unknown_corrupt_oversize_and_ambiguous_fail_closed(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        path = install_rollback_evidence(self.root, SHA_B, SHA_A)
        original = json.loads(path.read_text())
        ambiguous = deepcopy(original)
        ambiguous["records"] *= 2
        unknown = deepcopy(original)
        unknown["extra"] = "secret-sentinel"
        payloads = ["{", "[1]", "x" * (256 * 1024 + 1), json.dumps(ambiguous),
                    json.dumps(unknown), json.dumps(original).replace('"result": "compatible"',
                    '"result": "compatible", "result": "compatible"'),
                    json.dumps(original).replace('"records":', '"records": [], "records":')]
        for index, payload in enumerate(payloads):
            with self.subTest(index=index):
                path.write_text(payload)
                self.docker.events.clear()
                with self.assertRaises(ReleaseError) as caught:
                    self.runtime.rollback(self.profile, SHA_A)
                self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
                self.assertEqual(self.docker.mutations, [])

    def test_evidence_permission_missing_and_symlink_rejection(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        path = install_rollback_evidence(self.root, SHA_B, SHA_A)
        original = path.read_bytes()
        for violation in ("file-mode", "parent-mode", "missing", "symlink", "parent-symlink"):
            with self.subTest(violation=violation):
                if path.is_symlink():
                    path.unlink()
                path.write_bytes(original)
                path.chmod(0o600)
                path.parent.chmod(0o700)
                if violation == "file-mode":
                    path.chmod(0o644)
                elif violation == "parent-mode":
                    path.parent.chmod(0o770)
                elif violation == "missing":
                    path.unlink()
                elif violation == "symlink":
                    target = self.root / "operator" / "other.json"
                    target.write_bytes(original)
                    target.chmod(0o600)
                    path.unlink()
                    path.symlink_to(target)
                else:
                    alias = self.root / "alias"
                    alias.symlink_to(path.parent, target_is_directory=True)
                    profile = json.loads(self.profile.read_text())
                    profile["rollback_compatibility_file"] = str(alias / path.name)
                    write_json(self.profile, profile, mode=0o600)
                self.docker.events.clear()
                with self.assertRaises(ReleaseError) as caught:
                    self.runtime.rollback(self.profile, SHA_A)
                self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
                self.assertEqual(self.docker.mutations, [])

    def test_failed_migration_evidence_cannot_hide_uncertain_position(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.docker.fail_migration_for.add(SHA_B)
        with self.assertRaises(ReleaseError):
            self.runtime.deploy(self.profile, SHA_B)
        state = self.store.load()
        self.assertEqual(state["database_revision"]["status"], "uncertain")
        self.assertEqual(state["database_revision"]["generation"], 2)
        state["previous_release"] = SHA_B
        self.store.save(state)
        install_rollback_evidence(self.root, SHA_A, SHA_B)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.rollback(self.profile, SHA_B)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def test_historical_completed_noop_does_not_authorize_rollback_after_c_migration(self) -> None:
        shutil.rmtree(self.root / "releases" / SHA_B)
        _, model, manifest = create_release(self.root, SHA_B, shares_migration_with=SHA_A)
        self.docker.register(SHA_B, model, manifest)
        sha_c = "c" * 40
        _, model, _ = create_release(self.root, sha_c)
        manifest = update_manifest(self.root / "releases" / sha_c,
            lambda m: m["migration"].update({"identity": "sha256:" + "7" * 64}))
        self.docker.register(sha_c, model, manifest)
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.stage(self.profile, sha_c)
        self.runtime.migrate(self.profile, sha_c)
        position = self.store.load()["database_revision"]
        self.runtime.stage(self.profile, SHA_B)
        self.assertEqual(self.runtime.migrate(self.profile, SHA_B)["action"], "migration-noop")
        self.docker.unhealthy_for.add(SHA_B)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.activate(self.profile, SHA_B)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual([e[1] for e in self.docker.mutations if e[0] == "up"], [SHA_B])
        self.assertEqual(self.store.load()["database_revision"], position)

    def test_null_identities_require_operator_proof_and_leave_database_untracked(self) -> None:
        for release in (SHA_A, SHA_B):
            shutil.rmtree(self.root / "releases" / release)
            _, model, manifest = create_release(self.root, release, migration=False)
            self.docker.register(release, model, manifest)
            self.runtime.deploy(self.profile, release)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError):
            self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])
        install_rollback_evidence(self.root, SHA_B, SHA_A)
        self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(self.store.load()["database_revision"], {"status": "untracked", "migration_identity": None, "generation": 0})

    def test_database_revision_rejects_unknown_fields_bool_generation_and_bad_identity(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        original = self.store.load()
        for patch in ({"generation": True}, {"generation": -1}, {"status": "guessed"}, {"status": []},
                      {"migration_identity": "short"}, {"extra": "bad"}, {"migration_identity": None}):
            with self.subTest(patch=patch):
                state = deepcopy(original)
                state["database_revision"].update(patch)
                write_json(self.store.path, state, mode=0o600)
                with self.assertRaises(StateError):
                    self.store.load()

    def test_legacy_state_read_upgrade_is_untracked_and_does_not_write_or_guess_order(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        original = self.store.load()
        for version in ("docker-release-state/v1", "docker-release-state/v2"):
            with self.subTest(version=version):
                legacy = {k: v for k, v in original.items() if k != "database_revision"}
                legacy["contract_version"] = version
                if version.endswith("v1"):
                    del legacy["staged_releases"]
                write_json(self.store.path, legacy, mode=0o600)
                raw = self.store.path.read_bytes()
                state = self.store.load()
                self.assertEqual(state["contract_version"], "docker-release-state/v3")
                self.assertEqual(state["database_revision"], {"status": "untracked", "migration_identity": None, "generation": 0})
                self.assertEqual(state["migrations"], original["migrations"])
                self.assertEqual(self.store.path.read_bytes(), raw)

    def test_legacy_deploy_failure_blocks_fallback_in_v1_and_v2(self) -> None:
        for version in ("docker-release/v1", "docker-release/v2"):
            with self.subTest(version=version):
                root = self.root / version.split("/")[-1]
                docker = FakeDocker()
                for release in (SHA_A, SHA_B):
                    profile, model, manifest = create_release(root, release, contract_version=version,
                        identity_version="legacy" if version.endswith("v1") else "v2")
                    docker.register(release, model, manifest)
                runtime = ReleaseRuntime(docker, hostname="test-host")
                runtime.deploy(profile, SHA_A)
                docker.unhealthy_for.add(SHA_B)
                docker.events.clear()
                with self.assertRaises(ReleaseError) as caught:
                    runtime.deploy(profile, SHA_B)
                self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
                self.assertEqual([e[1] for e in docker.mutations if e[0] == "up"], [SHA_B])
                state = StateStore(root / "state", "newemaint-test").load()
                self.assertEqual(state["last_result"], "deployment-rollback-blocked")
                self.assertEqual(state["database_revision"]["generation"], 2)

    def test_failed_explicit_rollback_requires_separate_reverse_proof_before_restoration(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        install_rollback_evidence(self.root, SHA_B, SHA_A)
        self.docker.unhealthy_for.add(SHA_A)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual([e[1] for e in self.docker.mutations if e[0] == "up"], [SHA_A])
        self.assertEqual(self.store.load()["last_result"], "rollback-restore-blocked")

    def test_explicit_rollback_with_no_evidence_has_zero_old_mutations(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def use_shared_migration(self) -> None:
        shutil.rmtree(self.root / "releases" / SHA_B)
        _, model, manifest = create_release(self.root, SHA_B, shares_migration_with=SHA_A)
        self.docker.register(SHA_B, model, manifest)

    def test_same_known_identity_keeps_305_receipt_and_allows_rollback_without_evidence(self) -> None:
        self.use_shared_migration()
        self.runtime.deploy(self.profile, SHA_A)
        receipt = self.store.load()["migrations"]
        self.runtime.deploy(self.profile, SHA_B)
        self.assertEqual(self.store.load()["migrations"], receipt)
        self.docker.events.clear()
        self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual([e[0] for e in self.docker.mutations], ["up"])
        self.assertEqual(self.store.load()["database_revision"]["generation"], 1)

    def test_same_identity_rollback_failure_can_restore_current_but_still_reports_failure(self) -> None:
        self.use_shared_migration()
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        self.docker.unhealthy_for.add(SHA_A)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_FAILED")
        self.assertEqual([e[1] for e in self.docker.mutations if e[0] == "up"], [SHA_A, SHA_B])
        self.assertEqual(self.store.load()["last_result"], "rollback-current-restored")
        self.assertTrue(self.runtime.status(self.profile, SHA_B)["ok"])

    def test_untracked_completed_ledger_requires_observed_evidence_without_becoming_known(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        legacy = self.store.load()
        del legacy["database_revision"]
        legacy["contract_version"] = "docker-release-state/v2"
        write_json(self.store.path, legacy, mode=0o600)
        with self.assertRaises(ReleaseError):
            self.runtime.rollback(self.profile, SHA_A)
        install_rollback_evidence(self.root, SHA_B, SHA_A, database_identity=migration_identity(SHA_B))
        self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(self.store.load()["database_revision"], {"status": "untracked", "migration_identity": None, "generation": 0})

    def test_ledger_change_invalidates_existing_evidence_without_new_migration(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        install_rollback_evidence(self.root, SHA_B, SHA_A)
        state = self.store.load()
        state["migrations"][migration_identity(SHA_A)]["release_id"] = "c" * 40
        self.store.save(state)
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def test_manifest_bytes_change_invalidates_operator_proof(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        install_rollback_evidence(self.root, SHA_B, SHA_A)
        path = self.root / "releases" / SHA_A / "release.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def test_profile_change_during_candidate_up_blocks_fallback_to_new_namespace(self) -> None:
        self.use_shared_migration()
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.stage(self.profile, SHA_B)
        self.runtime.migrate(self.profile, SHA_B)
        self.docker.unhealthy_for.add(SHA_B)
        original_up = self.docker.compose_up
        def change_profile(*args: object) -> None:
            original_up(*args)
            value = json.loads(self.profile.read_text())
            value["compose_project"] = "other-project"
            write_json(self.profile, value, mode=0o600)
        self.docker.events.clear()
        with patch.object(self.docker, "compose_up", side_effect=change_profile):
            with self.assertRaises(ReleaseError) as caught:
                self.runtime.activate(self.profile, SHA_B)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual([e[1] for e in self.docker.mutations if e[0] == "up"], [SHA_B])

    def test_evidence_replaced_during_read_is_rejected(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        evidence = install_rollback_evidence(self.root, SHA_B, SHA_A)
        replacement = evidence.with_name("replacement.json")
        replacement.write_bytes(evidence.read_bytes())
        replacement.chmod(0o600)
        real_read = os.read
        def replace_on_read(fd: int, size: int) -> bytes:
            result = real_read(fd, size)
            if replacement.exists():
                os.replace(replacement, evidence)
            return result
        self.docker.events.clear()
        with patch("aisoft_release.rollback_compatibility.os.read", side_effect=replace_on_read):
            with self.assertRaises(ReleaseError) as caught:
                self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def test_profile_rejects_evidence_overlapping_release_state_or_env_paths(self) -> None:
        original = json.loads(self.profile.read_text())
        for path in (self.root / "releases" / "proof.json", self.root / "state" / "proof.json",
                     self.root / "target.env", self.root):
            with self.subTest(path=path):
                value = {**original, "rollback_compatibility_file": str(path)}
                write_json(self.profile, value, mode=0o600)
                with self.assertRaises(ReleaseError):
                    load_target_profile(self.profile)

    def test_evidence_from_other_owner_is_rejected_before_old_start(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        evidence_inode = install_rollback_evidence(self.root, SHA_B, SHA_A).stat().st_ino
        real_fstat = os.fstat
        def other_owner(fd: int) -> os.stat_result:
            info = real_fstat(fd)
            if stat.S_ISREG(info.st_mode) and info.st_ino == evidence_inode:
                fields = list(info)
                fields[4] = os.geteuid() + 10000
                return os.stat_result(fields)
            return info
        self.docker.events.clear()
        with patch("aisoft_release.rollback_compatibility.os.fstat", side_effect=other_owner):
            with self.assertRaises(ReleaseError) as caught:
                self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def test_evidence_expiry_is_exclusive_and_verified_time_inclusive(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        path = install_rollback_evidence(self.root, SHA_B, SHA_A)
        envelope = json.loads(path.read_text())
        envelope["records"][0].update(verified_at="2026-10-02T00:00:00Z", expires_at="2026-10-03T00:00:00Z")
        write_json(path, envelope, mode=0o600)
        expired = ReleaseRuntime(self.docker, hostname="test-host", now=datetime(2026, 10, 3, tzinfo=timezone.utc))
        self.docker.events.clear()
        with self.assertRaises(ReleaseError) as caught:
            expired.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])
        verified = ReleaseRuntime(self.docker, hostname="test-host", now=datetime(2026, 10, 2, tzinfo=timezone.utc))
        self.assertEqual(verified.rollback(self.profile, SHA_A)["action"], "rolled-back")

    def test_replaced_profile_owner_cannot_reauthorize_other_operator_evidence(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        evidence = install_rollback_evidence(self.root, SHA_B, SHA_A)
        evidence_inode = evidence.stat().st_ino
        parent_inode = evidence.parent.stat().st_ino
        foreign_uid = os.geteuid() + 10000
        original_stat, original_fstat = Path.stat, os.fstat
        original_config = self.docker.compose_config
        changed = []
        def foreign(info: os.stat_result) -> os.stat_result:
            fields = list(info)
            fields[4] = foreign_uid
            return os.stat_result(fields)
        def profile_stat(path: Path, *args: object, **kwargs: object) -> os.stat_result:
            info = original_stat(path, *args, **kwargs)
            return foreign(info) if changed and path == self.profile else info
        def evidence_fstat(fd: int) -> os.stat_result:
            info = original_fstat(fd)
            return foreign(info) if info.st_ino in {evidence_inode, parent_inode} else info
        def config_then_replace(*args: object) -> object:
            result = original_config(*args)
            if args[0].parent.name == SHA_B:
                content = self.profile.read_bytes()
                self.profile.unlink()
                self.profile.write_bytes(content)
                self.profile.chmod(0o600)
                changed.append(True)
            return result
        self.docker.events.clear()
        # Model a pathname replacement owned by another OS principal without requiring chown/root.
        with patch.object(self.docker, "compose_config", side_effect=config_then_replace), \
             patch.object(Path, "stat", profile_stat), \
             patch("aisoft_release.rollback_compatibility.os.fstat", side_effect=evidence_fstat):
            with self.assertRaises(ReleaseError) as caught:
                self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "ROLLBACK_BLOCKED")
        self.assertEqual(self.docker.mutations, [])

    def test_profile_replaced_between_protection_check_and_open_is_rechecked_on_fd(self) -> None:
        content = self.profile.read_bytes()
        original_open = os.open
        replaced = []
        def replace_then_open(path: object, *args: object, **kwargs: object) -> int:
            if path == self.profile and not replaced:
                self.profile.unlink()
                self.profile.write_bytes(content)
                self.profile.chmod(0o644)
                replaced.append(True)
            return original_open(path, *args, **kwargs)
        with patch("aisoft_release.contract.os.open", side_effect=replace_then_open):
            with self.assertRaises(ReleaseError) as caught:
                self.runtime.verify_target(self.profile, SHA_A)
        self.assertEqual(caught.exception.code, "INVALID_CONTRACT")
        self.assertEqual(self.docker.events, [])
