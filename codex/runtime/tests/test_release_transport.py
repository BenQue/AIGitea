from __future__ import annotations

from copy import deepcopy
import io
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch

from aisoft_release import transport as transport_module
from aisoft_release.contract import (
    ImageSpec,
    load_release_artifact,
    load_release_files,
    load_target_profile,
)
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


def archive_config_ids(release_dir: Path) -> dict[str, str]:
    with tarfile.open(release_dir / "images.tar") as archive:
        entries = json.load(archive.extractfile("manifest.json"))
    manifest = json.loads((release_dir / "release.json").read_text())
    by_tag = {entry["RepoTags"][0]: "sha256:" + Path(entry["Config"]).name for entry in entries}
    return {image["service"]: by_tag[image["runtime_reference"]] for image in manifest["images"]}


class CrossStoreDocker(FakeDocker):
    """Model the measured classic daemon config ID, not producer native ID."""

    def register_cross_store(self, release_id, model, manifest, release_dir):
        self.register(release_id, model, manifest)
        ids = archive_config_ids(release_dir)
        for image in manifest["images"]:
            self.images[image["reference"]]["Id"] = ids[image["service"]]

    def load_archive(self, archive_path):
        super().load_archive(archive_path)
        ids = archive_config_ids(archive_path.parent)
        for image in self.manifests[archive_path.parent.name]["images"]:
            self.images[image["runtime_reference"]]["Id"] = ids[image["service"]]


