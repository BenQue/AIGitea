"""Catalog pinning by revision and project-owned profiles (#409, ADR 0001 D5)."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from aisoft_architecture.jsonio import canonical_bytes, sha256_value


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
CLI = ARCH / "bin/aisoft-architecture"
RELEASES = ARCH / "catalog-releases"
PROJECT_PROFILE = ARCH / "fixtures/project-profile"
# A published revision is immutable: its catalog hash is what every lock that
# pins it recorded as catalog_sha256. Changing a snapshot breaks those locks.
PUBLISHED = {
    "2026.08.3": "00df83232ea680f6d2bde6f89467f305b561b76e8df562bce7ba058597daefca",
}
# Byte digests of every file in each published snapshot, profiles included.
PUBLISHED_FILES = {
    "2026.08.3": {
        "catalog.json": "260c49c4028caf6004769916d12c49920f510b6ccdb0cb9fc48abf4915f173e3",
        "profiles/linux-node-postgres-v1.json": "304e13475666de6fa834f3fce2530ef22bc8a0bf2aef591662ed77fb74ceb46a",
        "profiles/linux-node-systemd-postgres-v1.json": "84ee27f2bf45c0307395d67cada56d51a9fcf914b8432e37f708a7a1b501f39e",
        "profiles/small-embedded-sqlite-v1.json": "574cff3d8a3b947c241279b6ec0422cd5abf99e08174e863b11c710e87b7a360",
        "profiles/windows-dotnet-postgres-v1.json": "517a9e5de01902c69d70f9f43c98be17d884a0f6488c0c4ccf5546260dbd79c0",
    },
}


class CatalogPinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment.update({"http_proxy": "http://127.0.0.1:1", "https_proxy": "http://127.0.0.1:1", "NO_PROXY": ""})
        return subprocess.run([str(CLI), *args], text=True, capture_output=True, check=False, env=environment)

    def common(self, project: Path, *, releases: Path | None = RELEASES, today: str = "2026-10-21",
               project_profiles: Path | None = None) -> list[str]:
        args = [
            "--catalog", str(ARCH / "catalog.json"),
            "--profiles-dir", str(ARCH / "profiles"),
            "--schema-dir", str(ARCH / "schemas"),
            "--project", str(project),
            "--repo-root", str(ARCH),
            "--today", today,
        ]
        if releases is not None:
            args += ["--catalog-releases", str(releases)]
        if project_profiles is not None:
            args += ["--project-profiles-dir", str(project_profiles)]
        return args

    def pinned_project(self, revision: str = "2026.08.3") -> Path:
        project = json.loads((ARCH / "fixtures/valid/windows-project.json").read_text())
        project["catalog_revision"] = revision
        path = self.tmp / "pinned.json"
        path.write_text(json.dumps(project))
        return path

    def code(self, result: subprocess.CompletedProcess[str]) -> str:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        return json.loads(result.stderr)["diagnostics"][0]["code"]

    def test_published_snapshots_are_unchanged(self) -> None:
        self.assertEqual(sorted(path.name for path in RELEASES.iterdir()), sorted(PUBLISHED))
        for revision, digest in PUBLISHED.items():
            with self.subTest(revision=revision):
                catalog = json.loads((RELEASES / revision / "catalog.json").read_text())
                self.assertEqual(catalog["revision"], revision)
                self.assertEqual(sha256_value(catalog), digest)
                for profile in (RELEASES / revision / "profiles").iterdir():
                    self.assertEqual(json.loads(profile.read_text())["catalog_revision"], revision)
                root = RELEASES / revision
                files = {
                    path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in root.rglob("*") if path.is_file()
                }
                self.assertEqual(files, PUBLISHED_FILES[revision])

    def test_an_older_pinned_revision_validates_and_locks_against_its_snapshot(self) -> None:
        project = self.pinned_project()
        lock = self.tmp / "lock.json"
        result = self.run_cli(["lock", *self.common(project), "--output", str(lock)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(lock.read_text())["source_checksums"]["catalog_sha256"], PUBLISHED["2026.08.3"])
        result = self.run_cli(["validate", *self.common(project), "--lock", str(lock)])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["catalog_behind"], {"pinned": "2026.08.3", "current": "2026.09.0"})
        self.assertFalse(payload["catalog_review_overdue"])
        self.assertEqual(payload["profile_source"], "platform")

    def test_without_the_release_directory_the_old_mismatch_stands(self) -> None:
        result = self.run_cli(["validate", *self.common(self.pinned_project(), releases=None)])
        self.assertEqual(self.code(result), "PROJECT_CATALOG_MISMATCH")

    def test_unknown_newer_or_malformed_revisions_are_refused(self) -> None:
        for revision in ("2026.08.2", "2027.01.0", "../2026.08.3", "2026.8.3x"):
            with self.subTest(revision=revision):
                result = self.run_cli(["validate", *self.common(self.pinned_project(revision))])
                self.assertEqual(self.code(result), "CATALOG_REVISION_UNKNOWN")
                self.assertNotIn(revision, result.stderr)

    def test_a_pinned_snapshot_ages_into_a_report_not_a_failure(self) -> None:
        result = self.run_cli(["validate", *self.common(self.pinned_project(), today="2027-01-01")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["catalog_review_overdue"])

    def test_the_current_catalog_still_fails_when_overdue(self) -> None:
        result = self.run_cli(["validate", *self.common(ARCH / "fixtures/valid/windows-project.json", today="2027-01-01")])
        self.assertEqual(self.code(result), "CATALOG_REVIEW_OVERDUE")

    def copy_releases(self) -> Path:
        releases = self.tmp / "releases"
        shutil.copytree(RELEASES, releases)
        return releases

    def test_eol_in_a_pinned_snapshot_still_fails_closed(self) -> None:
        releases = self.copy_releases()
        path = releases / "2026.08.3/catalog.json"
        catalog = json.loads(path.read_text())
        for component in catalog["components"]:
            if component["id"] == "runtime.dotnet.10":
                component["lifecycle"].update({"support_end": None, "eol": "2026-10-01", "migrate_by": None})
        path.write_bytes(canonical_bytes(catalog))
        result = self.run_cli(["validate", *self.common(self.pinned_project(), releases=releases)])
        self.assertEqual(self.code(result), "COMPONENT_EOL")

    def test_editing_a_snapshot_drifts_every_lock_that_pins_it(self) -> None:
        project = self.pinned_project()
        lock = self.tmp / "lock.json"
        self.assertEqual(self.run_cli(["lock", *self.common(project), "--output", str(lock)]).returncode, 0)
        releases = self.copy_releases()
        path = releases / "2026.08.3/catalog.json"
        catalog = json.loads(path.read_text())
        catalog["components"][0]["remediation"] += " Edited."
        path.write_bytes(canonical_bytes(catalog))
        result = self.run_cli(["validate", *self.common(project, releases=releases), "--lock", str(lock)])
        self.assertEqual(self.code(result), "LOCK_DRIFT")


class ProjectProfileTests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(CLI), *args], text=True, capture_output=True, check=False)

    def common(self, project: Path, profiles: Path | None) -> list[str]:
        args = [
            "--catalog", str(ARCH / "catalog.json"),
            "--profiles-dir", str(ARCH / "profiles"),
            "--schema-dir", str(ARCH / "schemas"),
            "--project", str(project),
            "--today", "2026-10-21",
        ]
        if profiles is not None:
            args += ["--project-profiles-dir", str(profiles)]
        return args

    def test_a_project_owned_profile_validates_and_locks(self) -> None:
        project = PROJECT_PROFILE / "architecture.json"
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "lock.json"
            result = self.run_cli(["lock", *self.common(project, PROJECT_PROFILE / "profiles"), "--output", str(lock)])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["profile_source"], "project")
            result = self.run_cli(["validate", *self.common(project, PROJECT_PROFILE / "profiles"), "--lock", str(lock)])
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_without_the_project_directory_the_profile_is_unknown(self) -> None:
        result = self.run_cli(["validate", *self.common(PROJECT_PROFILE / "architecture.json", None)])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "PROFILE_UNKNOWN")

    def test_a_project_profile_shadows_the_platform_example_of_the_same_id(self) -> None:
        project = ARCH / "fixtures/valid/windows-project.json"
        with tempfile.TemporaryDirectory() as directory:
            profiles = Path(directory)
            profile = json.loads((ARCH / "profiles/windows-dotnet-postgres-v1.json").read_text())
            profile["description"] = "Project-owned copy."
            profile["constraints"]["backup"] = "Project-owned backup rule."
            (profiles / "windows-dotnet-postgres-v1.json").write_text(json.dumps(profile))
            lock = profiles / "lock.json"
            result = self.run_cli(["lock", *self.common(project, profiles), "--output", str(lock)])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["profile_source"], "project")
            # The platform example is a different machine profile, so the lock
            # proves which one was used.
            result = self.run_cli(["validate", *self.common(project, None), "--lock", str(lock)])
            self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "LOCK_DRIFT")

    def test_a_project_profile_must_name_preferred_catalog_components(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            profiles = Path(directory)
            profile = json.loads((PROJECT_PROFILE / "profiles/example-node-react-postgres-pm2-v1.json").read_text())
            profile["required_components"][1]["component_id"] = "runtime.node.22"
            del profile["required_components"][1]["transitions"]
            (profiles / f"{profile['profile_id']}.json").write_text(json.dumps(profile))
            result = self.run_cli(["validate", *self.common(PROJECT_PROFILE / "architecture.json", profiles)])
            self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "PROFILE_COMPONENT_STATE")

    def test_a_profile_id_is_checked_before_it_becomes_a_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = json.loads((PROJECT_PROFILE / "architecture.json").read_text())
            project["profile_id"] = "../profiles/windows-dotnet-postgres-v1"
            path = Path(directory) / "architecture.json"
            path.write_text(json.dumps(project))
            result = self.run_cli(["validate", *self.common(path, PROJECT_PROFILE / "profiles")])
            self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "PROFILE_ID_INVALID")


if __name__ == "__main__":
    unittest.main()
