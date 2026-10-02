"""Stable CLI for validate, lock and explain."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ArchitectureError, Diagnostic
from .jsonio import canonical_bytes, load_json, write_canonical
from .lockfile import build_lock, lock_schema_filename, validate_lock
from .schema import validate_schema


def _paths(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    catalog = load_json(args.catalog)
    schema_dir = Path(args.schema_dir)
    profile_path = Path(args.profiles_dir) / f"{load_json(args.project)['profile_id']}.json"
    project = load_json(args.project)
    return (
        catalog,
        load_json(schema_dir / "catalog-v1.schema.json"),
        load_json(profile_path),
        load_json(schema_dir / "profile-v1.schema.json"),
        project,
        load_json(schema_dir / "project-architecture-v1.schema.json"),
    )


def _today(value: str | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ArchitectureError(Diagnostic("DATE_INVALID", "--today 必须为 YYYY-MM-DD。", "--today")) from None


def _build(args: argparse.Namespace, *, schema_version: str = "2.0") -> dict[str, Any]:
    catalog, catalog_schema, profile, profile_schema, project, project_schema = _paths(args)
    repo_root = args.repo_root
    if repo_root is None:
        project_path = Path(args.project).absolute()
        if project_path.parent.name == ".aisoft":
            repo_root = project_path.parent.parent
    return build_lock(
        catalog, catalog_schema, profile, profile_schema, project, project_schema,
        _today(args.today), schema_version=schema_version, repo_root=repo_root,
    )


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    if args.lock:
        lock = load_json(args.lock)
        if not isinstance(lock, dict):
            raise ArchitectureError(Diagnostic("SCHEMA_TYPE", "lock 必须为 JSON object。", "$"))
        schema_version = lock.get("schema_version")
        lock_schema = load_json(Path(args.schema_dir) / lock_schema_filename(schema_version))
        # Fail on a mixed/unknown marker before selecting or rebuilding inputs.
        validate_schema(lock, lock_schema)
        expected = _build(args, schema_version=schema_version)
        validate_lock(lock, lock_schema, expected)
    else:
        expected = _build(args)
    return {
        "valid": True,
        "project_id": expected["project_id"],
        "profile_id": expected["profile_id"],
        "catalog_revision": expected["catalog_revision"],
        "lock_sha256": expected["lock_sha256"],
    }


def command_lock(args: argparse.Namespace) -> dict[str, Any]:
    lock = _build(args)
    write_canonical(args.output, lock)
    return {"written": str(args.output), "lock_sha256": lock["lock_sha256"]}


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
