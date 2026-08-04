from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from aisoft_release.errors import ReleaseError, TransportError
from aisoft_release.runner import ReleaseRuntime

from tests.release_test_support import (
    FakeDocker,
    SHA_A,
    WEB_IMAGE_ID,
    create_archive,
    create_release,
    sha256,
    update_manifest,
    write_json,
)


class ReleaseTransportTests(unittest.TestCase):
    def test_registry_verify_is_read_only_and_deploy_pulls_by_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root, migration=False)
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            runtime = ReleaseRuntime(docker, hostname="test-host")
            result = runtime.verify(profile, SHA_A)
            self.assertTrue(result["ok"])
            self.assertEqual(docker.mutations, [])
            runtime.deploy(profile, SHA_A)
            pulls = [event for event in docker.events if event[0] == "pull"]
            self.assertEqual(len(pulls), 1)
            self.assertIn("@sha256:", str(pulls[0][1]))
            self.assertTrue(any(event[0] == "up" for event in docker.events))

    def test_offline_tamper_fails_before_any_docker_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            archive = root / "releases" / SHA_A / "images.tar"
            with archive.open("ab") as handle:
                handle.write(b"tamper")
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            runtime = ReleaseRuntime(docker, hostname="test-host")
            with self.assertRaises(TransportError):
                runtime.verify(profile, SHA_A)
            self.assertEqual(docker.events, [])

    def test_offline_inventory_tamper_fails_before_any_docker_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            inventory = root / "releases" / SHA_A / "images.inventory.json"
            value = json.loads(inventory.read_text())
            value["images"][0]["image_id"] = "sha256:" + "9" * 64
            write_json(inventory, value)
            release_dir = root / "releases" / SHA_A
            update_manifest(
                release_dir,
                lambda item: item["offline_bundle"].update(
                    {"inventory_sha256": sha256(inventory)}
                ),
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").verify(profile, SHA_A)
            self.assertEqual(docker.events, [])

    def test_offline_archive_path_traversal_fails_before_any_docker_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            release_dir = root / "releases" / SHA_A
            archive = release_dir / "images.tar"
            create_archive(archive, unsafe_name="../manifest.json")
            inventory = release_dir / "images.inventory.json"
            inventory_value = json.loads(inventory.read_text())
            inventory_value["archive_sha256"] = sha256(archive)
            write_json(inventory, inventory_value)
            update_manifest(
                release_dir,
                lambda item: item["offline_bundle"].update(
                    {
                        "archive_sha256": sha256(archive),
                        "inventory_sha256": sha256(inventory),
                    }
                ),
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").verify(profile, SHA_A)
            self.assertEqual(docker.events, [])

    def test_valid_offline_deploy_loads_once_and_never_pulls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
            self.assertEqual(len([event for event in docker.events if event[0] == "load"]), 1)
            self.assertFalse(any(event[0] == "pull" for event in docker.events))

    def test_image_identity_mismatch_stops_before_compose_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root, migration=False)
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            reference = str(manifest["images"][0]["reference"])
            docker.images[reference] = {
                **docker.images[reference],
                "Id": "sha256:" + "9" * 64,
            }
            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
            self.assertFalse(any(event[0] == "up" for event in docker.events))


if __name__ == "__main__":
    unittest.main()
