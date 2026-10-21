"""Stable CLI for validate, lock and explain."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ArchitectureError, Diagnostic
from .jsonio import canonical_bytes, load_json, write_canonical
from .lockfile import build_lock, lock_schema_filename, validate_lock
from .schema import validate_schema
from .validator import REVISION_RE, catalog_review_overdue, revision_key


PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]+$")


@dataclass(frozen=True)
class Inputs:
    catalog: dict[str, Any]
    catalog_schema: dict[str, Any]
    profile: dict[str, Any]
    profile_schema: dict[str, Any]
    project: dict[str, Any]
    project_schema: dict[str, Any]
    profile_source: str
    # Set when the declaration pins a published revision older than --catalog.
    catalog_behind: dict[str, str] | None


def _select_catalog(args: argparse.Namespace, project: dict[str, Any]) -> tuple[dict[str, Any], Path, dict[str, str] | None]:
    """Pick the catalog the declaration pins (#409).

    The current catalog is used when the revisions match or no release
    directory was given, so PROJECT_CATALOG_MISMATCH keeps its meaning. An older
    revision resolves only to a published snapshot under --catalog-releases;
    the revision is checked before it becomes a path component.
    """
    current = load_json(args.catalog)
    revision = project.get("catalog_revision") if isinstance(project, dict) else None
    if args.catalog_releases is None or not isinstance(current, dict) or revision == current.get("revision"):
        return current, Path(args.profiles_dir), None
    current_revision = current.get("revision")
    if (
        not isinstance(revision, str)
        or not REVISION_RE.fullmatch(revision)
        or not isinstance(current_revision, str)
        or not REVISION_RE.fullmatch(current_revision)
        or revision_key(revision) >= revision_key(current_revision)
    ):
        raise ArchitectureError(Diagnostic(
            "CATALOG_REVISION_UNKNOWN", "catalog_revision 不是已发布的历史 revision。", "$.catalog_revision",
            "改用平台当前 catalog revision，或 pin 一个随发布包分发的历史 revision。",
        ))
    release = Path(args.catalog_releases) / revision
    if not (release / "catalog.json").is_file():
        raise ArchitectureError(Diagnostic(
            "CATALOG_REVISION_UNKNOWN", "catalog_revision 不是已发布的历史 revision。", "$.catalog_revision",
            "改用平台当前 catalog revision，或 pin 一个随发布包分发的历史 revision。",
        ))
    return load_json(release / "catalog.json"), release / "profiles", {"pinned": revision, "current": current_revision}


def _select_profile(args: argparse.Namespace, project: dict[str, Any], platform_profiles: Path) -> tuple[Path, str]:
    """A project-owned profile wins over the platform's examples (ADR 0001 D5)."""
    profile_id = project.get("profile_id") if isinstance(project, dict) else None
    if not isinstance(profile_id, str) or not PROFILE_ID_RE.fullmatch(profile_id):
        raise ArchitectureError(Diagnostic("PROFILE_ID_INVALID", "profile_id 格式无效。", "$.profile_id"))
    candidates = []
    if args.project_profiles_dir is not None:
        candidates.append((Path(args.project_profiles_dir) / f"{profile_id}.json", "project"))
    candidates.append((platform_profiles / f"{profile_id}.json", "platform"))
    for path, source in candidates:
        if path.is_file():
            return path, source
    raise ArchitectureError(Diagnostic(
        "PROFILE_UNKNOWN", "找不到 declaration 引用的 profile。", "$.profile_id",
        "在项目 .aisoft/profiles/ 自带该 profile，或改用平台已发布的 profile。",
    ))


def _paths(args: argparse.Namespace) -> Inputs:
    schema_dir = Path(args.schema_dir)
    project = load_json(args.project)
    catalog, platform_profiles, behind = _select_catalog(args, project)
    profile_path, profile_source = _select_profile(args, project, platform_profiles)
    return Inputs(
        catalog=catalog,
        catalog_schema=load_json(schema_dir / "catalog-v1.schema.json"),
        profile=load_json(profile_path),
        profile_schema=load_json(schema_dir / "profile-v1.schema.json"),
        project=project,
        project_schema=load_json(schema_dir / "project-architecture-v1.schema.json"),
        profile_source=profile_source,
        catalog_behind=behind,
    )


def _today(value: str | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ArchitectureError(Diagnostic("DATE_INVALID", "--today 必须为 YYYY-MM-DD。", "--today")) from None


def _build(args: argparse.Namespace, *, schema_version: str = "2.0") -> tuple[dict[str, Any], Inputs]:
    inputs = _paths(args)
    repo_root = args.repo_root
    if repo_root is None:
        project_path = Path(args.project).absolute()
        if project_path.parent.name == ".aisoft":
            repo_root = project_path.parent.parent
    lock = build_lock(
        inputs.catalog, inputs.catalog_schema, inputs.profile, inputs.profile_schema,
        inputs.project, inputs.project_schema,
        _today(args.today), schema_version=schema_version, repo_root=repo_root,
        pinned_catalog=inputs.catalog_behind is not None,
    )
    return lock, inputs


def _pin_report(inputs: Inputs, today: date) -> dict[str, Any]:
    """Extra result keys; absent when the declaration uses the current catalog."""
    report: dict[str, Any] = {"profile_source": inputs.profile_source}
    if inputs.catalog_behind is not None:
        report["catalog_behind"] = inputs.catalog_behind
        report["catalog_review_overdue"] = catalog_review_overdue(inputs.catalog, today)
    return report


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    if args.lock:
        lock = load_json(args.lock)
        if not isinstance(lock, dict):
            raise ArchitectureError(Diagnostic("SCHEMA_TYPE", "lock 必须为 JSON object。", "$"))
        schema_version = lock.get("schema_version")
        lock_schema = load_json(Path(args.schema_dir) / lock_schema_filename(schema_version))
        # Fail on a mixed/unknown marker before selecting or rebuilding inputs.
        validate_schema(lock, lock_schema)
        expected, inputs = _build(args, schema_version=schema_version)
        validate_lock(lock, lock_schema, expected)
    else:
        expected, inputs = _build(args)
    return {
        "valid": True,
        "project_id": expected["project_id"],
        "profile_id": expected["profile_id"],
        "catalog_revision": expected["catalog_revision"],
        "lock_sha256": expected["lock_sha256"],
        **_pin_report(inputs, _today(args.today)),
    }


def command_lock(args: argparse.Namespace) -> dict[str, Any]:
    lock, inputs = _build(args)
    write_canonical(args.output, lock)
    return {"written": str(args.output), "lock_sha256": lock["lock_sha256"], **_pin_report(inputs, _today(args.today))}


def command_explain(args: argparse.Namespace) -> dict[str, Any]:
    catalog = load_json(args.catalog)
    for component in catalog["components"]:
        if component["id"] == args.component:
            return {
                "component_id": component["id"],
                "version": component["version"],
                "state": component["state"],
                "source_url": component["provenance"]["source_url"],
                "support_end": component["lifecycle"]["support_end"],
                "eol": component["lifecycle"]["eol"],
                "compatibility": component["compatibility"],
                "remediation": component["remediation"],
            }
    raise ArchitectureError(Diagnostic("COMPONENT_UNKNOWN", "Catalog 中不存在该 component。", "--component"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisoft-architecture")
    subparsers = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--catalog", required=True)
    common.add_argument("--profiles-dir", required=True)
    common.add_argument("--project-profiles-dir")
    common.add_argument("--catalog-releases")
    common.add_argument("--schema-dir", required=True)
    common.add_argument("--project", required=True)
    common.add_argument("--repo-root")
    common.add_argument("--today")
    validate = subparsers.add_parser("validate", parents=[common])
    validate.add_argument("--lock")
    validate.set_defaults(handler=command_validate)
    lock = subparsers.add_parser("lock", parents=[common])
    lock.add_argument("--output", required=True)
    lock.set_defaults(handler=command_lock)
    explain = subparsers.add_parser("explain")
    explain.add_argument("--catalog", required=True)
    explain.add_argument("--component", required=True)
    explain.set_defaults(handler=command_explain)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = args.handler(args)
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except ArchitectureError as exc:
        output = {"valid": False, "diagnostics": [exc.diagnostic.as_dict()]}
        sys.stderr.buffer.write(canonical_bytes(output))
        return 2
    except (KeyError, TypeError, ValueError) as exc:
        diagnostic = Diagnostic("CONTRACT_INVALID", "架构文件结构无效；未输出输入值。", "$")
        sys.stderr.buffer.write(canonical_bytes({"valid": False, "diagnostics": [diagnostic.as_dict()]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
