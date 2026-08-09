from __future__ import annotations

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import tempfile
import tarfile
import unittest

from aisoft_release.contract import load_release_files, load_target_profile
from aisoft_release.errors import DeploymentError, ReleaseError, TransportError
from aisoft_release.runner import ReleaseRuntime
from aisoft_release.transport import produce_offline_archive

from tests.release_test_support import (
    FakeDocker,
    SHA_A,
    WEB_IMAGE_ID,
    create_archive,
    create_oci_archive,
    create_release,
    sha256,
    update_manifest,
    write_json,
)


def replace_with_oci_archive(
    release_dir: Path,
    manifest: dict[str, object],
    *,
    image_store: str,
    ref_name_form: str = "tag",
    tamper: str | None = None,
) -> dict[str, object]:
    archive = release_dir / "images.tar"
    images = deepcopy(manifest["images"])
    create_oci_archive(
        archive,
        images,
        image_store=image_store,
        ref_name_form=ref_name_form,
        tamper=tamper,
    )
    inventory = release_dir / "images.inventory.json"
    inventory_value = json.loads(inventory.read_text())
    inventory_value["archive_sha256"] = sha256(archive)
    inventory_value["images"] = deepcopy(images)
    for image in inventory_value["images"]:
        image["platform"] = "linux/amd64"
    write_json(inventory, inventory_value)
    return update_manifest(
        release_dir,
        lambda item: item.update(
            {
                "images": images,
                "offline_bundle": {
                    **item["offline_bundle"],
                    "archive_sha256": sha256(archive),
                    "inventory_sha256": sha256(inventory),
                },
            }
        ),
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
            tags = [event for event in docker.events if event[0] == "tag"]
            self.assertEqual(len(tags), 1)
            self.assertEqual(
                tags[0][2], "aisoft.local/admin/newemaint/web:" + SHA_A
            )
            self.assertTrue(any(event[0] == "up" for event in docker.events))

    def test_legacy_registry_deploy_remains_supported_without_retag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, migration=False, identity_version="legacy"
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
            self.assertEqual(len([event for event in docker.events if event[0] == "pull"]), 1)
            self.assertFalse(any(event[0] == "tag" for event in docker.events))

    def test_legacy_offline_bundle_rejects_before_any_docker_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root,
                transport="offline-bundle",
                migration=False,
                identity_version="legacy",
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            with self.assertRaisesRegex(
                TransportError, "must be republished.*before image load"
            ):
                ReleaseRuntime(docker, hostname="test-host").verify(profile, SHA_A)
            self.assertEqual(docker.events, [])

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
        variants = {
            "service": lambda image: image.update({"service": "other"}),
            "registry reference": lambda image: image.update(
                {
                    "reference": "registry.internal/admin/other@sha256:"
                    + "1" * 64
                }
            ),
            "registry digest": lambda image: image.update(
                {"digest": "sha256:" + "9" * 64}
            ),
            "transport tag": lambda image: image.update(
                {
                    "transport_reference": "aisoft.local/admin/newemaint/other:"
                    + SHA_A
                }
            ),
            "runtime tag": lambda image: image.update(
                {
                    "runtime_reference": "aisoft.local/admin/newemaint/other:"
                    + SHA_A
                }
            ),
            "image id": lambda image: image.update(
                {"image_id": "sha256:" + "9" * 64}
            ),
            "platform": lambda image: image.update({"platform": "linux/arm64"}),
            "unknown": lambda image: image.update({"extra": True}),
        }
        for name, transform in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(
                    root, transport="offline-bundle", migration=False
                )
                inventory = root / "releases" / SHA_A / "images.inventory.json"
                value = json.loads(inventory.read_text())
                transform(value["images"][0])
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
            create_archive(
                archive,
                list(manifest["images"]),
                unsafe_name="../manifest.json",
            )
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
            runtime_reference = str(manifest["images"][0]["runtime_reference"])
            self.assertEqual(docker.images[runtime_reference]["RepoDigests"], [])

    def test_docker_29_oci_archive_shapes_pass_read_only_preflight(self) -> None:
        cases = (
            ("containerd", "tag"),
            ("containerd", "full"),
            ("classic", "tag"),
            ("classic", "full"),
        )
        for image_store, ref_name_form in cases:
            with (
                self.subTest(
                    image_store=image_store, ref_name_form=ref_name_form
                ),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                profile, model, manifest = create_release(
                    root, transport="offline-bundle", migration=False
                )
                release_dir = root / "releases" / SHA_A
                updated = replace_with_oci_archive(
                    release_dir,
                    manifest,
                    image_store=image_store,
                    ref_name_form=ref_name_form,
                )
                docker = FakeDocker()
                docker.register(SHA_A, model, updated)
                result = ReleaseRuntime(docker, hostname="test-host").verify(
                    profile, SHA_A
                )
                self.assertTrue(result["ok"])
                self.assertEqual(docker.mutations, [])

    def test_docker_29_containerd_direct_manifest_identity_passes_preflight(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            release_dir = root / "releases" / SHA_A
            updated = replace_with_oci_archive(
                release_dir,
                manifest,
                image_store="containerd-direct",
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, updated)

            result = ReleaseRuntime(docker, hostname="test-host").verify(
                profile, SHA_A
            )

            self.assertTrue(result["ok"])
            self.assertEqual(docker.mutations, [])

    def test_docker_29_containerd_direct_manifest_rejects_unrelated_image_id(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            release_dir = root / "releases" / SHA_A
            updated = replace_with_oci_archive(
                release_dir,
                manifest,
                image_store="containerd-direct",
                tamper="declared-image-id",
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, updated)

            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").verify(profile, SHA_A)

            self.assertEqual(docker.mutations, [])

    def test_docker_29_oci_archive_tamper_fails_before_load(self) -> None:
        cases = (
            ("containerd", "reference"),
            ("containerd", "top-content"),
            ("containerd", "attestation-reference"),
            ("containerd", "graph-config"),
            ("containerd", "extra-descriptor"),
            ("containerd", "layer-source-size"),
            ("containerd", "descriptor-size-bool"),
            ("containerd", "index-schema-version"),
            ("classic", "reference"),
            ("classic", "top-content"),
            ("classic", "graph-config"),
            ("classic", "classic-metadata-parent"),
            ("classic", "classic-metadata-content"),
            ("classic", "layer-source-size"),
        )
        for image_store, tamper in cases:
            with (
                self.subTest(image_store=image_store, tamper=tamper),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                profile, model, manifest = create_release(
                    root, transport="offline-bundle", migration=False
                )
                release_dir = root / "releases" / SHA_A
                updated = replace_with_oci_archive(
                    release_dir,
                    manifest,
                    image_store=image_store,
                    tamper=tamper,
                )
                docker = FakeDocker()
                docker.register(SHA_A, model, updated)
                with self.assertRaises(TransportError):
                    ReleaseRuntime(docker, hostname="test-host").verify(
                        profile, SHA_A
                    )
                self.assertEqual(docker.mutations, [])

    def test_archive_reference_and_config_tamper_fail_before_load(self) -> None:
        transforms = {
            "transport tag": lambda images: images[0].update(
                {
                    "transport_reference": "aisoft.local/admin/newemaint/other:"
                    + SHA_A
                }
            ),
            "image config": lambda images: images[0].update(
                {"image_id": "sha256:" + "9" * 64}
            ),
            "missing tag": lambda images: images[0].pop("transport_reference"),
        }
        for name, transform in transforms.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(
                    root, transport="offline-bundle", migration=False
                )
                release_dir = root / "releases" / SHA_A
                archive = release_dir / "images.tar"
                archive_images = deepcopy(manifest["images"])
                transform(archive_images)
                create_archive(archive, archive_images)
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
                self.assertEqual(docker.mutations, [])

    def test_non_allowlisted_archive_member_fails_before_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            release_dir = root / "releases" / SHA_A
            archive = release_dir / "images.tar"
            with tarfile.open(archive, mode="a") as payload:
                unexpected = b"not part of the image archive contract\n"
                member = tarfile.TarInfo("unexpected.txt")
                member.size = len(unexpected)
                member.mode = 0o644
                payload.addfile(member, io.BytesIO(unexpected))
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
            self.assertEqual(docker.mutations, [])

    def test_wrong_store_is_rejected_before_load_or_other_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, transport="offline-bundle", migration=False
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            docker.capability_error = DeploymentError("fake rejected image store")
            with self.assertRaisesRegex(DeploymentError, "rejected image store"):
                ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
            self.assertEqual(docker.mutations, [])

    def test_post_load_identity_or_tag_failure_stops_before_migration_and_up(self) -> None:
        for failure in ("image-id", "runtime-tag"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(
                    root, transport="offline-bundle"
                )
                docker = FakeDocker()
                docker.register(SHA_A, model, manifest)
                if failure == "image-id":
                    docker.wrong_loaded_image_for.add(SHA_A)
                else:
                    docker.omit_runtime_tag_on_load_for.add(SHA_A)
                with self.assertRaises(TransportError):
                    ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
                self.assertEqual(len([event for event in docker.events if event[0] == "load"]), 1)
                self.assertFalse(any(event[0] in {"migration", "up"} for event in docker.events))

    def test_registry_requires_repo_digest_before_runtime_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root, migration=False)
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            reference = str(manifest["images"][0]["reference"])
            docker.images[reference] = {**docker.images[reference], "RepoDigests": []}
            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
            self.assertFalse(any(event[0] in {"tag", "up"} for event in docker.events))

    def test_producer_pulls_tags_verifies_and_saves_only_v2_tags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root, migration=False)
            files = load_release_files(load_target_profile(profile), SHA_A)
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            output = root / "producer-images.tar"
            produce_offline_archive(docker, files.manifest, output)
            names = [event[0] for event in docker.events]
            self.assertLess(names.index("pull"), names.index("tag"))
            self.assertLess(names.index("tag"), names.index("save"))
            save = next(event for event in docker.events if event[0] == "save")
            self.assertEqual(
                save[1], ("aisoft.local/admin/newemaint/web:" + SHA_A,)
            )

    def test_producer_never_saves_unverified_or_legacy_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root, migration=False)
            files = load_release_files(load_target_profile(profile), SHA_A)
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            reference = str(manifest["images"][0]["reference"])
            docker.images[reference] = {
                **docker.images[reference],
                "Id": "sha256:" + "9" * 64,
            }
            with self.assertRaises(TransportError):
                produce_offline_archive(docker, files.manifest, root / "invalid.tar")
            self.assertFalse(any(event[0] in {"tag", "save"} for event in docker.events))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, migration=False, identity_version="legacy"
            )
            files = load_release_files(load_target_profile(profile), SHA_A)
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            with self.assertRaises(TransportError):
                produce_offline_archive(docker, files.manifest, root / "legacy.tar")
            self.assertFalse(any(event[0] == "save" for event in docker.events))

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