class ReleaseTransportTests(unittest.TestCase):
    def test_measured_docker28_identity_uses_unchanged_real_archive(self):
        evidence = Path(__file__).resolve().parents[3] / "docs/changes/296-docker28-classic/evidence"
        receipt = json.loads((evidence / "real-identity.json").read_text())
        archive = evidence / "identity-archive.tar"
        self.assertEqual(sha256(archive), receipt["offline_archive_sha256"])
        image = ImageSpec(
            service="identity", reference=receipt["reference"],
            digest=receipt["producer"]["Id"], image_id=receipt["producer"]["Id"],
            transport_reference=receipt["consumer_offline"]["RepoTags"][0],
            runtime_reference=receipt["consumer_offline"]["RepoTags"][0],
        )
        graph = transport_module._validate_archive_structure(archive, (image,))
        identities = dict(graph.image_identities)["identity"]
        self.assertEqual(identities, {receipt["producer"]["Id"], receipt["consumer_offline"]["Id"]})
        transport_module._verify_registry_image(receipt["producer"], image, identities)
        transport_module._verify_registry_image(receipt["consumer_registry"], image, identities)
        transport_module._verify_local_image(receipt["consumer_offline"], image, identities)
        # Unproven RootFS equality alone never authorizes another native ID.
        forged = {**receipt["consumer_offline"], "Id": "sha256:" + "f" * 64}
        with self.assertRaises(ReleaseError):
            transport_module._verify_local_image(forged, image, identities)

    def test_legacy_v1_never_projects_config_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root, contract_version="docker-release/v1")
            release_dir = root / "releases" / SHA_A
            manifest = replace_with_oci_archive(release_dir, manifest, image_store="containerd-direct")
            docker = CrossStoreDocker()
            docker.register_cross_store(SHA_A, model, manifest, release_dir)
            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").deploy(profile, SHA_A)
            self.assertFalse(any(event[0] in {"tag", "migration", "up"} for event in docker.mutations))

    def test_cross_store_native_and_config_ids_accept_same_oci_artifact(self):
        for store in ("containerd-direct", "containerd", "classic"):
            for transport in ("registry", "offline-bundle"):
                for cross_store in (False, True):
                    with self.subTest(store=store, transport=transport, cross_store=cross_store), tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        profile, model, manifest = create_release(root, transport=transport)
                        release_dir = root / "releases" / SHA_A
                        manifest = replace_with_oci_archive(release_dir, manifest, image_store=store)
                        docker = CrossStoreDocker() if cross_store else FakeDocker()
                        if cross_store:
                            docker.register_cross_store(SHA_A, model, manifest, release_dir)
                        else:
                            docker.register(SHA_A, model, manifest)
                        runtime = ReleaseRuntime(docker, hostname="test-host")
                        runtime.stage(profile, SHA_A)
                        state = json.loads((root / "state" / "state.json").read_text())
                        self.assertEqual(state["staged_releases"][SHA_A]["image_ids"], {i["service"]: i["image_id"] for i in manifest["images"]})
                        runtime.migrate(profile, SHA_A)
                        runtime.activate(profile, SHA_A)
                        self.assertTrue(runtime.status(profile, SHA_A)["ok"])

    def test_cross_store_rejects_wrong_local_content_platform_or_registry_digest(self):
        for field, replacement in (("Id", "sha256:" + "f" * 64), ("Architecture", "arm64"), ("Os", "windows"), ("RepoDigests", [])):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(root, migration=False)
                release_dir = root / "releases" / SHA_A
                manifest = replace_with_oci_archive(release_dir, manifest, image_store="containerd")
                docker = CrossStoreDocker()
                docker.register_cross_store(SHA_A, model, manifest, release_dir)
                docker.images[manifest["images"][0]["reference"]][field] = replacement
                with self.assertRaises(TransportError):
                    ReleaseRuntime(docker, hostname="test-host").stage(profile, SHA_A)
                self.assertFalse(any(event[0] == "tag" for event in docker.mutations))

    def test_verified_oci_config_must_itself_be_linux_amd64(self):
        from tests.release_test_support import canonical_bytes
        for store in ("containerd-direct", "containerd"):
            with self.subTest(store=store), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(root, migration=False)
                def wrong_platform(value):
                    if isinstance(value, dict) and "fixture_service" in value:
                        value = {**value, "architecture": "arm64"}
                    return canonical_bytes(value)
                with patch("tests.release_test_support.canonical_bytes", side_effect=wrong_platform):
                    manifest = replace_with_oci_archive(root / "releases" / SHA_A, manifest, image_store=store)
                docker = FakeDocker()
                docker.register(SHA_A, model, manifest)
                with self.assertRaises(ReleaseError):
                    ReleaseRuntime(docker, hostname="test-host").stage(profile, SHA_A)
                self.assertEqual(docker.mutations, [])

    def test_cross_store_rejects_attestation_config_even_if_content_verified(self):
        from tests.release_test_support import canonical_bytes
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root)
            release_dir = root / "releases" / SHA_A
            manifest = replace_with_oci_archive(release_dir, manifest, image_store="containerd")
            docker = CrossStoreDocker()
            docker.register_cross_store(SHA_A, model, manifest, release_dir)
            attestation_id = "sha256:" + hashlib.sha256(canonical_bytes({})).hexdigest()
            docker.images[manifest["images"][0]["reference"]]["Id"] = attestation_id
            with self.assertRaises(TransportError):
                ReleaseRuntime(docker, hostname="test-host").stage(profile, SHA_A)
            self.assertFalse(any(event[0] == "tag" for event in docker.mutations))

    def test_cross_store_rejects_ambiguous_or_wrong_platform_index_before_pull(self):
        from tests.release_test_support import canonical_bytes
        for corruption in ("duplicate-runnable", "wrong-platform", "top-platform"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(root)
                def wrong_index(value):
                    if (
                        corruption == "top-platform"
                        and isinstance(value, dict)
                        and "manifests" in value
                        and "annotations" in value["manifests"][0]
                    ):
                        value = deepcopy(value)
                        value["manifests"][0]["platform"] = {"architecture": "arm64", "os": "linux"}
                    elif isinstance(value, dict) and value.get("mediaType") == transport_module.OCI_INDEX_MEDIA_TYPE:
                        value = deepcopy(value)
                        if corruption == "duplicate-runnable":
                            value["manifests"].append(deepcopy(value["manifests"][0]))
                        elif corruption == "wrong-platform":
                            value["manifests"][0]["platform"]["architecture"] = "arm64"
                    return canonical_bytes(value)
                with patch("tests.release_test_support.canonical_bytes", side_effect=wrong_index):
                    manifest = replace_with_oci_archive(root / "releases" / SHA_A, manifest, image_store="containerd")
                docker = FakeDocker()
                docker.register(SHA_A, model, manifest)
                with self.assertRaises(ReleaseError):
                    ReleaseRuntime(docker, hostname="test-host").stage(profile, SHA_A)
                self.assertEqual(docker.mutations, [])

    def test_cross_store_receipt_cannot_hide_changed_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(root)
            release_dir = root / "releases" / SHA_A
            manifest = replace_with_oci_archive(release_dir, manifest, image_store="containerd-direct")
            docker = CrossStoreDocker()
            docker.register_cross_store(SHA_A, model, manifest, release_dir)
            runtime = ReleaseRuntime(docker, hostname="test-host")
            runtime.stage(profile, SHA_A)
            mutation_count = len(docker.mutations)
            with (release_dir / "images.tar").open("ab") as stream:
                stream.write(b"tampered")
            with self.assertRaises(ReleaseError):
                runtime.migrate(profile, SHA_A)
            self.assertEqual(len(docker.mutations), mutation_count)

    def test_verified_archive_graph_matches_preflight_members(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_release(root, transport="offline-bundle", migration=False)
            files = load_release_artifact(root / "releases", SHA_A)
            graph = transport_module.inspect_offline_artifact(files)
            self.assertEqual(
                {member.kind for member in graph.members},
                {"image-config", "layer", "metadata"},
            )
            self.assertEqual(
                {member.name for member in graph.members},
                {
                    "2" * 64 + ".json",
                    "layers/0/layer.tar",
                    "manifest.json",
                    "repositories",
                },
            )

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
